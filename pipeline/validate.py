"""validate.py — Descarta cualquier escenario incoherente antes de publicarlo.

Verifica:
  1. Esquema completo (claves y tipos).
  2. Coherencia de la decisión con su fuente de verdad:
     - Torneo:   opcion_correcta_index == nash.correct_action(...)
     - Cash:     opcion_correcta_index == (equity >= pot_odds)
  3. Cartas válidas, sin duplicados y consistentes con la fase.
  4. Presencia de "es" y "en" en todos los campos narrativos.
  5. Rango sano de valores numéricos.
"""
from __future__ import annotations

import nash
import poker_math as pm

VALID_CARDS = {r + s for r in pm.RANKS for s in pm.SUITS}
DIFFS = {"Principiante", "Intermedio", "Avanzado"}
CAPAS = {"matematica_rapida", "psicologia_y_rangos", "control_y_conclusion"}


def check(s: dict) -> list[str]:
    if s.get("tipo") == "hand_full":
        return _check_hand(s)
    if s.get("tipo") == "outs":
        return _check_outs(s)

    errors: list[str] = []

    for key in ("id", "modo", "fase", "dificultad", "posicion_heroe",
                "posicion_villano", "stack_bb", "pozo_bb", "cartas_heroe",
                "board", "accion_previa", "opciones", "opcion_correcta_index",
                "math", "leak_tags", "desglose"):
        if key not in s:
            errors.append(f"falta clave '{key}'")
    if errors:
        return errors

    if s["modo"] not in ("Torneo", "Cash Game"):
        errors.append("modo desconocido")
    if s["dificultad"] not in DIFFS:
        errors.append("dificultad inválida")

    cards = s["cartas_heroe"]
    all_cards = cards + s["board"]
    if (len(cards) != 2 or len(set(all_cards)) != len(all_cards)
            or any(c not in VALID_CARDS for c in all_cards)):
        errors.append("cartas inválidas o duplicadas")

    m = s.get("math", {})
    if not (0 <= m.get("equity", -1) <= 1):
        errors.append("equity fuera de 0..1")
    if not (0 <= m.get("pot_odds", -1) <= 1):
        errors.append("pot_odds fuera de 0..1")

    if not errors:
        tipo = s.get("tipo")
        if s["modo"] == "Torneo":
            errors += _check_overcall(s) if tipo == "overcall" \
                else _check_torneo(s)
        else:
            errors += _check_cash(s)
            if tipo == "river_3way":
                errors += _check_multiway(s)

    # Bilingüe
    ap = s["accion_previa"]
    if not (isinstance(ap, dict) and ap.get("es") and ap.get("en")):
        errors.append("accion_previa sin es/en")
    d = s["desglose"]
    for loc in ("es", "en"):
        capas = d.get(loc, {})
        if set(capas) != CAPAS or not all(capas.values()):
            errors.append(f"desglose incompleto en '{loc}'")

    return errors


def _check_torneo(s: dict) -> list[str]:
    errors = []
    if s["fase"] != "Pre-Flop":
        errors.append("fase de Torneo debe ser Pre-Flop en el MVP")
    if s["posicion_heroe"] not in nash.TABLES:
        errors.append("posición del héroe desconocida")
        return errors
    if not (3 <= s["stack_bb"] <= 22):
        errors.append("stack fuera de rango")
    if not (1 <= s["pozo_bb"] <= 5):
        errors.append("pozo incoherente para pre-flop")
    if s["board"] != []:
        errors.append("board debe estar vacío en pre-flop")
    if s["opciones"] != ["Fold", "All-In"]:
        errors.append("opciones inválidas para Torneo")
        return errors
    hand = pm.hand_to_notation(s["cartas_heroe"])
    expected = nash.correct_action(s["posicion_heroe"], hand, s["stack_bb"])
    if s["opcion_correcta_index"] != expected:
        errors.append(
            f"respuesta incoherente con Nash ({s['opcion_correcta_index']}"
            f" != {expected} para {hand}@{s['stack_bb']}BB)")
    return errors


def _check_overcall(s: dict) -> list[str]:
    """Torneo, spot de overcall: el héroe (BB) paga o no un all-in rival.

    Fuente de verdad: el rango de jam se deriva de nash.jam_range y la
    decisión de pago = (equity >= pot_odds). Se revalida la coherencia del
    índice con los números ya calculados (mismo contrato que Cash)."""
    errors = []
    if s["fase"] != "Pre-Flop":
        errors.append("fase de overcall debe ser Pre-Flop")
    if s["board"] != []:
        errors.append("board debe estar vacío en pre-flop")
    if s["posicion_villano"] not in nash.TABLES:
        errors.append("posición del jammer desconocida")
    if not (3 <= s["stack_bb"] <= 22):
        errors.append("stack fuera de rango")
    if s["opciones"] != ["Fold", "Call"]:
        errors.append("opciones inválidas para overcall (solo Fold/Call)")
        return errors
    m = s["math"]
    expected = 1 if m["equity"] >= m["pot_odds"] else 0
    if s["opcion_correcta_index"] != expected:
        errors.append(
            f"decisión de overcall incoherente con equity vs pot_odds "
            f"({s['opcion_correcta_index']} != {expected})")
    return errors


def _check_multiway(s: dict) -> list[str]:
    """Cash a 3 bandas: además de _check_cash, exige exactamente 2 rivales."""
    errors = []
    op = s.get("oponentes")
    if not (isinstance(op, list) and len(op) == 2):
        errors.append("river_3way requiere exactamente 2 oponentes")
    return errors


def _check_cash(s: dict) -> list[str]:
    errors = []
    if s["fase"] != "River":
        errors.append("fase de Cash debe ser River en el MVP")
    if len(s["board"]) != 5:
        errors.append("el river requiere board de 5 cartas")
    if s["opciones"] != ["Fold", "Call"]:
        errors.append("opciones inválidas para Cash (solo Fold/Call)")
        return errors
    m = s["math"]
    for extra in ("mdf", "value_bluff_ratio"):
        if not (0 <= m.get(extra, -1) <= 1):
            errors.append(f"{extra} fuera de 0..1")
    expected = 1 if m["equity"] >= m["pot_odds"] else 0
    if s["opcion_correcta_index"] != expected:
        errors.append(
            f"decisión incoherente con equity vs pot_odds "
            f"({s['opcion_correcta_index']} != {expected})")
    return errors


def _check_hand(s: dict) -> list[str]:
    """Mano completa (flop→turn→river). Cada calle es una decisión Call/Fold
    cuya corrección se re-verifica con equity >= pot_odds, más consistencia de
    board por calle y presencia bilingüe del repaso paso a paso."""
    errors = []
    for key in ("id", "modo", "tipo", "dificultad", "posicion_heroe",
                "posicion_villano", "cartas_heroe", "board", "stack_bb",
                "pozo_bb", "opciones", "calles", "contexto", "resumen",
                "leak_tags"):
        if key not in s:
            errors.append(f"falta clave '{key}'")
    if errors:
        return errors

    if s["modo"] != "Mano Completa":
        errors.append("modo debe ser 'Mano Completa'")
    if s["dificultad"] not in DIFFS:
        errors.append("dificultad inválida")
    if s["opciones"] != ["Fold", "Call"]:
        errors.append("opciones inválidas (solo Fold/Call)")

    cards = s["cartas_heroe"]
    board = s["board"]
    all_cards = cards + board
    if (len(cards) != 2 or len(board) != 5
            or len(set(all_cards)) != len(all_cards)
            or any(c not in VALID_CARDS for c in all_cards)):
        errors.append("cartas inválidas o duplicadas")

    calles = s["calles"]
    if not isinstance(calles, list) or len(calles) != 3:
        errors.append("la mano requiere exactamente 3 calles")
        return errors
    for i, (nd, name) in enumerate(zip(calles, ("Flop", "Turn", "River"))):
        if nd.get("calle") != name:
            errors.append(f"calle {i} debe ser {name}")
        if nd.get("board") != board[:3 + i]:
            errors.append(f"board de {name} incoherente con el runout")
        m = nd.get("math", {})
        if not (0 <= m.get("equity", -1) <= 1):
            errors.append(f"equity fuera de 0..1 en {name}")
        if nd.get("villano_pasa"):
            # Nodo de check (solo river): correcto = Bet si EV(apostar) > EV(pasar).
            if nd.get("opciones") != ["Check", "Fold", "Bet"]:
                errors.append(f"opciones inválidas en {name} (check)")
            expected = 2 if m.get("ev_apostar", 0) > m.get("ev_pasar", 0) else 0
            if nd.get("opcion_correcta_index") != expected:
                errors.append(
                    f"decisión de check en {name} incoherente con EV "
                    f"({nd.get('opcion_correcta_index')} != {expected})")
        else:
            if not (0 <= m.get("pot_odds", -1) <= 1):
                errors.append(f"pot_odds fuera de 0..1 en {name}")
            expected = 1 if m.get("equity", 0) >= m.get("pot_odds", 1) else 0
            if nd.get("opcion_correcta_index") != expected:
                errors.append(
                    f"decisión de {name} incoherente con equity vs pot_odds "
                    f"({nd.get('opcion_correcta_index')} != {expected})")
        ex = nd.get("explicacion", {})
        if not (isinstance(ex, dict) and ex.get("es") and ex.get("en")):
            errors.append(f"explicacion de {name} sin es/en")

    for campo in ("contexto", "resumen"):
        v = s.get(campo, {})
        if not (isinstance(v, dict) and v.get("es") and v.get("en")):
            errors.append(f"{campo} sin es/en")

    return errors


def _check_outs(s: dict) -> list[str]:
    """Ejercicio de outs: la opción correcta debe ser el porcentaje ofrecido más
    cercano a la probabilidad exacta almacenada; además board de 3-4 cartas y
    prosa bilingüe (accion_previa + explicacion)."""
    errors = []
    for key in ("id", "modo", "tipo", "dificultad", "cartas_heroe", "board",
                "opciones", "opcion_correcta_index", "math", "accion_previa",
                "explicacion", "leak_tags"):
        if key not in s:
            errors.append(f"falta clave '{key}'")
    if errors:
        return errors

    if s["modo"] != "Outs":
        errors.append("modo debe ser 'Outs'")
    if s["dificultad"] not in DIFFS:
        errors.append("dificultad inválida")

    cards = s["cartas_heroe"]
    board = s["board"]
    all_cards = cards + board
    if (len(cards) != 2 or len(board) not in (3, 4)
            or len(set(all_cards)) != len(all_cards)
            or any(c not in VALID_CARDS for c in all_cards)):
        errors.append("cartas inválidas o board no es flop/turn")

    m = s["math"]
    if not (0 <= m.get("prob", -1) <= 1):
        errors.append("prob fuera de 0..1")
    if not (1 <= m.get("outs", 0) <= 20):
        errors.append("outs fuera de rango")

    # La opción correcta = el % ofrecido más cercano a la prob exacta.
    try:
        pcts = [int(o.rstrip("%")) for o in s["opciones"]]
    except (ValueError, AttributeError):
        errors.append("opciones no son porcentajes válidos")
        return errors
    if len(pcts) < 2:
        errors.append("faltan opciones")
        return errors
    target = m["prob"] * 100
    expected = min(range(len(pcts)), key=lambda i: abs(pcts[i] - target))
    if s["opcion_correcta_index"] != expected:
        errors.append(
            f"opción correcta no es la más cercana a {target:.1f}% "
            f"({s['opcion_correcta_index']} != {expected})")

    ap = s["accion_previa"]
    if not (isinstance(ap, dict) and ap.get("es") and ap.get("en")):
        errors.append("accion_previa sin es/en")
    ex = s["explicacion"]
    if not (isinstance(ex, dict) and ex.get("es") and ex.get("en")):
        errors.append("explicacion sin es/en")
    return errors


def filter_valid(scenarios: list[dict]) -> tuple[list[dict], list[str]]:
    ok, log = [], []
    for s in scenarios:
        errs = check(s)
        if errs:
            log.append(f"{s.get('id','?')}: {'; '.join(errs)}")
        else:
            ok.append(s)
    return ok, log

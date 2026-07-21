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
        if s["modo"] == "Torneo":
            errors += _check_torneo(s)
        else:
            errors += _check_cash(s)

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


def filter_valid(scenarios: list[dict]) -> tuple[list[dict], list[str]]:
    ok, log = [], []
    for s in scenarios:
        errs = check(s)
        if errs:
            log.append(f"{s.get('id','?')}: {'; '.join(errs)}")
        else:
            ok.append(s)
    return ok, log

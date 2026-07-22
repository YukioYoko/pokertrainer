"""hand_generator.py — Escenarios de MANO COMPLETA (postflop: flop→turn→river).

El héroe defiende la Ciega Grande frente a un open del Botón (heads-up, 100 BB).
En cada calle el villano apuesta (línea guionizada por el generador) y el héroe
decide SOLO Call/Fold. La respuesta correcta de cada calle se deriva
EXCLUSIVAMENTE de:
    Call si equity(héroe vs rango de apuesta del villano, cartas por venir)
    >= pot_odds, si no Fold.
La equidad es Monte Carlo con eval7 en flop/turn y enumeración exacta en el
river; el rango de apuesta se construye con la ratio de Janda por calle
(cash_ranges.build_street_bet_range). Sin subir del héroe y sin solver: cada
nodo es una decisión binaria verificable, en la línea de la Regla de Oro.

El héroe juega las tres calles seguidas; el repaso paso a paso lo redacta
explain.py a partir de la matemática ya calculada aquí.
"""
from __future__ import annotations

import random

import cash_math as cm
import cash_ranges as cr
import poker_math as pm

VILLAIN_POS = "BTN"
POS_LABEL = {
    "BTN": {"es": "Botón", "en": "Button"},
    "BB": {"es": "Ciega Grande", "en": "Big Blind"},
}
POT_FLOP_BB = 5.5                       # BTN 2.5 + BB 2.5 + SB 0.5 muerto
BET_FRACTIONS = [0.33, 0.5, 0.66, 0.75]
STREETS = ["Flop", "Turn", "River"]


def _deal(rng: random.Random):
    cards = rng.sample(list(pm._CARD), 7)
    return cards[:2], cards[2:]         # (hero, board5)


def _street_node(hero, board_partial, pot, frac, rng, seed_off):
    bet = round(pot * frac, 2)
    bluff_frac = cm.value_bluff_ratio(bet, pot)
    combos, info = cr.build_street_bet_range(VILLAIN_POS, board_partial, hero,
                                             bluff_frac)
    if info["n_value"] < 6:
        return None
    if len(board_partial) == 5:
        equity = pm.equity_river_exact(hero, combos, board_partial)
    else:
        equity = pm.equity_vs_combos_mc(hero, combos, board_partial,
                                        seed=seed_off)
    podds = cm.pot_odds_call(bet, pot)
    correct = 1 if equity >= podds else 0
    node = {
        "calle": STREETS[len(board_partial) - 3],
        "board": board_partial,
        "villano_apuesta_bb": bet,
        "pozo_previo_bb": round(pot, 2),
        "opciones": ["Fold", "Call"],
        "opcion_correcta_index": correct,
        "math": {"equity": equity, "pot_odds": podds,
                 "value_bluff_ratio": bluff_frac},
        "_rango": info,
    }
    return node, round(pot + 2 * bet, 2)   # nodo, pozo si el héroe paga


def _check_node(hero, board, pot, frac):
    """Nodo de RIVER donde el villano PASA: el héroe elige Check/Fold/Bet.

    Verificable (river = equidad exacta): correcto = Bet si EV(apostar) >
    EV(pasar). El villano capa su rango al pasar (todo lo que NO apostaría) y,
    frente a una apuesta, defiende por MDF con sus manos más fuertes. Foldear
    nunca es correcto: pasar es gratis (opción-trampa pedagógica).
    """
    dead = set(hero) | set(board)
    full = [c for c in pm.expand_range(cr.OPEN_RANGES[VILLAIN_POS])
            if c[0] not in dead and c[1] not in dead]
    bluff_frac = cm.value_bluff_ratio(round(pot * 0.66, 2), pot)
    bet_combos, _info = cr.build_river_bet_range(VILLAIN_POS, board, hero,
                                                 bluff_frac)
    bet_set = set(bet_combos)
    check_range = [c for c in full if c not in bet_set]
    if len(check_range) < 12:                 # rango de check demasiado fino
        return None

    bet = round(pot * frac, 2)
    mdf = cm.mdf(bet, pot)
    ranked = sorted(check_range, key=lambda c: cr._strength(c, board)[1],
                    reverse=True)
    calling = ranked[:max(1, round(mdf * len(check_range)))]
    eq_check = pm.equity_river_exact(hero, check_range, board)
    eq_call = pm.equity_river_exact(hero, calling, board)
    # Se redondea ANTES de decidir para que la respuesta coincida exactamente
    # con lo que re-verifica validate a partir de los valores almacenados.
    ev_pasar = round(eq_check * pot, 3)
    ev_apostar = round((1 - mdf) * pot + mdf * (
        eq_call * (pot + bet) - (1 - eq_call) * bet), 3)
    correct = 2 if ev_apostar > ev_pasar else 0   # 0=Check, 1=Fold, 2=Bet

    node = {
        "calle": "River",
        "board": board,
        "villano_pasa": True,
        "villano_apuesta_bb": 0,
        "apuesta_heroe_bb": bet,
        "pozo_previo_bb": round(pot, 2),
        "opciones": ["Check", "Fold", "Bet"],
        "opcion_correcta_index": correct,
        "math": {
            "equity": eq_check,
            "eq_call": eq_call,
            "mdf": round(mdf, 4),
            "ev_pasar": round(ev_pasar, 3),
            "ev_apostar": round(ev_apostar, 3),
        },
        "_rango": {"n_check": len(check_range), "n_call": len(calling)},
    }
    return node, round(pot, 2)                # pasar no cambia el pozo


def _closeness(nd) -> float:
    """Cuán ajustada es la decisión del nodo (0 = línea muy fina)."""
    m = nd["math"]
    if nd.get("villano_pasa"):
        return abs(m["ev_apostar"] - m["ev_pasar"]) / max(nd["pozo_previo_bb"], 1)
    return abs(m["equity"] - m["pot_odds"])


def _difficulty(nodes) -> str:
    dmin = min(_closeness(n) for n in nodes)
    if dmin <= 0.05:
        return "Avanzado"
    if dmin <= 0.12:
        return "Intermedio"
    return "Principiante"


def generate(n: int = 60, seed: int = 3042) -> list[dict]:
    rng = random.Random(seed)
    scenarios: list[dict] = []
    seen: set[tuple] = set()
    quota = {"Principiante": 0, "Intermedio": 0, "Avanzado": 0}
    target = {"Principiante": n // 3, "Intermedio": n // 3,
              "Avanzado": n - 2 * (n // 3)}

    attempts = 0
    while len(scenarios) < n and attempts < n * 1500:
        attempts += 1
        hero, board = _deal(rng)
        # El héroe no debe flopear los nuts (aburrido) ni ir a ciegas total.
        lvl_flop, _ = cr._strength((hero[0], hero[1]), board[:3])
        if lvl_flop > 4:
            continue

        fracs = [rng.choice(BET_FRACTIONS) for _ in range(3)]
        # En ~40% de las manos el villano PASA el river y el héroe decide
        # Check/Fold/Bet en vez de enfrentar una apuesta.
        river_check = rng.random() < 0.4
        nodes = []
        pot = POT_FLOP_BB
        ok = True
        for i in range(3):
            if i == 2 and river_check:
                res = _check_node(hero, board, pot, fracs[i])
            else:
                res = _street_node(hero, board[:3 + i], pot, fracs[i], rng,
                                   seed + len(scenarios) + i + 1)
            if res is None:
                ok = False
                break
            node, pot = res
            nodes.append(node)
        if not ok:
            continue

        diff = _difficulty(nodes)
        if quota[diff] >= target[diff]:
            continue
        key = (tuple(sorted(hero)), tuple(sorted(board)), tuple(fracs),
               river_check)
        if key in seen:
            continue
        seen.add(key)
        quota[diff] += 1

        hand = pm.hand_to_notation(hero)
        # leaks: una etiqueta por cada calle mal jugable (para el analizador).
        leaks = ["mano_completa"]
        if any(not nd.get("villano_pasa") and nd["opcion_correcta_index"] == 0
               for nd in nodes):
            leaks.append("continuar_sin_odds")
        if any(nd.get("villano_pasa") for nd in nodes):
            leaks.append("decision_check_river")
        if diff == "Avanzado":
            leaks.append("spot_borderline")

        # Se guarda _rango dentro de cada nodo para explain; se quita al final.
        scenarios.append({
            "id": f"hand_{len(scenarios) + 1:04d}",
            "modo": "Mano Completa",
            "tipo": "hand_full",
            "fase": "Multi",
            "dificultad": diff,
            "posicion_heroe": "BB",
            "posicion_villano": VILLAIN_POS,
            "cartas_heroe": hero,
            "board": board,
            "stack_bb": 100,
            "pozo_bb": pot,                # pozo final si paga las tres calles
            "opciones": ["Fold", "Call"],
            "calles": nodes,
            "leak_tags": leaks,
            "_meta": {
                "hand": hand,
                "pos_label": POS_LABEL["BTN"],
                "pos_label_heroe": POS_LABEL["BB"],
            },
        })
    return scenarios


if __name__ == "__main__":
    for s in generate(3):
        print(s["id"], s["_meta"]["hand"], "board", " ".join(s["board"]))
        for nd in s["calles"]:
            m = nd["math"]
            print(f"  {nd['calle']:5s} bet {nd['villano_apuesta_bb']:>4} "
                  f"eq={m['equity']:.2f} odds={m['pot_odds']:.2f} -> "
                  f"{nd['opciones'][nd['opcion_correcta_index']]}")

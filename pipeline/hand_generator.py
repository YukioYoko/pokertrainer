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


def _difficulty(nodes) -> str:
    dmin = min(abs(n["math"]["equity"] - n["math"]["pot_odds"]) for n in nodes)
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
        nodes = []
        pot = POT_FLOP_BB
        ok = True
        for i in range(3):
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
        key = (tuple(sorted(hero)), tuple(sorted(board)), tuple(fracs))
        if key in seen:
            continue
        seen.add(key)
        quota[diff] += 1

        hand = pm.hand_to_notation(hero)
        # leaks: una etiqueta por cada calle mal jugable (para el analizador).
        leaks = ["mano_completa"]
        if any(nd["opcion_correcta_index"] == 0 for nd in nodes):
            leaks.append("continuar_sin_odds")
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

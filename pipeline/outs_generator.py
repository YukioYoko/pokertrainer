"""outs_generator.py — Escenarios de PROBABILIDAD DE OUTS (flop, a veces turn).

Se muestra la mano del héroe y el board (3 o 4 cartas). El jugador elige, entre
4 porcentajes, la probabilidad de LIGAR al menos uno de sus outs para el river.

Todo es verificable y exacto (Regla de Oro):
  - out = carta no vista que MEJORA la categoría de la mano del héroe (se cuenta
    reevaluando con eval7/handeval, la misma clasificación que cash_ranges).
  - prob = probabilidad hipergeométrica exacta de que aparezca >=1 out entre las
    cartas por venir (2 desde el flop, 1 desde el turn). Sin Monte Carlo.
  - opción correcta = el porcentaje ofrecido más cercano a esa prob exacta.
No hay decisión de apuesta: es un ejercicio puro de cálculo de outs.
"""
from __future__ import annotations

import math
import random

import cash_ranges as cr
import handeval
import poker_math as pm

# Nombre localizado de la categoría a la que se liga (para la explicación).
DRAW_NAME = {
    "Straight Flush": {"es": "escalera de color", "en": "straight flush"},
    "Quads": {"es": "póker", "en": "quads"},
    "Full House": {"es": "full", "en": "full house"},
    "Flush": {"es": "color", "en": "flush"},
    "Straight": {"es": "escalera", "en": "straight"},
    "Trips": {"es": "trío", "en": "trips"},
    "Two Pair": {"es": "doble pareja", "en": "two pair"},
    "Pair": {"es": "pareja", "en": "pair"},
}


# Solo contamos outs hacia una mano FUERTE (escalera o mejor): son los outs
# "de verdad" de un proyecto. Emparejar la carta alta no cuenta como out.
_STRAIGHT = cr._HT_ORDER.index("Straight")


def _count_outs(hero: list[str], board: list[str]) -> tuple[int, str]:
    """Nº de cartas no vistas que llevan la mano a escalera o mejor USANDO las
    cartas del héroe (no un ligue del propio board), y la categoría más común.

    En el flop (3 cartas) sumar 1 deja 4 comunitarias: una mano de 5 cartas
    (escalera+) obliga a usar una carta del héroe, así que basta la categoría.
    En el turn (4 cartas) sumar 1 deja 5 comunitarias: hay que exigir además que
    la mano del héroe SUPERE a lo que liga el board por sí solo (si no, es un
    ligue del board que no ayuda al héroe)."""
    dead = set(hero) | set(board)
    turn = len(board) == 4
    outs = 0
    targets: dict[str, int] = {}
    for c in pm._CARD:
        if c in dead:
            continue
        level, score = cr._strength((hero[0], hero[1]), board + [c])
        if level < _STRAIGHT:
            continue
        if turn:
            board_score = handeval.evaluate([pm._CARD[x] for x in board + [c]])
            if score <= board_score:      # el board liga igual o mejor: no es out
                continue
        outs += 1
        name = handeval.handtype(score)
        targets[name] = targets.get(name, 0) + 1
    target = max(targets, key=targets.get) if targets else "Straight"
    return outs, target


def _hit_prob(outs: int, unseen: int, to_come: int) -> float:
    """Probabilidad exacta de que aparezca al menos un out entre las cartas por
    venir (hipergeométrica): 1 - C(unseen-outs, to_come)/C(unseen, to_come)."""
    miss = math.comb(unseen - outs, to_come) / math.comb(unseen, to_come)
    return round(1 - miss, 4)


def _options(true_pct: int, rng: random.Random) -> tuple[list[str], int]:
    """4 porcentajes: el correcto + 3 distractores plausibles y distintos."""
    pool = [true_pct + d for d in (-20, -14, -8, 8, 14, 20)]
    pool = [p for p in pool if 3 <= p <= 94 and p != true_pct]
    rng.shuffle(pool)
    distractors = []
    for p in pool:
        if all(abs(p - q) >= 5 for q in distractors + [true_pct]):
            distractors.append(p)
        if len(distractors) == 3:
            break
    while len(distractors) < 3:                     # respaldo defensivo
        p = max(3, min(94, true_pct + rng.choice([-25, 25, -30, 30])))
        if p not in distractors and abs(p - true_pct) >= 5:
            distractors.append(p)
    pcts = sorted(distractors + [true_pct])
    return [f"{p}%" for p in pcts], pcts.index(true_pct)


def _difficulty(outs: int, to_come: int) -> str:
    if to_come == 2 and outs in (8, 9):      # color / escalera abierta clásicos
        return "Principiante"
    if to_come == 1 or outs <= 6:            # turn, o proyectos finos
        return "Intermedio" if outs >= 4 else "Avanzado"
    return "Intermedio" if outs <= 12 else "Avanzado"


def generate(n: int = 80, seed: int = 4042) -> list[dict]:
    rng = random.Random(seed)
    scenarios: list[dict] = []
    seen: set[tuple] = set()
    quota = {"Principiante": 0, "Intermedio": 0, "Avanzado": 0}
    target_q = {"Principiante": n // 3, "Intermedio": n // 3,
                "Avanzado": n - 2 * (n // 3)}

    attempts = 0
    while len(scenarios) < n and attempts < n * 800:
        attempts += 1
        n_board = 3 if rng.random() < 0.6 else 4          # flop 60% / turn 40%
        cards = rng.sample(list(pm._CARD), 2 + n_board)
        hero, board = cards[:2], cards[2:]

        cur_level, _ = cr._strength((hero[0], hero[1]), board)
        if cur_level >= _STRAIGHT:            # ya tiene escalera+: no es proyecto
            continue
        if cur_level > cr._HT_ORDER.index("Pair"):   # más que 1 pareja: no proyecta
            continue
        outs, draw_target = _count_outs(hero, board)
        if not (4 <= outs <= 15):             # sin proyecto real / demasiado raro
            continue

        unseen = 52 - len(hero) - len(board)
        to_come = 5 - len(board)
        prob = _hit_prob(outs, unseen, to_come)
        true_pct = round(prob * 100)

        diff = _difficulty(outs, to_come)
        if quota[diff] >= target_q[diff]:
            continue
        key = (tuple(sorted(hero)), tuple(sorted(board)))
        if key in seen:
            continue
        seen.add(key)
        quota[diff] += 1

        opciones, correct = _options(true_pct, rng)
        scenarios.append({
            "id": f"outs_{len(scenarios) + 1:04d}",
            "modo": "Outs",
            "tipo": "outs",
            "fase": "Flop" if n_board == 3 else "Turn",
            "dificultad": diff,
            "posicion_heroe": "BB",
            "posicion_villano": "BTN",
            "cartas_heroe": hero,
            "board": board,
            "opciones": opciones,
            "opcion_correcta_index": correct,
            "math": {
                "prob": prob,
                "outs": outs,
                "cartas_por_venir": to_come,
                "regla_pulgar": outs * (4 if to_come == 2 else 2),
            },
            "leak_tags": ["calculo_outs"] + (
                ["spot_borderline"] if diff == "Avanzado" else []),
            "_meta": {
                "hand": pm.hand_to_notation(hero),
                "draw_target": draw_target,
                "draw_name": DRAW_NAME.get(draw_target,
                                           {"es": "mejor mano", "en": "better hand"}),
                "true_pct": true_pct,
            },
        })
    return scenarios


if __name__ == "__main__":
    for s in generate(6):
        m = s["math"]
        print(s["id"], s["_meta"]["hand"], "board", " ".join(s["board"]),
              f"outs={m['outs']} prob={m['prob']:.2f}", s["opciones"],
              "->", s["opciones"][s["opcion_correcta_index"]])

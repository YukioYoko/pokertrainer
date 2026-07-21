"""cash_ranges.py — Rangos embebidos para Cash 100 BB. Nada lo inventa el LLM.

1. Rangos de apertura preflop simplificados (estándares de la literatura,
   estilo Janda/charts modernos) por posición del villano.
2. Constructor del rango de APUESTA del villano en el river:
   - Valor: combos del rango preflop que en este board son doble pareja o
     mejor, o top pair con kicker fuerte (clasificación exacta con eval7).
   - Faroles: los combos SIN pareja más débiles, añadidos exactamente en la
     proporción de Janda (value_bluff_ratio) para el tamaño de apuesta dado.
   El rango resultante es una construcción matemática verificable, no una
   opinión.
"""
from __future__ import annotations

import eval7

import poker_math as pm

PAIRS = [r * 2 for r in "AKQJT98765432"]

# ------------------------------------------------------ aperturas preflop ---
OPEN_RANGES: dict[str, list[str]] = {
    # UTG 6-max ~15%: parejas medias+, broadways fuertes, Ax suited
    "UTG": [
        *PAIRS[:9],  # 66+
        "AKs", "AQs", "AJs", "ATs", "A9s", "A5s", "A4s",
        "AKo", "AQo", "AJo",
        "KQs", "KJs", "KTs", "KQo",
        "QJs", "QTs", "JTs", "T9s", "98s",
    ],
    # CO ~27%
    "CO": [
        *PAIRS,
        "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s",
        "A5s", "A4s", "A3s", "A2s",
        "AKo", "AQo", "AJo", "ATo", "A9o",
        "KQs", "KJs", "KTs", "K9s", "KQo", "KJo", "KTo",
        "QJs", "QTs", "Q9s", "QJo", "QTo",
        "JTs", "J9s", "JTo", "T9s", "T8s", "98s", "97s", "87s", "76s", "65s",
    ],
    # BTN ~44%
    "BTN": [
        *PAIRS,
        *[f"A{r}s" for r in "KQJT98765432"],
        *[f"A{r}o" for r in "KQJT98765432"],
        *[f"K{r}s" for r in "QJT98765432"],
        "KQo", "KJo", "KTo", "K9o", "K8o",
        "QJs", "QTs", "Q9s", "Q8s", "Q7s", "Q6s", "QJo", "QTo", "Q9o",
        "JTs", "J9s", "J8s", "J7s", "JTo", "J9o",
        "T9s", "T8s", "T7s", "T9o",
        "98s", "97s", "96s", "98o", "87s", "86s", "76s", "75s", "65s",
        "64s", "54s", "53s", "43s",
    ],
}

# --------------------------------------------------- clasificación exacta ---
_HT_ORDER = ["High Card", "Pair", "Two Pair", "Trips", "Straight",
             "Flush", "Full House", "Quads", "Straight Flush"]


def _strength(combo: tuple[str, str], board: list[str]) -> tuple[int, int]:
    """(nivel_de_mano, score_eval7) del combo en este board."""
    cards = [pm._CARD[combo[0]], pm._CARD[combo[1]]] + \
            [pm._CARD[c] for c in board]
    score = eval7.evaluate(cards)
    return _HT_ORDER.index(eval7.handtype(score)), score


def _is_top_pair_strong(combo: tuple[str, str], board: list[str]) -> bool:
    """Top pair (pareja con la carta más alta del board) y kicker T+."""
    top_rank = max(board, key=lambda c: pm.RANKS.index(c[0]))[0]
    ranks = [combo[0][0], combo[1][0]]
    if top_rank not in ranks:
        return False
    kicker = ranks[0] if ranks[1] == top_rank else ranks[1]
    return pm.RANKS.index(kicker) >= pm.RANKS.index("T")


def build_river_bet_range(
    villain_pos: str,
    board: list[str],
    hero: list[str],
    bluff_fraction: float,
) -> tuple[list[tuple[str, str]], dict]:
    """Rango de apuesta del villano en el river.

    Valor = doble pareja+ o top pair fuerte. Faroles = los combos sin pareja
    más débiles, en cantidad = valor * bluff_fraction / (1 - bluff_fraction)
    (así los faroles son exactamente `bluff_fraction` del rango total).
    Devuelve (combos, info) con conteos para el desglose pedagógico.
    """
    dead = set(hero) | set(board)
    combos = [c for c in pm.expand_range(OPEN_RANGES[villain_pos])
              if c[0] not in dead and c[1] not in dead]

    value, air = [], []
    for c in combos:
        level, score = _strength(c, board)
        if level >= 2 or (level == 1 and _is_top_pair_strong(c, board)):
            value.append(c)
        elif level == 0:
            air.append((score, c))

    air.sort(key=lambda x: x[0])  # los más débiles primero: faroles naturales
    n_bluffs = round(len(value) * bluff_fraction / (1 - bluff_fraction)) \
        if bluff_fraction < 1 else 0
    bluffs = [c for _, c in air[:n_bluffs]]

    info = {"n_value": len(value), "n_bluffs": len(bluffs),
            "bluff_fraction_real": round(
                len(bluffs) / (len(value) + len(bluffs)), 4)
            if value or bluffs else 0.0}
    return value + bluffs, info

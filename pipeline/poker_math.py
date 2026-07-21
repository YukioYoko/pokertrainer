"""poker_math.py — Cálculos exactos. Ningún número sale del LLM.

Equidad por Monte Carlo con eval7 (héroe vs rango del villano),
pot odds, SPR y outs. Todo determinista vía semilla.
"""
from __future__ import annotations

import random
from typing import Iterable

import eval7

RANKS = "23456789TJQKA"
SUITS = "cdhs"


# ---------------------------------------------------------------- helpers ---
def hand_to_notation(cards: list[str]) -> str:
    """['As','Kd'] -> 'AKo' | ['7h','7c'] -> '77' | ['J9s'...] etc."""
    r1, s1 = cards[0][0], cards[0][1]
    r2, s2 = cards[1][0], cards[1][1]
    if RANKS.index(r1) < RANKS.index(r2):
        r1, r2, s1, s2 = r2, r1, s2, s1
    if r1 == r2:
        return r1 + r2
    return r1 + r2 + ("s" if s1 == s2 else "o")


def expand_range(notations: Iterable[str]) -> list[tuple[str, str]]:
    """Convierte notaciones ('AKs','77','QJo') en combos concretos de 2 cartas."""
    combos: list[tuple[str, str]] = []
    for n in notations:
        if len(n) == 2:  # pareja
            r = n[0]
            cards = [r + s for s in SUITS]
            for i in range(4):
                for j in range(i + 1, 4):
                    combos.append((cards[i], cards[j]))
        else:
            r1, r2, kind = n[0], n[1], n[2]
            if kind == "s":
                combos += [(r1 + s, r2 + s) for s in SUITS]
            else:  # offsuit
                combos += [
                    (r1 + s1, r2 + s2)
                    for s1 in SUITS
                    for s2 in SUITS
                    if s1 != s2
                ]
    return combos


# ----------------------------------------------------------------- equity ---
_CARD = {r + s: eval7.Card(r + s) for r in RANKS for s in SUITS}


def equity_vs_range(
    hero: list[str],
    villain_range: Iterable[str],
    board: list[str] | None = None,
    iters: int = 20000,
    seed: int = 7,
) -> float:
    """Equidad del héroe vs un rango, por Monte Carlo. Devuelve 0..1."""
    rng = random.Random(seed)
    board = board or []
    hero_cards = [_CARD[c] for c in hero]
    board_cards = [_CARD[c] for c in board]
    dead = set(hero) | set(board)
    combos = [
        (_CARD[a], _CARD[b], a, b)
        for a, b in expand_range(villain_range)
        if a not in dead and b not in dead
    ]
    if not combos:
        return 0.0

    deck_master = [c for c in _CARD if c not in dead]
    need = 5 - len(board)
    wins = ties = total = 0
    for _ in range(iters):
        ca, cb, a, b = combos[rng.randrange(len(combos))]
        runout = board_cards + [
            _CARD[c] for c in rng.sample(deck_master, need + 2)
            if c not in (a, b)
        ][:need]
        h = eval7.evaluate(hero_cards + runout)
        vv = eval7.evaluate([ca, cb] + runout)
        if h > vv:
            wins += 1
        elif h == vv:
            ties += 1
        total += 1
    return round((wins + ties / 2) / total, 4)


def equity_river_exact(
    hero: list[str],
    villain_combos: list[tuple[str, str]],
    board: list[str],
) -> float:
    """Equidad EXACTA en el river (board completo): enumera cada combo
    del rango del villano y compara showdowns. Sin Monte Carlo."""
    hero_cards = [_CARD[c] for c in hero]
    board_cards = [_CARD[c] for c in board]
    dead = set(hero) | set(board)
    h = eval7.evaluate(hero_cards + board_cards)
    wins = ties = total = 0
    for a, b in villain_combos:
        if a in dead or b in dead:
            continue
        vv = eval7.evaluate([_CARD[a], _CARD[b]] + board_cards)
        if h > vv:
            wins += 1
        elif h == vv:
            ties += 1
        total += 1
    return round((wins + ties / 2) / total, 4) if total else 0.0


# ------------------------------------------------------------- aritmética ---
def pot_odds(to_call_bb: float, pot_bb: float) -> float:
    """Equidad mínima requerida para pagar: call / (pot + call). 0..1."""
    return round(to_call_bb / (pot_bb + to_call_bb), 4)


def spr(stack_bb: float, pot_bb: float) -> float:
    """Stack-to-Pot Ratio."""
    return round(stack_bb / pot_bb, 2) if pot_bb else 0.0


def outs_preflop() -> int:
    """Pre-flop no hay proyecto definido: outs = 0 por convención del MVP."""
    return 0

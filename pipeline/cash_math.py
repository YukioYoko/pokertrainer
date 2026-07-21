"""cash_math.py — Matemática exacta de Cash Games (river, apuesta única).

Sin solver: solo fórmulas cerradas y enumeración exacta.
  - pot_odds_call: equidad mínima para pagar (reutiliza poker_math).
  - mdf: frecuencia mínima de defensa = pot / (pot + bet).
  - value_bluff_ratio (Janda): fracción máxima de faroles inexplotable
    para un tamaño de apuesta dado = bet / (pot + 2*bet).
  - equity_river: enumeración exacta del héroe vs combos del villano
    (reutiliza poker_math.equity_river_exact).
"""
from __future__ import annotations

import poker_math as pm


def pot_odds_call(bet_bb: float, pot_before_bet_bb: float) -> float:
    """Equidad mínima para pagar: bet / (pot_antes + 2*bet). 0..1."""
    return pm.pot_odds(bet_bb, pot_before_bet_bb + bet_bb)


def mdf(bet_bb: float, pot_before_bet_bb: float) -> float:
    """Frecuencia mínima de defensa: pot / (pot + bet). 0..1."""
    return round(pot_before_bet_bb / (pot_before_bet_bb + bet_bb), 4)


def value_bluff_ratio(bet_bb: float, pot_before_bet_bb: float) -> float:
    """Janda: % máximo de faroles en el rango de apuesta que sigue siendo
    inexplotable = bet / (pot + 2*bet). 0..1."""
    return round(bet_bb / (pot_before_bet_bb + 2 * bet_bb), 4)


def equity_river(hero: list[str],
                 villain_combos: list[tuple[str, str]],
                 board: list[str]) -> float:
    """Equidad exacta del héroe en el river contra combos concretos."""
    return pm.equity_river_exact(hero, villain_combos, board)

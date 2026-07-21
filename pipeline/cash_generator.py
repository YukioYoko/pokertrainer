"""cash_generator.py — Escenarios de Cash (river, apuesta única, 100 BB).

La decisión correcta se deriva EXCLUSIVAMENTE de:
    Call si equity_exacta >= pot_odds_requeridas, si no Fold.
donde la equidad es una enumeración exacta contra un rango de apuesta
construido con la ratio de Janda (cash_ranges.build_river_bet_range).

Opciones siempre [Fold, Call]: nunca se ofrece Raise porque su corrección
no es verificable sin solver (Regla de Oro).
"""
from __future__ import annotations

import random

import cash_math as cm
import cash_ranges as cr
import poker_math as pm

VILLAIN_POSITIONS = ["UTG", "CO", "BTN"]
POS_LABEL = {
    "UTG": {"es": "Under the Gun", "en": "Under the Gun"},
    "CO": {"es": "Cutoff", "en": "Cutoff"},
    "BTN": {"es": "Botón", "en": "Button"},
    "BB": {"es": "Ciega Grande", "en": "Big Blind"},
}
BET_SIZES = [0.5, 0.75, 1.0, 1.5]   # fracción del pozo
POTS_BB = [6, 9, 12, 18]            # pozo al llegar al river (100 BB efectivo)

# Manos del héroe (defensor en BB): capadas a bluff-catchers y manos medias,
# el tipo de mano donde la decisión de river es un problema real de pot odds.
HERO_HANDS = [
    *[r * 2 for r in "JT98765433"],
    "AJs", "ATs", "A9s", "A8s", "A5s", "AJo", "ATo",
    "KQs", "KJs", "KTs", "K9s", "KQo", "KJo", "KTo",
    "QJs", "QTs", "Q9s", "QJo", "QTo",
    "JTs", "J9s", "JTo", "T9s", "T8s", "98s", "87s", "76s",
]


def _deal_hand(hand: str, rng: random.Random, dead: set) -> list[str] | None:
    for _ in range(20):
        if len(hand) == 2:
            s = rng.sample(pm.SUITS, 2)
            cards = [hand[0] + s[0], hand[1] + s[1]]
        elif hand[2] == "s":
            s = rng.choice(pm.SUITS)
            cards = [hand[0] + s, hand[1] + s]
        else:
            s1, s2 = rng.sample(pm.SUITS, 2)
            cards = [hand[0] + s1, hand[1] + s2]
        if not set(cards) & dead:
            return cards
    return None


def _deal_board(rng: random.Random, dead: set) -> list[str]:
    deck = [c for c in pm._CARD if c not in dead]
    return rng.sample(deck, 5)


def _difficulty(equity: float, pot_odds: float) -> str:
    dist = abs(equity - pot_odds)
    if dist <= 0.04:
        return "Avanzado"
    if dist <= 0.10:
        return "Intermedio"
    return "Principiante"


def generate(n: int = 100, seed: int = 1042) -> list[dict]:
    rng = random.Random(seed)
    scenarios: list[dict] = []
    seen: set[tuple] = set()
    quota = {"Principiante": 0, "Intermedio": 0, "Avanzado": 0}
    target = {"Principiante": n // 3, "Intermedio": n // 3,
              "Avanzado": n - 2 * (n // 3)}

    attempts = 0
    while len(scenarios) < n and attempts < n * 800:
        attempts += 1
        vpos = rng.choice(VILLAIN_POSITIONS)
        pot = rng.choice(POTS_BB)
        frac = rng.choice(BET_SIZES)
        bet = round(pot * frac, 2)
        hand = rng.choice(HERO_HANDS)

        board = _deal_board(rng, set())
        hero = _deal_hand(hand, rng, set(board))
        if hero is None:
            continue

        # El héroe debe tener algo intermedio: sin pareja no hay decisión,
        # con doble pareja+ el call es trivial y aburrido.
        level, _ = cr._strength((hero[0], hero[1]), board)
        if level == 0 or level > 2:
            continue

        bluff_frac = cm.value_bluff_ratio(bet, pot)
        combos, rango_info = cr.build_river_bet_range(vpos, board, hero,
                                                      bluff_frac)
        if rango_info["n_value"] < 8:   # board que machaca el rango: descartar
            continue

        equity = cm.equity_river(hero, combos, board)
        podds = cm.pot_odds_call(bet, pot)
        correct = 1 if equity >= podds else 0

        diff = _difficulty(equity, podds)
        if quota[diff] >= target[diff]:
            continue
        key = (vpos, hand, tuple(sorted(board)), pot, frac)
        if key in seen:
            continue
        seen.add(key)
        quota[diff] += 1

        scenarios.append({
            "id": f"cash_rv_{len(scenarios) + 1:04d}",
            "modo": "Cash Game",
            "fase": "River",
            "dificultad": diff,
            "posicion_heroe": "BB",
            "posicion_villano": vpos,
            "stack_bb": 100 - bet - pot / 2,   # aproximación del resto detrás
            "pozo_bb": round(pot + bet, 2),    # pozo que ve el héroe (con bet)
            "cartas_heroe": hero,
            "board": board,
            "opciones": ["Fold", "Call"],
            "opcion_correcta_index": correct,
            "math": {
                "equity": equity,
                "pot_odds": podds,
                "spr": pm.spr(100 - pot / 2, pot),
                "outs": 0,
                "mdf": cm.mdf(bet, pot),
                "value_bluff_ratio": bluff_frac,
            },
            "leak_tags": _leak_tags(correct, diff),
            "_meta": {
                "hand": hand,
                "pos_label": POS_LABEL[vpos],
                "pos_label_heroe": POS_LABEL["BB"],
                "bet_bb": bet,
                "pot_before_bet_bb": pot,
                "bet_fraction": frac,
                "rango": rango_info,
            },
        })
    return scenarios


def _leak_tags(correct: int, diff: str) -> list[str]:
    tags = ["pagar_sin_odds_river"] if correct == 0 \
        else ["fold_excesivo_river"]
    if diff == "Avanzado":
        tags.append("spot_borderline")
    return tags


if __name__ == "__main__":
    for s in generate(5)[:5]:
        m = s["math"]
        print(s["id"], s["_meta"]["hand"], "board", " ".join(s["board"]),
              f"eq={m['equity']:.2f} odds={m['pot_odds']:.2f}",
              "->", s["opciones"][s["opcion_correcta_index"]])

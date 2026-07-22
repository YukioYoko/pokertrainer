"""generator.py — Crea escenarios de Torneo de forma determinista (semilla fija).

Escala hasta 2000+ escenarios sin repetir combinaciones. Ejes de variación:
  posición (UTG/MP/HJ/CO/BTN/SB) × mano (169) × stack (4–20 BB en pasos de 0.5)
y, si hicieran falta más combinaciones únicas, ejes extra documentados en el
propio escenario: ante por jugador (0.10–0.15 BB) y nº de jugadores (6/8/9).

La dificultad se controla por la distancia entre el stack y el umbral Nash:
  - Principiante: decisión clarísima (lejos del umbral, o basura).
  - Intermedio:   distancia moderada.
  - Avanzado:     borderline (stack pegado al umbral).
"""
from __future__ import annotations

import random

import nash
import poker_math as pm

POSITIONS = ["UTG", "MP", "HJ", "CO", "BTN", "SB"]
POS_LABEL = {
    "SB": {"es": "Ciega Pequeña", "en": "Small Blind"},
    "BTN": {"es": "Botón", "en": "Button"},
    "CO": {"es": "Cutoff", "en": "Cutoff"},
    "HJ": {"es": "Hijack", "en": "Hijack"},
    "MP": {"es": "Posición Media", "en": "Middle Position"},
    "UTG": {"es": "Under the Gun", "en": "Under the Gun"},
}
PLAYERS_BEHIND = {"SB": 1, "BTN": 2, "CO": 3, "HJ": 4, "MP": 5, "UTG": 6}
ANTES = [0.125, 0.10, 0.15]      # eje extra 1 (el primero es el estándar)
TABLE_SIZES = [8, 6, 9]          # eje extra 2 (el primero es el estándar)


def _all_hands() -> list[str]:
    hands = [r * 2 for r in pm.RANKS[::-1]]
    for i, r1 in enumerate(pm.RANKS[::-1]):
        for r2 in pm.RANKS[::-1][i + 1:]:
            hands += [r1 + r2 + "s", r1 + r2 + "o"]
    return hands


def _deal(hand: str, rng: random.Random) -> list[str]:
    if len(hand) == 2:
        s = rng.sample(pm.SUITS, 2)
        return [hand[0] + s[0], hand[1] + s[1]]
    r1, r2, kind = hand[0], hand[1], hand[2]
    if kind == "s":
        s = rng.choice(pm.SUITS)
        return [r1 + s, r2 + s]
    s1, s2 = rng.sample(pm.SUITS, 2)
    return [r1 + s1, r2 + s2]


def _difficulty(stack: float, threshold: float) -> str:
    if threshold == 0:
        return "Principiante"
    dist = abs(stack - threshold)
    if dist <= 1.5:
        return "Avanzado"
    if dist <= 4:
        return "Intermedio"
    return "Principiante"


def generate(n: int = 100, seed: int = 42, equity_iters: int = 8000) -> list[dict]:
    rng = random.Random(seed)
    hands = _all_hands()
    scenarios: list[dict] = []
    seen: set[tuple] = set()
    quota = {"Principiante": 0, "Intermedio": 0, "Avanzado": 0}
    target = {"Principiante": n // 3, "Intermedio": n // 3,
              "Avanzado": n - 2 * (n // 3)}

    # Fase 1: solo el eje base; fases extra amplían ante/mesa si se agota.
    phase = 0
    attempts = 0
    max_attempts = n * 600
    while len(scenarios) < n and attempts < max_attempts:
        attempts += 1
        if phase == 0:
            ante, players = ANTES[0], TABLE_SIZES[0]
        else:
            ante = rng.choice(ANTES)
            players = rng.choice(TABLE_SIZES)
        # Si llevamos muchos intentos sin progreso, abre los ejes extra.
        if phase == 0 and attempts > n * 200:
            phase = 1

        pos = rng.choice(POSITIONS)
        hand = rng.choice(hands)
        stack = round(rng.uniform(4, 20) * 2) / 2  # pasos de 0.5 BB

        threshold = nash.push_threshold(pos, hand)
        diff = _difficulty(stack, threshold)
        if quota[diff] >= target[diff]:
            continue
        key = (pos, hand, stack, ante, players)
        if key in seen:
            continue
        # UTG/MP no aplican si la mesa es de 6 (no existen esos asientos).
        if players == 6 and pos in ("UTG", "MP"):
            continue
        # Basura absoluta solo a veces (interés pedagógico limitado).
        if threshold == 0 and rng.random() > 0.25:
            continue
        seen.add(key)
        quota[diff] += 1

        hero_cards = _deal(hand, rng)
        correct = nash.correct_action(pos, hand, stack)
        pot = round(1.5 + ante * players, 2)
        equity = pm.equity_vs_range(
            hero_cards, nash.bb_call_range(stack),
            iters=equity_iters, seed=seed + len(scenarios),
        )
        podds = pm.pot_odds(stack, pot + stack)

        scenarios.append({
            "id": f"mtt_pf_{len(scenarios) + 1:04d}",
            "modo": "Torneo",
            "tipo": "push_fold",
            "fase": "Pre-Flop",
            "dificultad": diff,
            "posicion_heroe": pos,
            "posicion_villano": "BB",
            # Cosmético: el BB es el único villano modelado; los demás asientos
            # por hablar se pintan vacíos para comunicar el jam contra la mesa.
            "oponentes": [
                {"posicion": "BB", "rol": "ciega", "pos_label": POS_LABEL_BB},
            ],
            "asientos_vacios": max(PLAYERS_BEHIND[pos] - 1, 0),
            "stack_bb": stack,
            "pozo_bb": pot,
            "cartas_heroe": hero_cards,
            "board": [],
            "opciones": ["Fold", "All-In"],
            "opcion_correcta_index": correct,
            "math": {
                "equity": equity,
                "pot_odds": podds,
                "spr": pm.spr(stack, pot),
                "outs": pm.outs_preflop(),
            },
            "leak_tags": _leak_tags(pos, correct, diff),
            "_meta": {
                "hand": hand,
                "threshold": threshold,
                "pos_label": POS_LABEL[pos],
                "players_behind": PLAYERS_BEHIND[pos],
                "ante_bb": ante,
                "players": players,
            },
        })
    return scenarios


# Posiciones desde las que un rival puede ir all-in en un spot de overcall
# (el héroe cierra en la BB; excluimos SB para que su ciega quede muerta).
JAMMER_POSITIONS = ["UTG", "MP", "HJ", "CO", "BTN"]
SEATS_BETWEEN = {"UTG": 5, "MP": 4, "HJ": 3, "CO": 2, "BTN": 1}
POS_LABEL_BB = {"es": "Ciega Grande", "en": "Big Blind"}


def generate_overcall(n: int = 60, seed: int = 77, equity_iters: int = 8000):
    """Escenarios de Torneo donde el héroe (BB) PAGA o no un all-in rival.

    Un rival va All-In desde 'jammer_pos', todos foldean y la acción cierra en
    el héroe. La corrección se deriva EXCLUSIVAMENTE de:
        Call si equity(héroe vs rango de jam) >= pot_odds, si no Fold.
    El rango de jam se deriva de nash.jam_range (misma fuente de verdad que el
    push/fold); la equidad es Monte Carlo con eval7. Sin solver ni tabla nueva.
    Es chip-EV (no ICM): decisión de pago pura, como corresponde al MVP.
    """
    rng = random.Random(seed)
    hands = _all_hands()
    scenarios: list[dict] = []
    seen: set[tuple] = set()
    quota = {"Principiante": 0, "Intermedio": 0, "Avanzado": 0}
    target = {"Principiante": n // 3, "Intermedio": n // 3,
              "Avanzado": n - 2 * (n // 3)}

    attempts = 0
    while len(scenarios) < n and attempts < n * 800:
        attempts += 1
        jammer = rng.choice(JAMMER_POSITIONS)
        stack = round(rng.uniform(5, 15) * 2) / 2   # stack efectivo (ambos)
        ante, players = ANTES[0], TABLE_SIZES[0]

        jrange = nash.jam_range(jammer, stack)
        if len(jrange) < 4:            # jam demasiado estrecho: sin decisión real
            continue
        hand = rng.choice(hands)
        hero_cards = _deal(hand, rng)

        equity = pm.equity_vs_range(
            hero_cards, jrange, iters=equity_iters,
            seed=seed + len(scenarios) + 1,
        )
        dead = round(0.5 + ante * players, 2)        # SB + antes muertos
        to_call = round(stack - 1, 2)                # el BB ya puso 1 BB
        pot_before = round(stack + 1 + dead, 2)      # jam + BB del héroe + dead
        podds = pm.pot_odds(to_call, pot_before)
        correct = 1 if equity >= podds else 0

        dist = abs(equity - podds)
        diff = ("Avanzado" if dist <= 0.04 else
                "Intermedio" if dist <= 0.10 else "Principiante")
        if quota[diff] >= target[diff]:
            continue
        key = (jammer, hand, stack)
        if key in seen:
            continue
        seen.add(key)
        quota[diff] += 1

        tags = (["pago_ligero_vs_jam"] if correct == 0
                else ["fold_excesivo_vs_jam"])
        if diff == "Avanzado":
            tags.append("spot_borderline")

        scenarios.append({
            "id": f"mtt_call_{len(scenarios) + 1:04d}",
            "modo": "Torneo",
            "tipo": "overcall",
            "fase": "Pre-Flop",
            "dificultad": diff,
            "posicion_heroe": "BB",
            "posicion_villano": jammer,
            "oponentes": [
                {"posicion": jammer, "rol": "agresor",
                 "pos_label": POS_LABEL[jammer]},
            ],
            "asientos_vacios": SEATS_BETWEEN[jammer],
            "stack_bb": stack,
            "pozo_bb": round(pot_before + to_call, 2),  # bote si el héroe paga
            "cartas_heroe": hero_cards,
            "board": [],
            "opciones": ["Fold", "Call"],
            "opcion_correcta_index": correct,
            "math": {
                "equity": equity,
                "pot_odds": podds,
                "spr": pm.spr(stack, pot_before),
                "outs": pm.outs_preflop(),
            },
            "leak_tags": tags,
            "_meta": {
                "hand": hand,
                "threshold": nash.push_threshold(jammer, hand),
                "pos_label": POS_LABEL[jammer],
                "pos_label_heroe": POS_LABEL_BB,
                "players_behind": 0,
                "ante_bb": ante,
                "players": players,
                "jam_pos_label": POS_LABEL[jammer],
                "n_jam_combos": len(jrange),
                "to_call_bb": to_call,
            },
        })
    return scenarios


def _leak_tags(pos: str, correct: int, diff: str) -> list[str]:
    tags = []
    if correct == 1:
        tags.append("pasividad_stack_corto" if pos != "SB"
                    else "no_robar_ciegas")
    else:
        tags.append("push_demasiado_ancho")
    if diff == "Avanzado":
        tags.append("spot_borderline")
    return tags


if __name__ == "__main__":
    for s in generate(5)[:5]:
        print(s["id"], s["posicion_heroe"], s["_meta"]["hand"],
              s["stack_bb"], "->", s["opciones"][s["opcion_correcta_index"]])

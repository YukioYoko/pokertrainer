"""nash.py — Fuente de verdad de la decisión correcta (push/fold).

Tabla de umbrales tipo Nash (aproximación del equilibrio jam-or-fold,
estilo HoldemResources/ICMIZER) embebida por posición.

Representación estándar: para cada mano, el stack MÁXIMO en BB con el que
el All-In sigue siendo correcto desde esa posición. Si stack <= umbral,
la jugada correcta es All-In (1); si no, Fold (0).

El MVP limita stacks a 4–15 BB, la zona donde estas aproximaciones son
más robustas. También expone el rango de pago (call) del BB para que
poker_math calcule la equidad real del héroe cuando lo pagan.
"""
from __future__ import annotations

PAIRS = [r * 2 for r in "AKQJT98765432"]


def _tier(hands: list[str], bb: float) -> dict[str, float]:
    return {h: bb for h in hands}


# --------------------------------------------------------------------------
# SB vs BB (jam-or-fold clásico). En SB los rangos Nash son muy anchos.
# --------------------------------------------------------------------------
SB: dict[str, float] = {}
SB.update(_tier(PAIRS, 20))                                   # cualquier pareja
SB.update(_tier([f"A{r}s" for r in "KQJT98765432"], 20))       # Ax suited
SB.update(_tier([f"A{r}o" for r in "KQJT98765432"], 20))       # Ax offsuit
SB.update(_tier([f"K{r}s" for r in "QJT98765432"], 18))
SB.update(_tier([f"K{r}o" for r in "QJT9876"], 14))
SB.update(_tier(["K5o", "K4o", "K3o", "K2o"], 10))
SB.update(_tier([f"Q{r}s" for r in "JT98765"], 14))
SB.update(_tier(["Q4s", "Q3s", "Q2s"], 10))
SB.update(_tier([f"Q{r}o" for r in "JT98"], 10))
SB.update(_tier(["Q7o", "Q6o", "Q5o"], 7))
SB.update(_tier([f"J{r}s" for r in "T987"], 13))
SB.update(_tier(["J6s", "J5s", "J4s"], 9))
SB.update(_tier(["JTo", "J9o", "J8o"], 9))
SB.update(_tier(["J7o"], 6))
SB.update(_tier(["T9s", "T8s", "T7s"], 12))
SB.update(_tier(["T6s"], 8))
SB.update(_tier(["T9o", "T8o"], 8))
SB.update(_tier(["T7o"], 5))
SB.update(_tier(["98s", "97s", "87s", "86s", "76s", "75s", "65s", "64s", "54s"], 10))
SB.update(_tier(["98o", "87o", "76o", "65o"], 6))
SB.update(_tier(["96s", "85s", "53s", "43s"], 6))

# --------------------------------------------------------------------------
# BTN (quedan SB y BB por hablar): más estrecho que SB.
# --------------------------------------------------------------------------
BTN: dict[str, float] = {}
BTN.update(_tier(PAIRS[:9], 20))                               # 66+
BTN.update(_tier(["55", "44", "33", "22"], 12))
BTN.update(_tier([f"A{r}s" for r in "KQJT98765432"], 20))
BTN.update(_tier([f"A{r}o" for r in "KQJT9"], 20))
BTN.update(_tier(["A8o", "A7o", "A6o", "A5o", "A4o"], 13))
BTN.update(_tier(["A3o", "A2o"], 10))
BTN.update(_tier(["KQs", "KJs", "KTs", "K9s"], 16))
BTN.update(_tier(["K8s", "K7s", "K6s", "K5s"], 10))
BTN.update(_tier(["KQo", "KJo", "KTo"], 13))
BTN.update(_tier(["K9o"], 8))
BTN.update(_tier(["QJs", "QTs", "Q9s"], 12))
BTN.update(_tier(["QJo", "QTo"], 9))
BTN.update(_tier(["JTs", "J9s", "T9s", "98s", "87s", "76s"], 9))
BTN.update(_tier(["JTo"], 7))

# --------------------------------------------------------------------------
# CO (quedan 3 jugadores): más estrecho que BTN.
# --------------------------------------------------------------------------
CO: dict[str, float] = {}
CO.update(_tier(PAIRS[:7], 20))                                # 88+
CO.update(_tier(["77", "66", "55"], 13))
CO.update(_tier(["44", "33", "22"], 8))
CO.update(_tier(["AKs", "AQs", "AJs", "ATs", "A9s", "A8s"], 20))
CO.update(_tier(["A7s", "A6s", "A5s", "A4s", "A3s", "A2s"], 13))
CO.update(_tier(["AKo", "AQo", "AJo", "ATo"], 20))
CO.update(_tier(["A9o", "A8o"], 10))
CO.update(_tier(["A5o", "A4o"], 7))
CO.update(_tier(["KQs", "KJs", "KTs"], 13))
CO.update(_tier(["K9s"], 8))
CO.update(_tier(["KQo", "KJo"], 10))
CO.update(_tier(["KTo"], 7))
CO.update(_tier(["QJs", "QTs"], 9))
CO.update(_tier(["JTs", "T9s"], 7))

# --------------------------------------------------------------------------
# HJ (quedan 4 jugadores): el más estrecho del MVP.
# --------------------------------------------------------------------------
HJ: dict[str, float] = {}
HJ.update(_tier(PAIRS[:6], 20))                                # 99+
HJ.update(_tier(["88", "77", "66"], 11))
HJ.update(_tier(["55", "44"], 7))
HJ.update(_tier(["AKs", "AQs", "AJs", "ATs"], 20))
HJ.update(_tier(["A9s", "A8s"], 12))
HJ.update(_tier(["A5s", "A4s"], 9))
HJ.update(_tier(["AKo", "AQo", "AJo"], 18))
HJ.update(_tier(["ATo"], 11))
HJ.update(_tier(["KQs", "KJs"], 11))
HJ.update(_tier(["KTs"], 8))
HJ.update(_tier(["KQo"], 9))
HJ.update(_tier(["QJs"], 7))

# --------------------------------------------------------------------------
# MP (quedan 5 jugadores): más estrecho que HJ.
# --------------------------------------------------------------------------
MP: dict[str, float] = {}
MP.update(_tier(PAIRS[:5], 20))                                # TT+
MP.update(_tier(["99", "88", "77"], 10))
MP.update(_tier(["66", "55"], 6))
MP.update(_tier(["AKs", "AQs", "AJs", "ATs"], 20))
MP.update(_tier(["A9s"], 10))
MP.update(_tier(["A5s", "A4s"], 7))
MP.update(_tier(["AKo", "AQo"], 17))
MP.update(_tier(["AJo"], 12))
MP.update(_tier(["ATo"], 8))
MP.update(_tier(["KQs", "KJs"], 9))
MP.update(_tier(["KTs"], 6))
MP.update(_tier(["KQo"], 7))
MP.update(_tier(["QJs"], 6))

# --------------------------------------------------------------------------
# UTG (quedan 6+ jugadores): el rango más premium.
# --------------------------------------------------------------------------
UTG: dict[str, float] = {}
UTG.update(_tier(PAIRS[:4], 20))                               # JJ+
UTG.update(_tier(["TT", "99"], 12))
UTG.update(_tier(["88", "77"], 8))
UTG.update(_tier(["66", "55"], 5))
UTG.update(_tier(["AKs", "AQs", "AJs"], 20))
UTG.update(_tier(["ATs"], 12))
UTG.update(_tier(["A9s"], 7))
UTG.update(_tier(["A5s"], 6))
UTG.update(_tier(["AKo"], 20))
UTG.update(_tier(["AQo"], 13))
UTG.update(_tier(["AJo"], 8))
UTG.update(_tier(["KQs"], 8))
UTG.update(_tier(["KJs"], 6))
UTG.update(_tier(["KQo"], 5))

TABLES: dict[str, dict[str, float]] = {
    "SB": SB, "BTN": BTN, "CO": CO, "HJ": HJ, "MP": MP, "UTG": UTG,
}

# Rango con el que el BB paga un All-In (se estrecha al crecer el stack).
# Lo usa poker_math para calcular la equidad real del héroe cuando lo pagan.
BB_CALL_RANGES: dict[str, list[str]] = {
    "short": [  # stack efectivo <= 8 BB: el BB defiende ancho
        *PAIRS,
        *[f"A{r}s" for r in "KQJT98765432"],
        *[f"A{r}o" for r in "KQJT98765432"],
        "KQs", "KJs", "KTs", "K9s", "K8s", "KQo", "KJo", "KTo", "K9o",
        "QJs", "QTs", "Q9s", "QJo", "QTo", "JTs", "J9s", "JTo", "T9s", "98s",
    ],
    "deep": [  # stack efectivo > 8 BB: pago más estrecho
        *PAIRS[:11],  # 44+
        *[f"A{r}s" for r in "KQJT9876"],
        "A5s", "AKo", "AQo", "AJo", "ATo", "A9o",
        "KQs", "KJs", "KTs", "KQo", "KJo", "QJs", "QTs", "JTs",
    ],
}


def bb_call_range(stack_bb: float) -> list[str]:
    return BB_CALL_RANGES["short" if stack_bb <= 8 else "deep"]


def push_threshold(position: str, hand: str) -> float:
    """Stack máximo (BB) con el que la mano es un All-In correcto. 0 = nunca."""
    return TABLES[position].get(hand, 0.0)


def correct_action(position: str, hand: str, stack_bb: float) -> int:
    """0 = Fold, 1 = All-In. Única fuente de verdad del pipeline."""
    return 1 if stack_bb <= push_threshold(position, hand) else 0


def jam_range(position: str, stack_bb: float) -> list[str]:
    """Rango con el que 'position' va All-In a 'stack_bb' BB.

    Se deriva de la MISMA tabla de umbrales (fuente de verdad única): una mano
    entra en el rango de jam si su umbral de push es >= el stack efectivo.
    Sirve para calcular la equidad real del héroe cuando decide PAGAR un jam
    (spot de overcall), sin introducir ningún número nuevo inventado.
    """
    return [h for h, thr in TABLES[position].items() if thr >= stack_bb]

"""handeval.py — Evaluador de manos con la API que usa el pipeline (estilo
eval7), respaldado por `treys` (puro Python, sin compilador C).

Motivo: eval7 obliga a compilar con MSVC en Windows; treys se instala con un
simple `pip install`. Los rankings son idénticos (ambos son evaluadores exactos
de 7 cartas), así que las equidades no cambian. Se invierte la escala de treys
(donde 1 = mejor) para conservar la convención de eval7: MAYOR score = mejor.

Expone lo único que el pipeline consume de eval7:
  - Card(texto)         -> objeto carta ('As', 'Td', ...)
  - evaluate(cartas)    -> int, mayor = mejor (acepta lista plana de 5-7 cartas)
  - handtype(score)     -> str con los nombres que usa cash_ranges._HT_ORDER
"""
from __future__ import annotations

from treys import Card as _TCard, Evaluator as _Evaluator

_EV = _Evaluator()
_MAX = 7463                      # treys: 1..7462 (1=mejor). score = _MAX - rank

# treys usa "Three/Four of a Kind" y separa "Royal Flush"; el pipeline
# (cash_ranges._HT_ORDER) espera los nombres de eval7.
_CLASS_TO_EVAL7 = {
    "Royal Flush": "Straight Flush",
    "Straight Flush": "Straight Flush",
    "Four of a Kind": "Quads",
    "Full House": "Full House",
    "Flush": "Flush",
    "Straight": "Straight",
    "Three of a Kind": "Trips",
    "Two Pair": "Two Pair",
    "Pair": "Pair",
    "High Card": "High Card",
}


class Card:
    """Carta ligera; guarda el entero de treys y su texto original."""
    __slots__ = ("_i", "txt")

    def __init__(self, txt: str):
        self.txt = txt
        self._i = _TCard.new(txt)


def evaluate(cards: list[Card]) -> int:
    """Evalúa la mejor mano de 5 entre `cards` (lista plana de 5-7 cartas).
    Devuelve un int donde MAYOR = mejor (convención eval7)."""
    ints = [c._i for c in cards]
    rank = _EV.evaluate(ints[:2], ints[2:])   # treys: (hand, board), une ambas
    return _MAX - rank


def handtype(score: int) -> str:
    """Nombre de la categoría (estilo eval7) para un score de `evaluate`."""
    rank = _MAX - score
    return _CLASS_TO_EVAL7[_EV.class_to_string(_EV.get_rank_class(rank))]

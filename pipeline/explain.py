"""explain.py — Único punto donde interviene el LLM.

Recibe la matemática y la decisión correcta YA calculadas y solo redacta:
  - accion_previa (es/en)
  - desglose en 3 capas (es/en)
UNA llamada por escenario devuelve ambos idiomas.

Variables de entorno: ANTHROPIC_API_KEY, ANTHROPIC_MODEL (def: claude-haiku-4-5-20251001).
Modo offline (sin API, para pruebas): usa plantillas deterministas.
"""
from __future__ import annotations

import json
import os

SYSTEM = (
    "Eres un entrenador profesional de póker (GTO/ICM y teoría de Janda para cash). "
    "Recibes un escenario con la matemática y la jugada correcta YA calculadas: "
    "no las cuestiones ni inventes números; interpreta exactamente los que recibes. "
    "Redacta en español natural y pedagógico (prioridad) y su traducción fiel al inglés. "
    "Devuelve SOLO un JSON válido, sin markdown ni texto extra, con este esquema: "
    '{"accion_previa":{"es":"...","en":"..."},'
    '"desglose":{"es":{"matematica_rapida":"...","psicologia_y_rangos":"...",'
    '"control_y_conclusion":"..."},"en":{...mismas claves...}}}. '
    "Si modo=Torneo (push/fold): accion_previa describe que todos foldean hasta el héroe; "
    "matematica_rapida interpreta equity, pot odds y el umbral Nash; "
    "psicologia_y_rangos cubre el rango de pago del BB y la fold equity. "
    "Si modo=Cash Game (river): accion_previa describe el pozo al llegar al river y la "
    "apuesta del villano; matematica_rapida interpreta equity vs pot odds, la MDF y la "
    "ratio valor:farol de Janda (value_bluff_ratio) para ese tamaño de apuesta; "
    "psicologia_y_rangos describe cómo se compone el rango de apuesta del villano "
    "(n_value combos de valor, n_bluffs faroles). "
    "control_y_conclusion siempre: por qué la opción correcta supera a la otra y qué error "
    "conceptual comete quien elige mal. Cada capa: 2-3 frases."
)


def _payload(s: dict) -> str:
    m = s["_meta"]
    base = {
        "modo": s["modo"],
        "mano": m["hand"],
        "cartas": s["cartas_heroe"],
        "board": s["board"],
        "stack_bb": s["stack_bb"],
        "pozo_bb": s["pozo_bb"],
        "jugada_correcta": s["opciones"][s["opcion_correcta_index"]],
        "math": s["math"],
        "dificultad": s["dificultad"],
    }
    if s["modo"] == "Torneo":
        base |= {
            "posicion_heroe": m["pos_label"]["es"],
            "posicion_heroe_en": m["pos_label"]["en"],
            "jugadores_por_hablar": m["players_behind"],
            "umbral_nash_bb": m["threshold"],
        }
    else:  # Cash Game
        base |= {
            "posicion_villano": m["pos_label"]["es"],
            "posicion_villano_en": m["pos_label"]["en"],
            "apuesta_bb": m["bet_bb"],
            "pozo_antes_apuesta_bb": m["pot_before_bet_bb"],
            "fraccion_pozo": m["bet_fraction"],
            "composicion_rango": m["rango"],
        }
    return json.dumps(base, ensure_ascii=False)


# ------------------------------------------------------------------ online ---
def explain_llm(s: dict) -> dict:
    import anthropic  # import perezoso: solo si hay API
    client = anthropic.Anthropic()  # usa ANTHROPIC_API_KEY
    model = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
    msg = client.messages.create(
        model=model, max_tokens=1200, system=SYSTEM,
        messages=[{"role": "user", "content": _payload(s)}],
    )
    text = "".join(b.text for b in msg.content if b.type == "text").strip()
    if text.startswith("```"):
        text = text.strip("`\n")
        text = text[4:] if text.startswith("json") else text
    return json.loads(text)


# ----------------------------------------------------------------- offline ---
def explain_offline(s: dict) -> dict:
    """Plantillas deterministas para probar el pipeline sin API."""
    if s["modo"] == "Cash Game":
        return _offline_cash(s)
    m = s["_meta"]
    hand, stack, thr = m["hand"], s["stack_bb"], m["threshold"]
    eq = round(s["math"]["equity"] * 100, 1)
    po = round(s["math"]["pot_odds"] * 100, 1)
    push = s["opcion_correcta_index"] == 1
    pos_es, pos_en = m["pos_label"]["es"], m["pos_label"]["en"]

    ap_es = (f"Nivel con antes. Todos se retiran hasta ti en {pos_es} "
             f"con {stack} BB. La Ciega Grande te cubre.")
    ap_en = (f"Ante level. Everyone folds to you in the {pos_en} "
             f"with {stack} BB. The Big Blind covers you.")

    if push:
        mat_es = (f"Con {hand} y {stack} BB estás dentro del umbral Nash de "
                  f"{thr} BB: el All-In es correcto por equilibrio. Si te pagan, "
                  f"tu equidad es {eq}% y solo necesitas {po}% para ser rentable "
                  f"cuando entra el dinero.")
        mat_en = (f"With {hand} at {stack} BB you are inside the {thr} BB Nash "
                  f"threshold: jamming is correct by equilibrium. When called, "
                  f"your equity is {eq}% versus the {po}% you need once the "
                  f"money goes in.")
        con_es = ("El All-In combina fold equity inmediata con equidad "
                  "suficiente cuando te pagan. Quien foldea aquí sobrevalora "
                  "esperar 'una mano mejor' mientras las ciegas y antes "
                  "devoran su stack.")
        con_en = ("Jamming combines immediate fold equity with enough equity "
                  "when called. Folding here overvalues waiting for a better "
                  "hand while blinds and antes eat the stack.")
    else:
        mat_es = (f"{hand} queda fuera del umbral Nash "
                  f"({thr if thr else 'no empujable'} BB) con {stack} BB. "
                  f"Tu equidad al ser pagado sería {eq}%, insuficiente para "
                  f"justificar arriesgar todo el stack.")
        mat_en = (f"{hand} is outside its Nash threshold "
                  f"({thr if thr else 'never a jam'} BB) at {stack} BB. "
                  f"Your equity when called would be {eq}%, not enough to "
                  f"risk the whole stack.")
        con_es = ("Foldear preserva tus fichas para un spot con mejor mano o "
                  "más fold equity. Quien empuja aquí confunde 'stack corto' "
                  "con 'empujar cualquier cosa': el rango importa incluso "
                  "bajo presión.")
        con_en = ("Folding preserves chips for a spot with a better hand or "
                  "more fold equity. Jamming here confuses being short with "
                  "shoving anything: range still matters under pressure.")

    psi_es = (f"Con {m['players_behind']} jugador(es) por hablar, la Ciega "
              f"Grande solo paga un rango condensado de parejas y broadways; "
              f"todo lo demás foldea y te regala el pozo. Cuanto más corto tu "
              f"stack, más ancho te paga y menos fold equity tienes.")
    psi_en = (f"With {m['players_behind']} player(s) left to act, the Big "
              f"Blind only calls a condensed range of pairs and broadways; "
              f"everything else folds and gifts you the pot. The shorter your "
              f"stack, the wider you get called and the less fold equity you have.")

    return {
        "accion_previa": {"es": ap_es, "en": ap_en},
        "desglose": {
            "es": {"matematica_rapida": mat_es,
                   "psicologia_y_rangos": psi_es,
                   "control_y_conclusion": con_es},
            "en": {"matematica_rapida": mat_en,
                   "psicologia_y_rangos": psi_en,
                   "control_y_conclusion": con_en},
        },
    }


def _offline_cash(s: dict) -> dict:
    m = s["_meta"]
    hand = m["hand"]
    bet, pot = m["bet_bb"], m["pot_before_bet_bb"]
    frac = int(m["bet_fraction"] * 100)
    eq = round(s["math"]["equity"] * 100, 1)
    po = round(s["math"]["pot_odds"] * 100, 1)
    mdf_pct = round(s["math"]["mdf"] * 100, 1)
    vbr = round(s["math"]["value_bluff_ratio"] * 100, 1)
    nv, nb = m["rango"]["n_value"], m["rango"]["n_bluffs"]
    call = s["opcion_correcta_index"] == 1
    vpos_es, vpos_en = m["pos_label"]["es"], m["pos_label"]["en"]

    ap_es = (f"Cash 100 BB. Llegas al river con {pot} BB en el pozo. "
             f"El rival en {vpos_es} apuesta {bet} BB ({frac}% del pozo).")
    ap_en = (f"100 BB cash game. You reach the river with {pot} BB in the pot. "
             f"The {vpos_en} bets {bet} BB ({frac}% pot).")

    mat_es = (f"Pagar {bet} BB para ganar {pot + bet} BB exige {po}% de "
              f"equidad y tu {hand} tiene {eq}% contra el rango de apuesta. "
              f"La MDF ante este tamaño es {mdf_pct}% y la ratio de Janda "
              f"permite hasta {vbr}% de faroles inexplotables.")
    mat_en = (f"Calling {bet} BB to win {pot + bet} BB requires {po}% equity "
              f"and your {hand} has {eq}% against the betting range. "
              f"MDF versus this sizing is {mdf_pct}% and the Janda ratio "
              f"allows up to {vbr}% unexploitable bluffs.")

    psi_es = (f"El rango de apuesta del rival se compone de {nv} combos de "
              f"valor (doble pareja o mejor, o top pair fuerte) y {nb} "
              f"faroles naturales sin equidad de showdown. Tu mano solo gana "
              f"contra la porción de faroles y las manos de valor que superas.")
    psi_en = (f"The villain's betting range holds {nv} value combos (two pair "
              f"or better, or strong top pair) and {nb} natural bluffs with "
              f"no showdown value. Your hand only wins against the bluff "
              f"portion and the value hands you beat.")

    if call:
        con_es = (f"Con {eq}% de equidad frente a {po}% requerido, el call es "
                  f"rentable a largo plazo aunque pierdas esta mano concreta. "
                  f"Quien foldea aquí sobre-foldea contra un rango que aún "
                  f"contiene suficientes faroles.")
        con_en = (f"With {eq}% equity versus the {po}% required, calling is "
                  f"profitable long-term even if you lose this specific hand. "
                  f"Folding here over-folds against a range that still holds "
                  f"enough bluffs.")
    else:
        con_es = (f"Con {eq}% de equidad y {po}% requerido, cada call quema "
                  f"dinero: el rango de apuesta te supera demasiado a menudo. "
                  f"Quien paga aquí confunde 'podría ser un farol' con las "
                  f"odds reales que la apuesta le ofrece.")
        con_en = (f"With {eq}% equity against {po}% required, every call burns "
                  f"money: the betting range beats you too often. Calling here "
                  f"confuses 'it could be a bluff' with the actual odds the "
                  f"bet is laying.")

    return {
        "accion_previa": {"es": ap_es, "en": ap_en},
        "desglose": {
            "es": {"matematica_rapida": mat_es,
                   "psicologia_y_rangos": psi_es,
                   "control_y_conclusion": con_es},
            "en": {"matematica_rapida": mat_en,
                   "psicologia_y_rangos": psi_en,
                   "control_y_conclusion": con_en},
        },
    }


def explain(s: dict, offline: bool = False) -> dict:
    if offline or not os.environ.get("ANTHROPIC_API_KEY"):
        return explain_offline(s)
    try:
        return explain_llm(s)
    except Exception as e:  # red de seguridad: nunca romper el build
        print(f"  [warn] LLM falló en {s['id']} ({e}); uso plantilla offline")
        return explain_offline(s)

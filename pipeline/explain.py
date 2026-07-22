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
    "Si tipo=overcall (Torneo): el héroe está en la Ciega Grande y decide PAGAR o no un "
    "All-In rival; accion_previa describe el jam desde posicion_jammer y que folden hasta él; "
    "matematica_rapida interpreta equity vs pot odds para pagar a_pagar_bb (decisión chip-EV); "
    "psicologia_y_rangos explica que el rango de jam (combos_de_jam) se deriva de los umbrales Nash. "
    "Si tipo=river_3way (Cash): hay DOS rivales (agresor que apuesta y pagador que iguala en frío) "
    "y el héroe cierra; recalca que debe superar a ambos, por lo que la equidad baja frente a la "
    "unión de rango de apuesta y rango del pagador (rango_pagador). "
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
    tipo = s.get("tipo")
    if s["modo"] == "Torneo" and tipo == "overcall":
        base |= {
            "tipo": "overcall",
            "posicion_heroe": "Ciega Grande",
            "posicion_jammer": m["jam_pos_label"]["es"],
            "posicion_jammer_en": m["jam_pos_label"]["en"],
            "combos_de_jam": m["n_jam_combos"],
            "a_pagar_bb": m["to_call_bb"],
        }
    elif s["modo"] == "Torneo":
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
        if tipo == "river_3way":
            base |= {
                "tipo": "river_3way",
                "posicion_pagador": m["pos_label_pagador"]["es"],
                "posicion_pagador_en": m["pos_label_pagador"]["en"],
                "rango_pagador": m["rango_pagador"],
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
    if s.get("tipo") == "overcall":
        return _offline_overcall(s)
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


def _offline_overcall(s: dict) -> dict:
    """Plantilla determinista para el spot de overcall (pagar un jam)."""
    m = s["_meta"]
    hand, stack = m["hand"], s["stack_bb"]
    eq = round(s["math"]["equity"] * 100, 1)
    po = round(s["math"]["pot_odds"] * 100, 1)
    call = s["opcion_correcta_index"] == 1
    jpos_es, jpos_en = m["jam_pos_label"]["es"], m["jam_pos_label"]["en"]
    ncombos, to_call = m["n_jam_combos"], m["to_call_bb"]

    ap_es = (f"Nivel con antes. El rival en {jpos_es} va All-In por {stack} BB "
             f"y todos foldean hasta ti en la Ciega Grande. Debes pagar "
             f"{to_call} BB para ver el showdown.")
    ap_en = (f"Ante level. The {jpos_en} shoves All-In for {stack} BB and it "
             f"folds to you in the Big Blind. You must call {to_call} BB to "
             f"see the showdown.")

    mat_es = (f"Pagar {to_call} BB para disputar el bote exige {po}% de equidad "
              f"y tu {hand} tiene {eq}% frente al rango de jam del rival "
              f"(unos {ncombos} combos). Es una decisión de chip-EV pura: "
              f"comparas tu equidad con las probabilidades del bote.")
    mat_en = (f"Calling {to_call} BB to contest the pot needs {po}% equity and "
              f"your {hand} has {eq}% against the villain's jamming range "
              f"(about {ncombos} combos). It is a pure chip-EV call: your "
              f"equity versus the pot odds.")

    psi_es = (f"El rango de all-in desde {jpos_es} se deriva de los umbrales "
              f"Nash: cuanto más corto el stack, más ancho jamea y más manos "
              f"medias pagas rentablemente. A {stack} BB su rango sigue "
              f"conteniendo faroles y manos dominadas que subes de equidad.")
    psi_en = (f"The all-in range from {jpos_en} comes straight from the Nash "
              f"thresholds: the shorter the stack, the wider the shove and the "
              f"more medium hands you can profitably call. At {stack} BB that "
              f"range still holds bluffs and dominated hands you beat.")

    if call:
        con_es = (f"Con {eq}% de equidad frente a {po}% requerido, pagar es "
                  f"+EV a largo plazo aunque pierdas esta mano. Foldear aquí "
                  f"regala fold equity a un rango que jamea demasiado ancho.")
        con_en = (f"With {eq}% equity versus the {po}% required, calling is "
                  f"+EV long-term even if you lose this hand. Folding here "
                  f"rewards a range that jams far too wide.")
    else:
        con_es = (f"Con {eq}% de equidad y {po}% requerido, pagar quema fichas: "
                  f"el rango de jam te supera demasiado. Quien paga confunde "
                  f"'estoy en la ciega' con tener las odds para disputar el bote.")
        con_en = (f"With {eq}% equity against {po}% required, calling burns "
                  f"chips: the jamming range beats you too often. Calling here "
                  f"confuses 'I'm in the blind' with actually having the odds.")

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

    is_3way = s.get("tipo") == "river_3way"
    pag_es = pag_en = ""
    if is_3way:
        pag_es = m["pos_label_pagador"]["es"]
        pag_en = m["pos_label_pagador"]["en"]
        ncall = m["rango_pagador"]["n_call"]

    if is_3way:
        ap_es = (f"Cash 100 BB a 3 bandas. En el river el rival en {vpos_es} "
                 f"apuesta {bet} BB y el de {pag_es} iguala en frío; cierras tú "
                 f"desde la Ciega Grande.")
        ap_en = (f"3-way 100 BB cash game. On the river the {vpos_en} bets "
                 f"{bet} BB and the {pag_en} cold-calls; you close the action "
                 f"from the Big Blind.")
    else:
        ap_es = (f"Cash 100 BB. Llegas al river con {pot} BB en el pozo. "
                 f"El rival en {vpos_es} apuesta {bet} BB ({frac}% del pozo).")
        ap_en = (f"100 BB cash game. You reach the river with {pot} BB in the "
                 f"pot. The {vpos_en} bets {bet} BB ({frac}% pot).")

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
    if is_3way:
        psi_es += (f" Además, el pagador en {pag_es} entra con ~{ncall} combos "
                   f"de una pareja hecha: al ser 3 bandas necesitas superar a "
                   f"AMBOS rivales para llevarte el bote, así que tu equidad "
                   f"real baja frente a la suma de los dos rangos.")
        psi_en += (f" On top of that, the {pag_en} cold-caller shows up with "
                   f"~{ncall} one-pair combos: three-way you must beat BOTH "
                   f"opponents to win, so your real equity drops against the "
                   f"union of the two ranges.")

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

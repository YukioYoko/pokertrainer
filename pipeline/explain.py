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

    if call:
        psi_es = (f"El rango de all-in desde {jpos_es} se deriva de los umbrales "
                  f"Nash. A {stack} BB es lo bastante ancho (parejas medias, Ax "
                  f"y manos peores que la tuya) para que tu equidad alcance el "
                  f"precio: cuanto más corto el stack, más rentable es pagar.")
        psi_en = (f"The all-in range from {jpos_en} comes from the Nash "
                  f"thresholds. At {stack} BB it is wide enough (medium pairs, "
                  f"Ax and hands worse than yours) for your equity to meet the "
                  f"price: the shorter the stack, the more profitable the call.")
    else:
        psi_es = (f"El rango de all-in desde {jpos_es} a {stack} BB, aunque "
                  f"incluya alguna mano peor, en conjunto te supera: hay "
                  f"demasiadas parejas y ases que te dominan. Por eso tu "
                  f"equidad no llega al precio y estar en la ciega no obliga a pagar.")
        psi_en = (f"The all-in range from {jpos_en} at {stack} BB, even if it "
                  f"holds a few worse hands, beats you overall: too many pairs "
                  f"and aces dominate you. That is why your equity falls short "
                  f"and being in the blind does not force a call.")

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

    if nb > 0:
        psi_es = (f"El rango de apuesta del rival son {nv} combos de valor "
                  f"(doble pareja o mejor, o top pair fuerte) y {nb} faroles "
                  f"sin equidad de showdown. Ganas contra esos faroles y contra "
                  f"las manos de valor que superas; el resto te tiene batido.")
        psi_en = (f"The villain's betting range is {nv} value combos (two pair "
                  f"or better, or strong top pair) and {nb} bluffs with no "
                  f"showdown value. You win against those bluffs and the value "
                  f"hands you beat; the rest has you beaten.")
    else:
        psi_es = (f"En este board el rival no tiene faroles naturales: su "
                  f"apuesta son {nv} combos de puro valor, así que casi solo "
                  f"ganas cuando tu mano supera a manos de valor concretas. Por "
                  f"eso el rango te bate tan a menudo.")
        psi_en = (f"On this board the villain has no natural bluffs: the bet is "
                  f"{nv} pure-value combos, so you mostly win only when your "
                  f"hand beats specific value holdings. That is why the range "
                  f"has you beaten so often.")
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


def _offline_hand(s: dict) -> dict:
    """Repaso paso a paso determinista de una mano completa (flop→turn→river).

    Devuelve `contexto` (introducción), `calles` (cada nodo con su `explicacion`
    es/en) y `resumen` (veredicto global). No usa LLM: multi-nodo, siempre
    disponible y coherente con la matemática ya calculada por hand_generator.
    """
    m = s["_meta"]
    hand = m["hand"]
    vpos_es, vpos_en = m["pos_label"]["es"], m["pos_label"]["en"]

    ctx_es = (f"Defiendes la Ciega Grande con {hand} frente a un open del "
              f"{vpos_es}, mano a mano y 100 BB. Juegas flop, turn y river: en "
              f"cada calle decides Call o Fold. Al terminar repasamos cada "
              f"decisión comparando tu equidad con las pot odds.")
    ctx_en = (f"You defend the Big Blind with {hand} against a {vpos_en} open, "
              f"heads-up and 100 BB deep. You play flop, turn and river: each "
              f"street you choose Call or Fold. Afterwards we review every "
              f"decision comparing your equity to the pot odds.")

    calles_out = []
    for nd in s["calles"]:
        eq = round(nd["math"]["equity"] * 100, 1)
        pot = nd["pozo_previo_bb"]
        calle = nd["calle"]
        if nd.get("villano_pasa"):
            bet = nd["apuesta_heroe_bb"]
            eva = nd["math"]["ev_apostar"]
            evp = nd["math"]["ev_pasar"]
            bet_ok = nd["opcion_correcta_index"] == 2
            ex_es = (f"{calle}: el villano PASA y capa su rango (deja fuera sus "
                     f"manos fuertes). Tu equidad frente a ese rango es {eq}%. "
                     f"Apostar {bet} BB rinde {eva} BB y pasar {evp} BB, así que "
                     f"lo correcto es {'apostar por valor' if bet_ok else 'pasar y ver un showdown gratis'}. "
                     f"Foldear jamás: pasar no cuesta nada.")
            ex_en = (f"{calle}: villain CHECKS, capping their range (no strong "
                     f"hands left). Your equity vs that range is {eq}%. Betting "
                     f"{bet} BB yields {eva} BB and checking {evp} BB, so the "
                     f"right play is {'a value bet' if bet_ok else 'to check back and take a free showdown'}. "
                     f"Never fold: checking is free.")
        else:
            po = round(nd["math"]["pot_odds"] * 100, 1)
            bet = nd["villano_apuesta_bb"]
            nv = nd["_rango"]["n_value"]
            nb = nd["_rango"]["n_bluffs"]
            call = nd["opcion_correcta_index"] == 1
            veredicto_es = ("pagar es correcto: tienes el precio"
                            if call else "lo correcto es foldear: no tienes precio")
            veredicto_en = ("calling is correct: you have the price"
                            if call else "folding is correct: you lack the price")
            ex_es = (f"{calle}: el villano apuesta {bet} BB a un pozo de {pot} BB, "
                     f"así que necesitas {po}% de equidad y tienes {eq}% frente a "
                     f"su rango ({nv} manos de valor, {nb} faroles). Por eso "
                     f"{veredicto_es}.")
            ex_en = (f"{calle}: villain bets {bet} BB into a {pot} BB pot, so you "
                     f"need {po}% equity and you have {eq}% against their range "
                     f"({nv} value hands, {nb} bluffs). That is why {veredicto_en}.")
        clean = {k: v for k, v in nd.items() if k != "_rango"}
        clean["explicacion"] = {"es": ex_es, "en": ex_en}
        calles_out.append(clean)

    n_call = sum(1 for nd in s["calles"]
                 if not nd.get("villano_pasa") and nd["opcion_correcta_index"] == 1)
    n_fold = sum(1 for nd in s["calles"]
                 if not nd.get("villano_pasa") and nd["opcion_correcta_index"] == 0)
    res_es = (f"En esta mano la línea correcta era pagar {n_call} calle(s) y "
              f"foldear {n_fold}. La clave en cada punto es la misma: ¿tu "
              f"equidad supera las pot odds que te ofrece la apuesta? Si en "
              f"alguna calle pagaste sin precio, ahí se fuga tu EV.")
    res_en = (f"In this hand the correct line was to call {n_call} street(s) "
              f"and fold {n_fold}. The key at every point is the same: does "
              f"your equity beat the pot odds the bet lays? Any street you "
              f"called without the price is where your EV leaks.")

    return {
        "contexto": {"es": ctx_es, "en": ctx_en},
        "calles": calles_out,
        "resumen": {"es": res_es, "en": res_en},
    }


def _offline_outs(s: dict) -> dict:
    """Explicación determinista del cálculo de outs (accion_previa + explicacion).
    No usa las 3 capas del desglose: es un ejercicio de probabilidad puntual."""
    m = s["_meta"]
    hand = m["hand"]
    draw_es = m["draw_name"]["es"]
    draw_en = m["draw_name"]["en"]
    outs = s["math"]["outs"]
    prob = round(s["math"]["prob"] * 100, 1)
    tc = s["math"]["cartas_por_venir"]
    regla = s["math"]["regla_pulgar"]
    calle_es = "flop" if tc == 2 else "turn"
    calle_en = "flop" if tc == 2 else "turn"
    factor = 4 if tc == 2 else 2

    ap_es = (f"Tienes {hand} y vas a {draw_es}. Con el board actual en el "
             f"{calle_es}, ¿qué probabilidad tienes de ligar tu proyecto de "
             f"aquí al river?")
    ap_en = (f"You hold {hand} drawing to a {draw_en}. With the current "
             f"{calle_en} board, what is your chance to complete it by the "
             f"river?")

    ex_es = (f"Tienes {outs} outs (cartas que te dan {draw_es}). Con {tc} "
             f"carta(s) por venir, la probabilidad exacta de ligar al menos "
             f"uno es {prob}%. Regla rápida: outs × {factor} = {regla}%, muy "
             f"cerca del valor real — úsala en la mesa para estimar al vuelo.")
    ex_en = (f"You have {outs} outs (cards that make your {draw_en}). With {tc} "
             f"card(s) to come, the exact chance to hit at least one is {prob}%. "
             f"Quick rule: outs × {factor} = {regla}%, very close to the real "
             f"number — use it at the table to estimate on the fly.")

    return {
        "accion_previa": {"es": ap_es, "en": ap_en},
        "explicacion": {"es": ex_es, "en": ex_en},
    }


def explain(s: dict, offline: bool = False) -> dict:
    if s.get("tipo") == "outs":
        return _offline_outs(s)        # ejercicio de probabilidad (sin LLM)
    if s.get("tipo") == "hand_full":
        return _offline_hand(s)        # multi-nodo determinista (sin LLM)
    if offline or not os.environ.get("ANTHROPIC_API_KEY"):
        return explain_offline(s)
    try:
        return explain_llm(s)
    except Exception as e:  # red de seguridad: nunca romper el build
        print(f"  [warn] LLM falló en {s['id']} ({e}); uso plantilla offline")
        return explain_offline(s)

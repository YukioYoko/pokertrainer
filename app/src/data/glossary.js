/**
 * Glosario de tecnicismos usados en las explicaciones (desglose) de los escenarios.
 * Bilingüe (es/en), igual que la prosa de los escenarios. Orden = orden de aparición
 * pedagógico, no alfabético. `term` es el encabezado; se muestra igual en ambos idiomas
 * salvo que se traduzca en `label`.
 */
export default [
  {
    id: 'push-fold',
    label: { es: 'Push / Fold', en: 'Push / Fold' },
    def: {
      es: 'Estrategia de stack corto donde solo hay dos decisiones antes del flop: ir All-In (push) o retirarse (fold). No se contemplan subidas parciales porque con pocas ciegas dejan de tener sentido.',
      en: 'Short-stack strategy where the only pre-flop choices are shoving All-In (push) or folding. Partial raises are dropped because with few blinds they stop making sense.'
    }
  },
  {
    id: 'all-in',
    label: { es: 'All-In', en: 'All-In' },
    def: {
      es: 'Apostar todas tus fichas en una sola jugada.',
      en: 'Betting all of your chips in a single move.'
    }
  },
  {
    id: 'fold',
    label: { es: 'Fold (retirarse)', en: 'Fold' },
    def: {
      es: 'Abandonar la mano y renunciar a lo que ya hubieras puesto en el pozo.',
      en: 'Giving up the hand and forfeiting whatever you already put in the pot.'
    }
  },
  {
    id: 'call',
    label: { es: 'Call (igualar)', en: 'Call' },
    def: {
      es: 'Igualar la apuesta del rival para seguir en la mano sin subirla.',
      en: 'Matching the opponent’s bet to stay in the hand without raising.'
    }
  },
  {
    id: 'bb',
    label: { es: 'BB (Big Blind / Ciega Grande)', en: 'BB (Big Blind)' },
    def: {
      es: 'La ciega grande. Se usa como unidad de medida: un stack de "10 BB" son diez veces la apuesta obligatoria mayor. Ojo: "BB" también nombra la posición del jugador que la paga.',
      en: 'The big blind. Used as a unit: a "10 BB" stack is ten times the larger forced bet. Note: "BB" also names the seat of the player who posts it.'
    }
  },
  {
    id: 'stack',
    label: { es: 'Stack', en: 'Stack' },
    def: {
      es: 'La cantidad de fichas que tienes disponibles, casi siempre expresada en BB.',
      en: 'The amount of chips you have available, almost always expressed in BB.'
    }
  },
  {
    id: 'pozo',
    label: { es: 'Pozo (Pot)', en: 'Pot' },
    def: {
      es: 'El total de fichas apostadas que se lleva el ganador de la mano.',
      en: 'The total of bet chips that the winner of the hand takes.'
    }
  },
  {
    id: 'posiciones',
    label: { es: 'Posiciones (SB, BB, BTN, CO, HJ)', en: 'Positions (SB, BB, BTN, CO, HJ)' },
    def: {
      es: 'El asiento respecto al repartidor: SB=Ciega Pequeña, BB=Ciega Grande, BTN=Botón (repartidor), CO=Cutoff (a su derecha), HJ=Hijack (dos a su derecha). Cuanto más tarde actúas, más fuerte tiene que ser tu rango.',
      en: 'The seat relative to the dealer: SB=Small Blind, BB=Big Blind, BTN=Button (dealer), CO=Cutoff (to its right), HJ=Hijack (two to its right). The later you act, the wider you can play.'
    }
  },
  {
    id: 'equity',
    label: { es: 'Equidad (Equity)', en: 'Equity' },
    def: {
      es: 'Tu probabilidad de ganar la mano si llega al showdown, en porcentaje. Si tienes 60% de equidad, en promedio ganas 6 de cada 10 veces contra ese rango.',
      en: 'Your probability of winning the hand at showdown, as a percentage. With 60% equity you win 6 out of 10 times on average against that range.'
    }
  },
  {
    id: 'pot-odds',
    label: { es: 'Pot odds (probabilidades del pozo)', en: 'Pot odds' },
    def: {
      es: 'La equidad mínima que necesitas para que pagar sea rentable. Se calcula como apuesta / (pozo + apuesta). Regla de oro del entrenador: si tu equidad ≥ pot odds, pagar es +EV.',
      en: 'The minimum equity you need for a call to be profitable. Computed as bet / (pot + bet). Trainer’s golden rule: if your equity ≥ pot odds, calling is +EV.'
    }
  },
  {
    id: 'ev',
    label: { es: 'EV (Valor Esperado)', en: 'EV (Expected Value)' },
    def: {
      es: 'Cuánto ganas o pierdes en promedio con una decisión si la repitieras infinitas veces. "+EV" es rentable a largo plazo; "−EV" (o EV−) es un error táctico aunque esa vez ganes.',
      en: 'How much a decision wins or loses on average over infinite repetitions. "+EV" is profitable long-term; "−EV" (or EV−) is a tactical mistake even if you win that time.'
    }
  },
  {
    id: 'rango',
    label: { es: 'Rango (Range)', en: 'Range' },
    def: {
      es: 'El conjunto de todas las manos posibles que un jugador podría tener en una situación dada. No razonamos contra una mano concreta del rival, sino contra su rango entero.',
      en: 'The set of all possible hands a player could hold in a given spot. We don’t reason against one specific hand, but against the opponent’s whole range.'
    }
  },
  {
    id: 'nash',
    label: { es: 'Equilibrio de Nash', en: 'Nash equilibrium' },
    def: {
      es: 'La estrategia push/fold matemáticamente inexplotable: ninguno de los dos jugadores puede mejorar su EV cambiando su rango unilateralmente. Es la fuente de la respuesta correcta en modo Torneo.',
      en: 'The mathematically unexploitable push/fold strategy: neither player can improve their EV by changing their range unilaterally. It’s the source of the correct answer in Tournament mode.'
    }
  },
  {
    id: 'value-bluff',
    label: { es: 'Valor y farol (Value / Bluff)', en: 'Value / Bluff' },
    def: {
      es: 'Una apuesta de valor busca que te pague una mano peor; un farol (bluff) busca que una mano mejor se retire. Un rango equilibrado mezcla ambas en cierta proporción.',
      en: 'A value bet wants a worse hand to call; a bluff wants a better hand to fold. A balanced range mixes both in a certain ratio.'
    }
  },
  {
    id: 'mdf',
    label: { es: 'MDF (Frecuencia Mínima de Defensa)', en: 'MDF (Minimum Defense Frequency)' },
    def: {
      es: 'El porcentaje del rango que debes defender (pagar/subir) frente a una apuesta para no ser explotado por faroles. Depende solo del tamaño de la apuesta relativo al pozo.',
      en: 'The share of your range you must defend (call/raise) against a bet so you can’t be exploited by bluffs. It depends only on the bet size relative to the pot.'
    }
  },
  {
    id: 'spr',
    label: { es: 'SPR (Stack-to-Pot Ratio)', en: 'SPR (Stack-to-Pot Ratio)' },
    def: {
      es: 'El stack efectivo dividido entre el pozo. Un SPR bajo empuja a jugadas de todo-o-nada; un SPR alto deja margen para maniobrar en calles posteriores.',
      en: 'The effective stack divided by the pot. A low SPR pushes toward all-or-nothing plays; a high SPR leaves room to maneuver on later streets.'
    }
  },
  {
    id: 'river',
    label: { es: 'River (calle final)', en: 'River' },
    def: {
      es: 'La quinta y última carta comunitaria. Ya no quedan cartas por venir, así que la equidad es exacta: ganas, pierdes o empatas.',
      en: 'The fifth and final community card. No more cards are coming, so equity is exact: you win, lose or tie.'
    }
  },
  {
    id: 'board',
    label: { es: 'Board (cartas comunitarias)', en: 'Board' },
    def: {
      es: 'Las cartas que están sobre la mesa y todos comparten para formar su mejor mano de cinco.',
      en: 'The face-up cards on the table that everyone shares to make their best five-card hand.'
    }
  },
  {
    id: 'showdown',
    label: { es: 'Showdown', en: 'Showdown' },
    def: {
      es: 'El momento en que los jugadores restantes muestran sus cartas y se decide quién gana el pozo.',
      en: 'The moment the remaining players reveal their cards and the pot is awarded.'
    }
  },
  {
    id: 'heroe-villano',
    label: { es: 'Héroe / Villano', en: 'Hero / Villain' },
    def: {
      es: 'Convención de análisis: el "héroe" eres tú (quien toma la decisión) y el "villano" es el rival cuyo rango enfrentas.',
      en: 'Analysis convention: the "hero" is you (the decision-maker) and the "villain" is the opponent whose range you face.'
    }
  }
]

<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import PokerTable from './PokerTable.vue'
import EquityBar from './EquityBar.vue'
import { progress, record } from '../stores/progress.js'

const props = defineProps({ scenarios: Array })
defineEmits(['exit'])

const { locale } = useI18n()
const SESSION = 5

const order = ref(buildSession())
const handIdx = ref(0)
const streetIdx = ref(0)
const picks = ref([])              // índices elegidos en la mano actual
const phase = ref('play')          // 'play' | 'review' | 'done'
const sessionScore = ref([])       // por mano: { ok, total } decisiones jugadas

const hasHands = computed(() => order.value.length > 0)
const hand = computed(() => props.scenarios[order.value[handIdx.value]])
const calle = computed(() => hand.value.calles[streetIdx.value])
const loc = computed(() => (locale.value === 'en' ? 'en' : 'es'))

// Calles efectivamente jugadas (si el héroe foldea, la mano termina ahí).
const playedCalles = computed(() =>
  hand.value.calles.slice(0, picks.value.length))
// Foldeó antes del river → la mano se cortó; no mostramos el resumen global.
const foldedEarly = computed(() =>
  picks.value.length < hand.value.calles.length)

// Vista de mesa por calle: board parcial + pozo previo a la apuesta.
const viewScenario = computed(() => ({
  ...hand.value,
  board: calle.value.board,
  pozo_bb: calle.value.pozo_previo_bb
}))

function shuffle (arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]]
  }
  return arr
}
function buildSession () {
  const keys = [...props.scenarios.keys()]
  const isSeen = (i) => props.scenarios[i].id in progress.answered
  const unseen = shuffle(keys.filter(i => !isSeen(i)))
  const seen = shuffle(keys.filter(isSeen))
  return [...unseen, ...seen].slice(0, SESSION)
}

async function choose (i) {
  picks.value.push(i)
  const folded = i === 0                                   // 0 = Fold
  const lastStreet = streetIdx.value + 1 >= hand.value.calles.length
  if (folded || lastStreet) {
    // Foldear corta la mano aquí; un Call en el river también la termina.
    // El repaso y el score cuentan solo las calles jugadas.
    const played = picks.value.length
    const ok = hand.value.calles.slice(0, played)
      .filter((nd, k) => picks.value[k] === nd.opcion_correcta_index).length
    sessionScore.value.push({ ok, total: played })
    await record(hand.value, ok === played)   // bien jugada = todo lo jugado correcto
    phase.value = 'review'
  } else {
    streetIdx.value++
  }
}

function nextHand () {
  if (handIdx.value + 1 >= order.value.length) { phase.value = 'done'; return }
  handIdx.value++
  streetIdx.value = 0
  picks.value = []
  phase.value = 'play'
}

function restart () {
  order.value = buildSession()
  handIdx.value = 0
  streetIdx.value = 0
  picks.value = []
  sessionScore.value = []
  phase.value = 'play'
}

// Resumen final: sobre las decisiones realmente tomadas (no siempre 3 por mano).
const okStreetsTotal = computed(() =>
  sessionScore.value.reduce((a, s) => a + s.ok, 0))
const totalStreets = computed(() =>
  sessionScore.value.reduce((a, s) => a + s.total, 0))
const accuracy = computed(() => totalStreets.value
  ? Math.round((okStreetsTotal.value / totalStreets.value) * 100) : 0)
</script>

<template>
  <!-- Estado vacío: aún no hay manos de este modo en la base -->
  <section v-if="!hasHands" class="flex-1 flex flex-col items-center justify-center px-5 pb-8 text-center gap-5">
    <p class="text-5xl">🎬</p>
    <p class="text-naipe/70 max-w-xs leading-relaxed">{{ $t('manoCompleta.vacio') }}</p>
    <button
      class="px-5 py-3 rounded-xl border border-felt-600 text-naipe/80 hover:border-naipe/40
             focus-visible:outline focus-visible:outline-2 focus-visible:outline-ambar"
      @click="$emit('exit')"
    >{{ $t('resumen.volver') }}</button>
  </section>

  <!-- Resumen de sesión -->
  <section v-else-if="phase === 'done'" class="flex-1 flex flex-col items-center justify-center px-5 pb-8 text-center">
    <h2 class="text-2xl font-semibold">{{ $t('resumen.titulo') }}</h2>
    <p class="font-num text-5xl mt-4 text-ambar">{{ accuracy }}%</p>
    <p class="text-sm text-naipe/50 mt-2">
      {{ $t('manoCompleta.decisiones', { ok: okStreetsTotal, total: totalStreets }) }}
    </p>
    <div class="flex gap-3 mt-10">
      <button
        class="px-5 py-3 rounded-xl border border-felt-600 text-naipe/80 hover:border-naipe/40
               focus-visible:outline focus-visible:outline-2 focus-visible:outline-ambar"
        @click="$emit('exit')"
      >{{ $t('resumen.volver') }}</button>
      <button
        class="px-5 py-3 rounded-xl bg-ambar text-felt-950 font-semibold hover:brightness-110
               focus-visible:outline focus-visible:outline-2 focus-visible:outline-naipe"
        @click="restart"
      >{{ $t('resumen.otra') }}</button>
    </div>
  </section>

  <!-- Juego + repaso -->
  <section v-else class="flex-1 flex flex-col px-4 pb-6 max-w-md w-full mx-auto">
    <div class="flex items-center justify-between text-sm text-naipe/50">
      <button
        class="underline-offset-2 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-ambar rounded"
        @click="$emit('exit')"
      >← {{ $t('gimnasio.salir') }}</button>
      <span class="font-num">{{ $t('manoCompleta.mano', { actual: handIdx + 1, total: order.length }) }}</span>
      <span class="text-xs px-2 py-0.5 rounded-full border border-felt-600">
        {{ $t('dificultad.' + hand.dificultad) }}
      </span>
    </div>

    <!-- FASE JUEGO -->
    <template v-if="phase === 'play'">
      <!-- Indicador de calles -->
      <div class="flex items-center gap-1.5 mt-3">
        <span
          v-for="(nd, k) in hand.calles" :key="k"
          class="h-1.5 flex-1 rounded-full"
          :class="k < streetIdx ? 'bg-ambar' : k === streetIdx ? 'bg-naipe/60' : 'bg-felt-700'"
        />
      </div>

      <p v-if="streetIdx === 0" class="mt-4 text-sm leading-relaxed text-naipe/70 bg-felt-800 border border-felt-700 rounded-xl px-4 py-3">
        {{ hand.contexto[loc] }}
      </p>

      <div class="mt-4">
        <PokerTable :scenario="viewScenario" />
      </div>

      <p class="mt-5 text-center">
        <span class="text-xs uppercase tracking-wider text-naipe/40 block">{{ calle.calle }}</span>
        <span class="text-naipe/90">
          {{ $t('manoCompleta.apuesta', { pos: $t('posicion.' + hand.posicion_villano), bet: calle.villano_apuesta_bb }) }}
        </span>
      </p>

      <div class="mt-auto pt-5 grid grid-cols-2 gap-3">
        <button
          v-for="(op, i) in calle.opciones" :key="op"
          class="py-4 rounded-2xl text-lg font-semibold transition-colors
                 focus-visible:outline focus-visible:outline-2 focus-visible:outline-naipe"
          :class="i === 1
            ? 'bg-ambar text-felt-950 hover:brightness-110'
            : 'bg-felt-700 border border-felt-600 hover:bg-felt-600'"
          @click="choose(i)"
        >{{ op }}</button>
      </div>
    </template>

    <!-- FASE REPASO (paso a paso) -->
    <template v-else>
      <h3 class="mt-5 text-lg font-semibold text-ambar">{{ $t('manoCompleta.repaso') }}</h3>

      <div class="mt-3 space-y-3 overflow-y-auto">
        <div
          v-for="(nd, k) in playedCalles" :key="k"
          class="rounded-2xl border p-4"
          :class="picks[k] === nd.opcion_correcta_index
            ? 'border-gana/40 bg-gana/5' : 'border-pierde/40 bg-pierde/5'"
        >
          <div class="flex items-center justify-between">
            <span class="text-xs uppercase tracking-wider text-naipe/50">{{ nd.calle }}</span>
            <span
              class="text-sm font-semibold"
              :class="picks[k] === nd.opcion_correcta_index ? 'text-gana' : 'text-pierde'"
            >
              {{ picks[k] === nd.opcion_correcta_index ? '✓' : '✗' }}
              {{ nd.opciones[picks[k]] }}
              <span v-if="picks[k] !== nd.opcion_correcta_index" class="text-naipe/50 font-normal">
                → {{ nd.opciones[nd.opcion_correcta_index] }}
              </span>
            </span>
          </div>
          <div class="mt-3">
            <EquityBar :equity="nd.math.equity" :pot-odds="nd.math.pot_odds" />
          </div>
          <p class="mt-3 text-sm text-naipe/80 leading-relaxed">{{ nd.explicacion[loc] }}</p>
        </div>

        <!-- Nota de retirada si la mano se cortó antes del river -->
        <p v-if="foldedEarly" class="text-sm text-ambar/90 leading-relaxed bg-felt-800 border border-ambar-dim rounded-xl px-4 py-3">
          {{ $t('manoCompleta.terminada', { calle: playedCalles[playedCalles.length - 1].calle }) }}
        </p>
        <!-- Resumen global solo si se jugó la mano entera (llegó al river) -->
        <p v-else class="text-sm text-naipe/60 leading-relaxed bg-felt-800 border border-felt-700 rounded-xl px-4 py-3">
          {{ hand.resumen[loc] }}
        </p>
      </div>

      <button
        class="mt-4 w-full py-3.5 rounded-2xl bg-ambar text-felt-950 text-lg font-semibold
               hover:brightness-110 focus-visible:outline focus-visible:outline-2 focus-visible:outline-naipe"
        @click="nextHand"
      >{{ handIdx + 1 >= order.length ? $t('whycard.verResumen') : $t('manoCompleta.siguienteMano') }}</button>
    </template>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import PokerTable from './PokerTable.vue'
import WhyCard from './WhyCard.vue'
import { progress, record } from '../stores/progress.js'

const props = defineProps({ scenarios: Array })
defineEmits(['exit'])

const { locale } = useI18n()
const SESSION = 10

// Sesión aleatoria que prioriza manos NO jugadas: solo repite las ya
// vistas cuando se agotan las nuevas, para que no se repitan entre sesiones.
const order = ref(buildSession())
const idx = ref(0)
const picked = ref(null)          // índice de opción elegida, null = sin responder
const results = ref([])           // booleans de la sesión
const finished = ref(false)

const scenario = computed(() => props.scenarios[order.value[idx.value]])
const isCorrect = computed(() =>
  picked.value !== null && picked.value === scenario.value.opcion_correcta_index)

// Estado de cada mano de la sesión para la barra de progreso segmentada.
const dots = computed(() => order.value.map((_, i) => {
  if (i < results.value.length) return results.value[i] ? 'ok' : 'fail'
  if (i === idx.value) return 'current'
  return 'pending'
}))
const scoreOk = computed(() => results.value.filter(Boolean).length)

// Anillo de precisión del resumen (estilo chess.com).
const RING_C = 2 * Math.PI * 52
const accuracy = computed(() => results.value.length
  ? Math.round((scoreOk.value / results.value.length) * 100) : 0)
const tier = computed(() => {
  const a = accuracy.value
  return a >= 90 ? 'excelente' : a >= 70 ? 'bien'
    : a >= 40 ? 'sigue' : 'repasa'
})
// Clases literales completas (Tailwind no detecta clases concatenadas).
const RING = {
  gana: { stroke: 'stroke-gana', text: 'text-gana' },
  ambar: { stroke: 'stroke-ambar', text: 'text-ambar' },
  pierde: { stroke: 'stroke-pierde', text: 'text-pierde' }
}
const ringCls = computed(() => RING[
  accuracy.value >= 70 ? 'gana' : accuracy.value >= 40 ? 'ambar' : 'pierde'])

function shuffle (arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]]
  }
  return arr
}

// Construye la sesión: primero manos sin responder (barajadas), y si no
// llegan a SESSION, completa con las ya jugadas (también barajadas). Así
// cada sesión es distinta y no repite hasta haber agotado el banco de manos.
function buildSession () {
  const keys = [...props.scenarios.keys()]
  const isSeen = (i) => props.scenarios[i].id in progress.answered
  const unseen = shuffle(keys.filter(i => !isSeen(i)))
  const seen = shuffle(keys.filter(isSeen))
  return [...unseen, ...seen].slice(0, SESSION)
}

async function choose (i) {
  if (picked.value !== null) return
  picked.value = i
  const ok = i === scenario.value.opcion_correcta_index
  results.value.push(ok)
  await record(scenario.value, ok)
}

function next () {
  if (idx.value + 1 >= order.value.length) { finished.value = true; return }
  idx.value++
  picked.value = null
}

function restart () {
  order.value = buildSession()
  idx.value = 0
  picked.value = null
  results.value = []
  finished.value = false
}
</script>

<template>
  <!-- Resumen de sesión -->
  <section v-if="finished" class="flex-1 flex flex-col items-center justify-center px-5 pb-8 text-center">
    <h2 class="text-2xl font-semibold">{{ $t('resumen.titulo') }}</h2>

    <!-- Anillo de precisión -->
    <div class="relative w-40 h-40 mt-6">
      <svg viewBox="0 0 120 120" class="w-full h-full -rotate-90">
        <circle cx="60" cy="60" r="52" fill="none" stroke-width="10" class="stroke-felt-700" />
        <circle
          cx="60" cy="60" r="52" fill="none" stroke-width="10" stroke-linecap="round"
          class="transition-all duration-700"
          :class="ringCls.stroke"
          :stroke-dasharray="RING_C"
          :stroke-dashoffset="RING_C * (1 - accuracy / 100)"
        />
      </svg>
      <div class="absolute inset-0 flex flex-col items-center justify-center">
        <span class="font-num text-4xl" :class="ringCls.text">{{ accuracy }}%</span>
        <span class="font-num text-xs text-naipe/50 mt-0.5">{{ scoreOk }}/{{ results.length }}</span>
      </div>
    </div>

    <p class="text-lg font-semibold mt-5" :class="ringCls.text">
      {{ $t('resumen.nivel.' + tier) }}
    </p>
    <p class="text-sm text-naipe/50 mt-1">
      {{ $t('resumen.aciertos', { ok: scoreOk, total: results.length }) }}
    </p>

    <div class="flex gap-3 mt-8">
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

  <!-- Gimnasio -->
  <section v-else class="flex-1 flex flex-col px-4 pb-6 max-w-md w-full mx-auto">
    <div class="flex items-center justify-between text-sm text-naipe/50">
      <button
        class="underline-offset-2 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-ambar rounded"
        @click="$emit('exit')"
      >← {{ $t('gimnasio.salir') }}</button>
      <span class="font-num text-gana/90">✓ {{ scoreOk }}</span>
      <span class="text-xs px-2 py-0.5 rounded-full border border-felt-600">
        {{ $t('dificultad.' + scenario.dificultad) }}
      </span>
    </div>

    <!-- Progreso de la sesión (estilo puzzle) -->
    <div class="flex items-center gap-1 mt-3">
      <span
        v-for="(d, i) in dots" :key="i"
        class="h-2 flex-1 rounded-full transition-colors duration-300"
        :class="{
          'bg-gana': d === 'ok',
          'bg-pierde': d === 'fail',
          'bg-ambar': d === 'current',
          'bg-felt-700': d === 'pending'
        }"
      />
    </div>
    <p class="text-center text-xs text-naipe/40 font-num mt-1.5">
      {{ $t('gimnasio.mano', { actual: idx + 1, total: order.length }) }}
    </p>

    <div class="mt-4" :class="{ 'opacity-40 pointer-events-none': picked !== null }">
      <PokerTable :scenario="scenario" />
    </div>

    <!-- Acción previa -->
    <p class="mt-5 text-sm leading-relaxed text-naipe/80 bg-felt-800 border border-felt-700 rounded-xl px-4 py-3">
      {{ scenario.accion_previa[locale] || scenario.accion_previa.es }}
    </p>

    <!-- Decisión -->
    <div class="mt-auto pt-5 grid grid-cols-2 gap-3">
      <button
        v-for="(op, i) in scenario.opciones" :key="op"
        class="py-4 rounded-2xl text-lg font-semibold transition-colors
               focus-visible:outline focus-visible:outline-2 focus-visible:outline-naipe"
        :class="i === 1
          ? 'bg-ambar text-felt-950 hover:brightness-110'
          : 'bg-felt-700 border border-felt-600 hover:bg-felt-600'"
        :disabled="picked !== null"
        @click="choose(i)"
      >{{ op }}</button>
    </div>

    <!-- Why Card -->
    <WhyCard
      v-if="picked !== null"
      :scenario="scenario"
      :correct="isCorrect"
      :is-last="idx + 1 >= order.length"
      @next="next"
    />
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import PokerTable from './PokerTable.vue'
import { progress, record } from '../stores/progress.js'

const props = defineProps({ scenarios: Array })
defineEmits(['exit'])

const { locale } = useI18n()
const SESSION = 10

const order = ref(buildSession())
const idx = ref(0)
const picked = ref(null)
const results = ref([])
const finished = ref(false)

const hasScenarios = computed(() => order.value.length > 0)
const scenario = computed(() => props.scenarios[order.value[idx.value]])
const loc = computed(() => (locale.value === 'en' ? 'en' : 'es'))
const isCorrect = computed(() =>
  picked.value !== null && picked.value === scenario.value.opcion_correcta_index)

const dots = computed(() => order.value.map((_, i) => {
  if (i < results.value.length) return results.value[i] ? 'ok' : 'fail'
  if (i === idx.value) return 'current'
  return 'pending'
}))
const scoreOk = computed(() => results.value.filter(Boolean).length)

// Anillo de precisión (igual que el gimnasio).
const RING_C = 2 * Math.PI * 52
const accuracy = computed(() => results.value.length
  ? Math.round((scoreOk.value / results.value.length) * 100) : 0)
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

// Color de cada botón tras responder: verde=correcto, rojo=tu error, neutro=resto.
function btnClass (i) {
  if (picked.value === null) {
    return 'bg-felt-700 border border-felt-600 hover:bg-felt-600'
  }
  if (i === scenario.value.opcion_correcta_index) return 'bg-gana text-felt-950'
  if (i === picked.value) return 'bg-pierde text-naipe'
  return 'bg-felt-800 border border-felt-700 text-naipe/50'
}
</script>

<template>
  <!-- Estado vacío -->
  <section v-if="!hasScenarios" class="flex-1 flex flex-col items-center justify-center px-5 pb-8 text-center gap-5">
    <p class="text-5xl">🎯</p>
    <p class="text-naipe/70 max-w-xs leading-relaxed">{{ $t('outs.vacio') }}</p>
    <button
      class="px-5 py-3 rounded-xl border border-felt-600 text-naipe/80 hover:border-naipe/40
             focus-visible:outline focus-visible:outline-2 focus-visible:outline-ambar"
      @click="$emit('exit')"
    >{{ $t('resumen.volver') }}</button>
  </section>

  <!-- Resumen de sesión -->
  <section v-else-if="finished" class="flex-1 flex flex-col items-center justify-center px-5 pb-8 text-center">
    <h2 class="text-2xl font-semibold">{{ $t('resumen.titulo') }}</h2>
    <div class="relative w-40 h-40 mt-6">
      <svg viewBox="0 0 120 120" class="w-full h-full -rotate-90">
        <circle cx="60" cy="60" r="52" fill="none" stroke-width="10" class="stroke-felt-700" />
        <circle
          cx="60" cy="60" r="52" fill="none" stroke-width="10" stroke-linecap="round"
          class="transition-all duration-700" :class="ringCls.stroke"
          :stroke-dasharray="RING_C" :stroke-dashoffset="RING_C * (1 - accuracy / 100)"
        />
      </svg>
      <div class="absolute inset-0 flex flex-col items-center justify-center">
        <span class="font-num text-4xl" :class="ringCls.text">{{ accuracy }}%</span>
        <span class="font-num text-xs text-naipe/50 mt-0.5">{{ scoreOk }}/{{ results.length }}</span>
      </div>
    </div>
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

  <!-- Ejercicio -->
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

    <div class="flex items-center gap-1 mt-3">
      <span
        v-for="(d, i) in dots" :key="i"
        class="h-2 flex-1 rounded-full transition-colors duration-300"
        :class="{ 'bg-gana': d === 'ok', 'bg-pierde': d === 'fail', 'bg-ambar': d === 'current', 'bg-felt-700': d === 'pending' }"
      />
    </div>

    <div class="mt-4">
      <PokerTable :scenario="scenario" />
    </div>

    <p class="mt-5 text-sm leading-relaxed text-naipe/80 bg-felt-800 border border-felt-700 rounded-xl px-4 py-3">
      {{ scenario.accion_previa[loc] }}
    </p>

    <!-- Opciones de porcentaje -->
    <div class="mt-4 grid grid-cols-2 gap-3">
      <button
        v-for="(op, i) in scenario.opciones" :key="op"
        class="py-4 rounded-2xl text-lg font-semibold font-num transition-colors
               focus-visible:outline focus-visible:outline-2 focus-visible:outline-naipe"
        :class="btnClass(i)"
        :disabled="picked !== null"
        @click="choose(i)"
      >{{ op }}</button>
    </div>

    <!-- Repaso del cálculo -->
    <div v-if="picked !== null" class="mt-4 rounded-2xl border p-4"
      :class="isCorrect ? 'border-gana/40 bg-gana/5' : 'border-pierde/40 bg-pierde/5'">
      <div class="flex items-center justify-between">
        <span class="font-semibold" :class="isCorrect ? 'text-gana' : 'text-pierde'">
          {{ isCorrect ? '✓ ' + $t('whycard.optima') : '✗ ' + $t('outs.fallo') }}
        </span>
        <span class="font-num text-sm text-naipe/70">
          {{ $t('outs.outs', { n: scenario.math.outs }) }} ·
          {{ Math.round(scenario.math.prob * 100) }}%
        </span>
      </div>
      <p class="mt-2 text-sm text-naipe/85 leading-relaxed">{{ scenario.explicacion[loc] }}</p>
    </div>

    <button
      v-if="picked !== null"
      class="mt-4 w-full py-3.5 rounded-2xl bg-ambar text-felt-950 text-lg font-semibold
             hover:brightness-110 focus-visible:outline focus-visible:outline-2 focus-visible:outline-naipe"
      @click="next"
    >{{ idx + 1 >= order.length ? $t('whycard.verResumen') : $t('whycard.siguiente') }}</button>
  </section>
</template>

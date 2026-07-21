<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import PokerTable from './PokerTable.vue'
import WhyCard from './WhyCard.vue'
import { record } from '../stores/progress.js'

const props = defineProps({ scenarios: Array })
defineEmits(['exit'])

const { locale } = useI18n()
const SESSION = 10

// Sesión: mezcla ligera reproducible por día para variar sin repetirse
const order = ref(shuffle([...props.scenarios.keys()]).slice(0, SESSION))
const idx = ref(0)
const picked = ref(null)          // índice de opción elegida, null = sin responder
const results = ref([])           // booleans de la sesión
const finished = ref(false)

const scenario = computed(() => props.scenarios[order.value[idx.value]])
const isCorrect = computed(() =>
  picked.value !== null && picked.value === scenario.value.opcion_correcta_index)

function shuffle (arr) {
  const seed = Number(new Date().toISOString().slice(0, 10).replaceAll('-', ''))
  let s = seed
  const rnd = () => ((s = (s * 9301 + 49297) % 233280) / 233280)
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(rnd() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]]
  }
  return arr
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
  order.value = shuffle([...props.scenarios.keys()]).slice(0, SESSION)
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
    <p class="font-num text-5xl mt-4 text-ambar">
      {{ $t('resumen.aciertos', { ok: results.filter(Boolean).length, total: results.length }) }}
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

  <!-- Gimnasio -->
  <section v-else class="flex-1 flex flex-col px-4 pb-6 max-w-md w-full mx-auto">
    <div class="flex items-center justify-between text-sm text-naipe/50">
      <button
        class="underline-offset-2 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-ambar rounded"
        @click="$emit('exit')"
      >← {{ $t('gimnasio.salir') }}</button>
      <span class="font-num">{{ $t('gimnasio.mano', { actual: idx + 1, total: order.length }) }}</span>
      <span class="text-xs px-2 py-0.5 rounded-full border border-felt-600">
        {{ $t('dificultad.' + scenario.dificultad) }}
      </span>
    </div>

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

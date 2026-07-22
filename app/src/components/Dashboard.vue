<script setup>
import { computed } from 'vue'
import { progress, stats } from '../stores/progress.js'

defineProps({ counts: Object })
defineEmits(['start'])

const s = computed(() => stats())
</script>

<template>
  <section class="flex-1 flex flex-col px-5 pb-8 max-w-md w-full mx-auto">
    <h1 class="text-2xl font-semibold mt-4">{{ $t('dashboard.saludo') }}</h1>

    <!-- Marcadores -->
    <div class="grid grid-cols-2 gap-3 mt-6">
      <div class="bg-felt-800 rounded-2xl p-4 border border-felt-700">
        <p class="text-xs uppercase tracking-widest text-naipe/40">{{ $t('dashboard.racha') }}</p>
        <p class="font-num text-3xl mt-1 text-ambar">
          {{ progress.streak }}<span class="text-sm text-naipe/50 ml-1">{{ $t('dashboard.dias') }}</span>
        </p>
      </div>
      <div class="bg-felt-800 rounded-2xl p-4 border border-felt-700">
        <p class="text-xs uppercase tracking-widest text-naipe/40">{{ $t('dashboard.precision') }}</p>
        <p class="font-num text-3xl mt-1" :class="s.total ? 'text-gana' : 'text-naipe/30'">
          {{ s.total ? s.accuracy + '%' : '—' }}
        </p>
        <p class="text-xs text-naipe/40 mt-1">{{ s.total }} {{ $t('dashboard.manos') }}</p>
      </div>
    </div>

    <p v-if="!s.total" class="text-sm text-naipe/50 mt-4">{{ $t('dashboard.vacio') }}</p>

    <!-- Modos -->
    <div class="mt-auto pt-8 space-y-3">
      <button
        class="w-full flex items-center gap-4 text-left bg-felt-700 hover:bg-felt-600 border border-ambar-dim
               rounded-2xl p-5 transition-colors
               focus-visible:outline focus-visible:outline-2 focus-visible:outline-ambar"
        @click="$emit('start', 'Torneo')"
      >
        <span class="text-2xl w-11 h-11 shrink-0 grid place-items-center rounded-xl bg-felt-950/60 border border-ambar-dim">🏆</span>
        <span class="flex-1">
          <span class="block text-lg font-semibold text-ambar">{{ $t('dashboard.modoTorneos') }}</span>
          <span class="block text-sm text-naipe/60 mt-0.5">
            {{ $t('dashboard.modoTorneosDesc', { n: counts.torneo }) }}
          </span>
        </span>
        <span class="text-naipe/30 text-xl" aria-hidden="true">›</span>
      </button>

      <button
        class="w-full flex items-center gap-4 text-left bg-felt-700 hover:bg-felt-600 border border-felt-600
               rounded-2xl p-5 transition-colors
               focus-visible:outline focus-visible:outline-2 focus-visible:outline-ambar"
        @click="$emit('start', 'Cash Game')"
      >
        <span class="text-2xl w-11 h-11 shrink-0 grid place-items-center rounded-xl bg-felt-950/60 border border-felt-600">💵</span>
        <span class="flex-1">
          <span class="block text-lg font-semibold">{{ $t('dashboard.modoCash') }}</span>
          <span class="block text-sm text-naipe/60 mt-0.5">
            {{ $t('dashboard.modoCashDesc', { n: counts.cash }) }}
          </span>
        </span>
        <span class="text-naipe/30 text-xl" aria-hidden="true">›</span>
      </button>

      <button
        class="w-full flex items-center gap-4 text-left bg-felt-700 hover:bg-felt-600 border border-felt-600
               rounded-2xl p-5 transition-colors
               focus-visible:outline focus-visible:outline-2 focus-visible:outline-ambar"
        @click="$emit('start', 'Mano Completa')"
      >
        <span class="text-2xl w-11 h-11 shrink-0 grid place-items-center rounded-xl bg-felt-950/60 border border-felt-600">🎬</span>
        <span class="flex-1">
          <span class="block text-lg font-semibold">{{ $t('dashboard.modoMano') }}</span>
          <span class="block text-sm text-naipe/60 mt-0.5">
            {{ $t('dashboard.modoManoDesc', { n: counts.manos }) }}
          </span>
        </span>
        <span class="text-naipe/30 text-xl" aria-hidden="true">›</span>
      </button>
    </div>
  </section>
</template>

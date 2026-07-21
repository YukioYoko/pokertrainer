<script setup>
import PlayingCard from './PlayingCard.vue'

defineProps({ scenario: Object })
</script>

<template>
  <div class="relative mx-auto w-full max-w-sm aspect-[4/3]">
    <!-- Paño -->
    <div class="absolute inset-4 rounded-[45%] bg-felt-700 border-4 border-felt-600 shadow-inner" />

    <!-- Villano (arriba) -->
    <div class="absolute top-0 left-1/2 -translate-x-1/2 text-center">
      <div class="bg-felt-900 border border-felt-600 rounded-xl px-3 py-1.5">
        <p class="text-[11px] uppercase tracking-wider text-naipe/50">{{ $t('gimnasio.villano') }}</p>
        <p class="text-sm font-semibold">{{ $t('posicion.' + scenario.posicion_villano) }}</p>
      </div>
    </div>

    <!-- Pozo (centro) -->
    <div class="absolute inset-0 flex flex-col items-center justify-center gap-1">
      <div v-if="scenario.board.length" class="flex gap-1.5 mb-1">
        <PlayingCard v-for="c in scenario.board" :key="c" :card="c" size="sm" />
      </div>
      <div class="bg-felt-950/70 rounded-full px-4 py-1 border border-ambar-dim">
        <span class="text-[11px] uppercase tracking-wider text-naipe/50 mr-2">{{ $t('gimnasio.pozo') }}</span>
        <span class="font-num text-ambar font-semibold">{{ scenario.pozo_bb }} BB</span>
      </div>
    </div>

    <!-- Héroe (abajo) -->
    <div class="absolute bottom-0 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2">
      <div class="flex gap-2">
        <PlayingCard v-for="c in scenario.cartas_heroe" :key="c" :card="c" />
      </div>
      <div class="bg-felt-900 border border-ambar rounded-xl px-4 py-1.5 text-center">
        <p class="text-sm font-semibold text-ambar">{{ $t('posicion.' + scenario.posicion_heroe) }}</p>
        <p class="font-num text-sm">
          <span class="text-naipe/50 text-[11px] uppercase tracking-wider mr-1">{{ $t('gimnasio.stack') }}</span>
          {{ scenario.stack_bb }} BB
        </p>
      </div>
    </div>
  </div>
</template>

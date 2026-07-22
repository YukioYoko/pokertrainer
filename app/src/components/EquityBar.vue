<script setup>
import { computed } from 'vue'

// Barra de evaluación al estilo chess.com: cuánta equidad tienes (relleno)
// frente al umbral de pot odds que necesitas (marcador). Si el relleno pasa
// el marcador, pagar es rentable.
const props = defineProps({
  equity: Number,   // 0..1
  potOdds: Number   // 0..1
})

const win = computed(() => props.equity >= props.potOdds)
// Probabilidad de que el rival tenga la mejor mano (complemento de tu equidad).
const villano = computed(() => Math.max(0, 1 - props.equity))
const pct = (x) => Math.round(x * 1000) / 10
const clamp = (x) => Math.min(100, Math.max(0, x * 100))
</script>

<template>
  <div>
    <div class="flex justify-between text-[11px] uppercase tracking-wider text-naipe/50 mb-1.5">
      <span>{{ $t('whycard.equity') }}</span>
      <span>{{ $t('whycard.potOdds') }}</span>
    </div>

    <div class="relative">
      <!-- Pista + relleno de equidad -->
      <div class="h-4 rounded-full bg-felt-950 border border-felt-700 overflow-hidden">
        <div
          class="h-full rounded-full transition-all duration-500"
          :class="win ? 'bg-gana' : 'bg-pierde'"
          :style="{ width: clamp(equity) + '%' }"
        />
      </div>
      <!-- Marcador del umbral (pot odds) -->
      <div
        class="absolute -top-1 h-6 w-0.5 bg-naipe"
        :style="{ left: clamp(potOdds) + '%' }"
        aria-hidden="true"
      >
        <span class="absolute -top-4 left-1/2 -translate-x-1/2 text-[10px] text-naipe/70">▼</span>
      </div>
    </div>

    <p class="text-xs text-naipe/70 mt-2.5 font-num">
      {{ $t('evalbar.tienes') }} <b class="text-naipe">{{ pct(equity) }}%</b>
      · {{ $t('evalbar.necesitas') }} <b class="text-naipe">{{ pct(potOdds) }}%</b>
      →
      <span :class="win ? 'text-gana font-semibold' : 'text-pierde font-semibold'">
        {{ win ? $t('evalbar.rentable') : $t('evalbar.noRentable') }}
      </span>
    </p>
    <p class="text-xs text-naipe/50 mt-1 font-num">
      {{ $t('evalbar.rivalMejor') }} <b class="text-pierde/90">{{ pct(villano) }}%</b>
    </p>
  </div>
</template>

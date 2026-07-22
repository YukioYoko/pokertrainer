<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import PlayingCard from './PlayingCard.vue'

const props = defineProps({ scenario: Object })
const { locale, t } = useI18n()

// Nombre de una posición: usa el label bilingüe embebido si viene, si no i18n.
function posName (op) {
  if (op?.pos_label) return op.pos_label[locale.value] || op.pos_label.es
  return t('posicion.' + op.posicion)
}

// Lista de villanos a pintar arriba. Fallback: un único villano legacy.
const villanos = computed(() => {
  if (props.scenario.oponentes?.length) return props.scenario.oponentes
  return [{ posicion: props.scenario.posicion_villano, rol: null }]
})
const asientosVacios = computed(() => props.scenario.asientos_vacios || 0)

const ROL_LABEL = {
  agresor: { es: 'apuesta', en: 'bets' },
  pagador: { es: 'iguala', en: 'calls' },
  ciega: { es: 'ciega', en: 'blind' }
}
function rolName (rol) {
  return rol ? (ROL_LABEL[rol]?.[locale.value] || ROL_LABEL[rol]?.es) : null
}
</script>

<template>
  <div class="relative mx-auto w-full max-w-sm">
    <!-- Paño (óvalo decorativo de fondo) -->
    <div class="absolute inset-0 rounded-[42%] bg-felt-700 border-4 border-felt-600 shadow-inner" />

    <!-- Contenido en columna: nada se solapa -->
    <div class="relative flex flex-col items-center justify-between gap-4 min-h-[20rem] py-6 px-4">
      <!-- Villanos + asientos vacíos (arriba) -->
      <div class="flex items-start justify-center gap-2 flex-wrap">
        <div
          v-for="(op, i) in villanos" :key="'v' + i"
          class="bg-felt-900 border border-felt-600 rounded-xl px-3 py-1.5 text-center"
        >
          <p class="text-[11px] uppercase tracking-wider text-naipe/50">
            {{ $t('gimnasio.villano') }}<span v-if="rolName(op.rol)"> · {{ rolName(op.rol) }}</span>
          </p>
          <p class="text-sm font-semibold">{{ posName(op) }}</p>
        </div>
        <!-- Asientos vacíos: comunican la mesa completa (cosmético) -->
        <div
          v-for="s in asientosVacios" :key="'s' + s"
          class="w-9 h-9 rounded-full border border-dashed border-felt-600/70 opacity-40
                 flex items-center justify-center text-naipe/30 text-xs"
          aria-hidden="true"
        >∅</div>
      </div>

      <!-- Board + Pozo (centro) -->
      <div class="flex flex-col items-center gap-2">
        <div v-if="scenario.board.length" class="flex gap-1.5">
          <PlayingCard v-for="c in scenario.board" :key="c" :card="c" size="sm" />
        </div>
        <div v-if="scenario.pozo_bb != null" class="bg-felt-950/70 rounded-full px-4 py-1 border border-ambar-dim">
          <span class="text-[11px] uppercase tracking-wider text-naipe/50 mr-2">{{ $t('gimnasio.pozo') }}</span>
          <span class="font-num text-ambar font-semibold">{{ scenario.pozo_bb }} BB</span>
        </div>
      </div>

      <!-- Héroe (abajo) -->
      <div class="flex flex-col items-center gap-2">
        <div class="flex gap-2">
          <PlayingCard v-for="c in scenario.cartas_heroe" :key="c" :card="c" />
        </div>
        <div class="bg-felt-900 border border-ambar rounded-xl px-4 py-1.5 text-center">
          <p class="text-sm font-semibold text-ambar">{{ $t('posicion.' + scenario.posicion_heroe) }}</p>
          <p v-if="scenario.stack_bb != null" class="font-num text-sm">
            <span class="text-naipe/50 text-[11px] uppercase tracking-wider mr-1">{{ $t('gimnasio.stack') }}</span>
            {{ scenario.stack_bb }} BB
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

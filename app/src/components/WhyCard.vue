<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import EquityBar from './EquityBar.vue'

const props = defineProps({
  scenario: Object,
  correct: Boolean,
  isLast: Boolean
})
defineEmits(['next'])

const { locale, t } = useI18n()
const tab = ref('matematica')

const TABS = [
  { id: 'matematica', campo: 'matematica_rapida' },
  { id: 'rangos', campo: 'psicologia_y_rangos' },
  { id: 'conclusion', campo: 'control_y_conclusion' }
]

const desglose = computed(() =>
  props.scenario.desglose[locale.value] || props.scenario.desglose.es)
const correctAction = computed(() =>
  props.scenario.opciones[props.scenario.opcion_correcta_index])
</script>

<template>
  <Transition name="fade" appear>
    <div class="fixed inset-0 bg-felt-950/70 z-10" aria-hidden="true" />
  </Transition>

  <Transition name="slide-up" appear>
    <div
      class="fixed inset-x-0 bottom-0 z-20 bg-felt-800 rounded-t-3xl shadow-panel
             max-w-md mx-auto max-h-[80dvh] flex flex-col"
      role="dialog" aria-modal="true"
    >
      <!-- Veredicto -->
      <div
        class="rounded-t-3xl px-5 py-4"
        :class="correct ? 'bg-gana/15 border-b border-gana/40' : 'bg-pierde/15 border-b border-pierde/40'"
      >
        <p class="text-lg font-semibold" :class="correct ? 'text-gana' : 'text-pierde'">
          {{ correct ? '✓ ' + t('whycard.optima') : '✗ ' + t('whycard.error') }}
        </p>
        <p v-if="!correct" class="text-sm text-naipe/70 mt-0.5">
          {{ t('whycard.correctaEra', { accion: correctAction }) }}
        </p>
        <div class="mt-3">
          <EquityBar :equity="scenario.math.equity" :pot-odds="scenario.math.pot_odds" />
        </div>
      </div>

      <!-- Pestañas -->
      <div class="flex border-b border-felt-700">
        <button
          v-for="tb in TABS" :key="tb.id"
          class="flex-1 py-3 text-sm transition-colors
                 focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-ambar"
          :class="tab === tb.id
            ? 'text-ambar border-b-2 border-ambar font-semibold'
            : 'text-naipe/50 hover:text-naipe/80'"
          @click="tab = tb.id"
        >{{ t('whycard.' + tb.id) }}</button>
      </div>

      <div class="px-5 py-4 overflow-y-auto leading-relaxed text-[15px] text-naipe/90">
        {{ desglose[TABS.find(x => x.id === tab).campo] }}
      </div>

      <div class="p-4 pt-2 pb-[max(env(safe-area-inset-bottom),1rem)]">
        <button
          class="w-full py-3.5 rounded-2xl bg-ambar text-felt-950 text-lg font-semibold
                 hover:brightness-110 focus-visible:outline focus-visible:outline-2 focus-visible:outline-naipe"
          @click="$emit('next')"
        >{{ isLast ? t('whycard.verResumen') : t('whycard.siguiente') }}</button>
      </div>
    </div>
  </Transition>
</template>

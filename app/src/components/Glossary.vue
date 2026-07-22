<script setup>
import { useI18n } from 'vue-i18n'
import terms from '../data/glossary.js'

defineEmits(['close'])
const { locale } = useI18n()
const lang = () => (locale.value === 'en' ? 'en' : 'es')
</script>

<template>
  <Transition name="fade" appear>
    <div class="fixed inset-0 bg-felt-950/70 z-30" aria-hidden="true" @click="$emit('close')" />
  </Transition>

  <Transition name="slide-up" appear>
    <div
      class="fixed inset-x-0 bottom-0 z-40 bg-felt-800 rounded-t-3xl shadow-panel
             max-w-md mx-auto max-h-[85dvh] flex flex-col"
      role="dialog" aria-modal="true" :aria-label="$t('glosario.titulo')"
    >
      <div class="flex items-center justify-between px-5 py-4 border-b border-felt-700">
        <h2 class="text-lg font-semibold text-ambar">{{ $t('glosario.titulo') }}</h2>
        <button
          class="text-naipe/50 hover:text-naipe rounded-full w-8 h-8 flex items-center justify-center
                 focus-visible:outline focus-visible:outline-2 focus-visible:outline-ambar"
          :aria-label="$t('glosario.cerrar')"
          @click="$emit('close')"
        >✕</button>
      </div>

      <p class="px-5 pt-3 text-sm text-naipe/50">{{ $t('glosario.intro') }}</p>

      <div class="px-5 py-3 overflow-y-auto space-y-4">
        <div
          v-for="t in terms" :key="t.id"
          class="border-b border-felt-700/60 pb-3 last:border-0"
        >
          <p class="font-semibold text-naipe">{{ t.label[lang()] }}</p>
          <p class="text-sm text-naipe/70 mt-1 leading-relaxed">{{ t.def[lang()] }}</p>
        </div>
      </div>

      <div class="p-4 pt-2 pb-[max(env(safe-area-inset-bottom),1rem)]">
        <button
          class="w-full py-3.5 rounded-2xl bg-ambar text-felt-950 text-lg font-semibold
                 hover:brightness-110 focus-visible:outline focus-visible:outline-2 focus-visible:outline-naipe"
          @click="$emit('close')"
        >{{ $t('glosario.cerrar') }}</button>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Dashboard from './components/Dashboard.vue'
import Gimnasio from './components/Gimnasio.vue'
import Glossary from './components/Glossary.vue'
import { load, progress, setLocale } from './stores/progress.js'

const { locale } = useI18n()
const view = ref('dashboard') // 'dashboard' | 'gimnasio'
const showGlossary = ref(false)
const mode = ref('Torneo')    // 'Torneo' | 'Cash Game'
const all = ref([])           // scenarios_db.json cargado como asset estático
const ready = ref(false)

const scenarios = computed(() =>
  all.value.filter(s => s.modo === mode.value))
const counts = computed(() => ({
  torneo: all.value.filter(s => s.modo === 'Torneo').length,
  cash: all.value.filter(s => s.modo === 'Cash Game').length
}))

function start (m) {
  mode.value = m
  view.value = 'gimnasio'
}

onMounted(async () => {
  await load()
  locale.value = progress.locale
  const res = await fetch(import.meta.env.BASE_URL + 'scenarios_db.json')
  all.value = (await res.json()).escenarios
  ready.value = true
})

async function toggleLocale () {
  locale.value = locale.value === 'es' ? 'en' : 'es'
  await setLocale(locale.value)
}
</script>

<template>
  <div class="min-h-dvh flex flex-col bg-felt-950">
    <header class="flex items-center justify-between px-5 pt-[max(env(safe-area-inset-top),1rem)] pb-3">
      <div class="flex items-baseline gap-2">
        <span class="text-ambar font-semibold tracking-wide">{{ $t('app.titulo') }}</span>
        <span class="text-xs text-naipe/40">{{ $t('app.subtitulo') }}</span>
      </div>
      <div class="flex items-center gap-2">
        <button
          class="text-xs tracking-wide border border-felt-600 rounded-full px-3 py-1
                 text-naipe/70 hover:border-ambar hover:text-ambar transition-colors
                 focus-visible:outline focus-visible:outline-2 focus-visible:outline-ambar"
          :aria-label="$t('glosario.titulo')"
          @click="showGlossary = true"
        >
          {{ $t('glosario.boton') }}
        </button>
        <button
          class="text-xs font-num tracking-widest border border-felt-600 rounded-full px-3 py-1
                 text-naipe/70 hover:border-ambar hover:text-ambar transition-colors
                 focus-visible:outline focus-visible:outline-2 focus-visible:outline-ambar"
          @click="toggleLocale"
        >
          {{ locale === 'es' ? 'ES · en' : 'es · EN' }}
        </button>
      </div>
    </header>

    <main class="flex-1 flex flex-col">
      <Dashboard
        v-if="view === 'dashboard' && ready"
        :counts="counts"
        @start="start"
      />
      <Gimnasio
        v-else
        :key="mode"
        :scenarios="scenarios"
        @exit="view = 'dashboard'"
      />
    </main>

    <Glossary v-if="showGlossary" @close="showGlossary = false" />
  </div>
</template>

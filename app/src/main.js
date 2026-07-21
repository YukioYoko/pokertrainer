import { createApp } from 'vue'
import { createI18n } from 'vue-i18n'
import App from './App.vue'
import es from './i18n/es.json'
import en from './i18n/en.json'
import './style.css'

export const i18n = createI18n({
  legacy: false,
  locale: 'es',          // prioridad al español
  fallbackLocale: 'es',
  messages: { es, en }
})

createApp(App).use(i18n).mount('#app')

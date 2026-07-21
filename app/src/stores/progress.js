/**
 * Progreso local del jugador con @capacitor/preferences.
 * (En web usa localStorage por debajo; en Android, SharedPreferences nativas.)
 * Guarda: racha de días, historial de respuestas, contadores de leaks e idioma.
 */
import { reactive } from 'vue'
import { Preferences } from '@capacitor/preferences'

const KEY = 'pg_progress_v1'

export const progress = reactive({
  locale: 'es',
  streak: 0,
  lastDay: null,        // 'YYYY-MM-DD' del último día jugado
  answered: {},         // id -> true si fue correcta, false si no
  leaks: {},            // leak_tag -> nº de fallos (base del Leaks Analyzer)
  loaded: false
})

export async function load () {
  const { value } = await Preferences.get({ key: KEY })
  if (value) Object.assign(progress, JSON.parse(value))
  progress.loaded = true
}

async function save () {
  const { loaded, ...data } = progress
  await Preferences.set({ key: KEY, value: JSON.stringify(data) })
}

export async function setLocale (locale) {
  progress.locale = locale
  await save()
}

/** Registra una respuesta y actualiza racha + leaks. */
export async function record (scenario, wasCorrect) {
  progress.answered[scenario.id] = wasCorrect
  if (!wasCorrect) {
    for (const tag of scenario.leak_tags || []) {
      progress.leaks[tag] = (progress.leaks[tag] || 0) + 1
    }
  }
  const today = new Date().toISOString().slice(0, 10)
  if (progress.lastDay !== today) {
    const yesterday = new Date(Date.now() - 864e5).toISOString().slice(0, 10)
    progress.streak = progress.lastDay === yesterday ? progress.streak + 1 : 1
    progress.lastDay = today
  }
  await save()
}

export function stats () {
  const values = Object.values(progress.answered)
  const total = values.length
  const ok = values.filter(Boolean).length
  return { total, ok, accuracy: total ? Math.round((ok / total) * 100) : 0 }
}

// ---------------------------------------------------------------------------
// TODO RevenueCat (@revenuecat/purchases-capacitor):
//   import { Purchases } from '@revenuecat/purchases-capacitor'
//   await Purchases.configure({ apiKey: 'goog_XXXX' })
//   const { customerInfo } = await Purchases.getCustomerInfo()
//   → desbloquear contenido si customerInfo.entitlements.active['pro']
//   La validación de recibos ocurre server-side en RevenueCat, nunca aquí.
// ---------------------------------------------------------------------------
// TODO Firebase (Auth + Firestore):
//   Solo para cuenta, sincronizar `progress` entre dispositivos y respaldar
//   el estado premium vía webhook de RevenueCat. La app funciona 100% offline
//   sin esto.
// ---------------------------------------------------------------------------

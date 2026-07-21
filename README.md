# Poker Gym — MVP Push/Fold (bilingüe ES/EN)

Entrenador de póker push/fold, offline-first. Los **2500 escenarios ya vienen
generados y validados** (`app/public/scenarios_db.json`: 2000 Torneo + 500 Cash),
así que para probar la app **no hace falta correr el pipeline**.

## Correr la app web (esto es lo único que necesitas)

Requisitos: [Node.js](https://nodejs.org/) (incluye `npm`).

    cd app
    npm install      # solo la primera vez
    npm run dev

Vite imprime una URL local (por defecto http://localhost:5173). Ábrela en el
navegador. La app carga los escenarios ya generados y funciona 100% offline;
el idioma (ES/EN) se cambia con el botón de la cabecera.

### Otros comandos de la app

    npm run build      # build de producción a app/dist
    npm run preview    # sirve el build de producción localmente

## Estructura

- `app/` — Entregable B: Vite + Vue 3 + Tailwind + vue-i18n, offline-first,
  lista para Capacitor. Incluye `public/scenarios_db.json` ya generado.
- `pipeline/` — Entregable A: generador de escenarios (Python). **Opcional**:
  solo se usa para regenerar `scenarios_db.json`. Ver más abajo.

## Android (opcional)

    cd app
    npm run build && npx cap add android && npx cap sync && npx cap open android

## Regenerar los escenarios (pipeline — opcional)

Solo necesario si quieres volver a generar `scenarios_db.json`. La matemática
(eval7 Monte Carlo) y la decisión correcta (tabla Nash embebida) las calcula el
código; el LLM (API Anthropic) solo redacta las explicaciones ES+EN. Con
`--offline` funciona sin API usando plantillas. `validate.py` descarta todo
escenario incoherente.

    cd pipeline
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-...        # opcional: ANTHROPIC_MODEL
    python build.py --modo ambos --n 2000 --n-cash 500   # o --offline sin API
    cp scenarios_db.json ../app/public/

## Pendiente (stubs marcados con TODO en src/stores/progress.js)

- RevenueCat (@revenuecat/purchases-capacitor) para packs/suscripción.
- Firebase Auth+Firestore para sincronizar progreso entre dispositivos.

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Poker Gym — a bilingual (ES/EN) push/fold poker trainer MVP. Two deliverables:

- `pipeline/` — Python generator that produces a validated `scenarios_db.json` of training scenarios.
- `app/` — Vite + Vue 3 + Tailwind + vue-i18n web app (offline-first, Capacitor-ready for Android) that consumes that JSON.

The two are connected by one artifact: `scenarios_db.json`. The pipeline writes it; the app reads it from `app/public/scenarios_db.json` (served as a static asset, fetched at runtime — see [app/src/App.vue](app/src/App.vue) `onMounted`). Note: `pipeline/README.md` says to copy the JSON to `app/src/data/`, but the app actually loads it from `app/public/` — the root [README.md](README.md) is correct.

## Commands

### Pipeline (Python)
```bash
cd pipeline
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-...           # optional; also ANTHROPIC_MODEL (default: claude-haiku-4-5-20251001)
python build.py --modo ambos --n 2000 --n-cash 500   # full generation (LLM explanations)
python build.py --modo ambos --n 100 --offline       # no API — deterministic template explanations
cp scenarios_db.json ../app/public/       # publish to the app
```
- `--modo torneo|cash|ambos` selects which generators run. `--n` = tournament count (or cash count when `--modo cash`); `--n-cash` = cash count when `--modo ambos`. `--seed` is fixed (default 42) for deterministic output.
- Individual modules are runnable for quick smoke tests: `python generator.py`, `python cash_generator.py` each print a few sample scenarios.
- There is no test suite or linter configured.

### App (web / Android)
```bash
cd app
npm install
npm run dev          # Vite dev server
npm run build        # production build to app/dist
npm run android      # build + npx cap sync android + npx cap open android
```

## Architecture

### Pipeline: math is computed, the LLM only narrates

The core design rule ("Regla de Oro"): **every number and every correct answer is computed by deterministic code; the LLM never decides anything and never invents numbers.** The LLM is called in exactly one place ([pipeline/explain.py](pipeline/explain.py)) and only writes the ES/EN prose explanations, given the already-computed math. It always has an offline fallback (deterministic templates) and failures never break the build.

Two independent scenario generators, both producing the same scenario schema (with a `modo` field), merged by [pipeline/build.py](pipeline/build.py):

1. **Tournament (Torneo)** — pre-flop push/fold.
   - [pipeline/nash.py](pipeline/nash.py) is the **single source of truth** for the correct action: embedded per-position Nash jam-or-fold thresholds (max stack in BB at which All-In is correct). `correct_action(pos, hand, stack)` → 0 Fold / 1 All-In. Also exposes the BB's calling range.
   - [pipeline/generator.py](pipeline/generator.py) deterministically enumerates position × hand (169) × stack (4–20 BB) combinations, quota-balanced across difficulty tiers (difficulty = distance from the Nash threshold). Extra variation axes (ante, table size) open only if base combinations are exhausted.

2. **Cash Game (Cash)** — river, single bet, 100 BB.
   - Correct action is derived purely from `equity >= pot_odds` → Call, else Fold.
   - [pipeline/cash_ranges.py](pipeline/cash_ranges.py) builds the villain's river betting range as a *verifiable construction*: value combos (two pair+ or strong top pair, classified exactly with eval7) plus the weakest air combos added in exactly the Janda value:bluff ratio for the bet size.
   - [pipeline/cash_math.py](pipeline/cash_math.py) provides MDF, the Janda `value_bluff_ratio`, and exact river equity.

Shared math lives in [pipeline/poker_math.py](pipeline/poker_math.py): eval7-backed equity (Monte Carlo `equity_vs_range` for pre-flop, exact enumeration `equity_river_exact` for the river), pot odds, SPR, hand-notation helpers. All seeded/deterministic.

[pipeline/validate.py](pipeline/validate.py) is the gatekeeper — `build.py` runs it last and drops any scenario that fails. Critically, it **re-derives the correct answer from the source of truth** (re-runs `nash.correct_action` for Torneo, re-checks `equity >= pot_odds` for Cash) and discards mismatches, plus checks schema, card validity, and that every narrative field has both `es` and `en`.

Output shape: `{"version": 2, "escenarios": [...]}`. The internal `_meta` field carries data for the LLM prompt and is stripped before writing.

### App: offline-first Vue

- Single-page, two views toggled by state in [app/src/App.vue](app/src/App.vue): `Dashboard` (mode select) → `Gimnasio` (training session). Mode is `Torneo` | `Cash Game`; scenarios are filtered from the loaded DB by `modo`.
- [app/src/components/Gimnasio.vue](app/src/components/Gimnasio.vue) runs a 10-hand session. Session selection (`buildSession`) is **randomized and prioritizes unseen hands** — scenarios whose `id` is not yet in `progress.answered` come first (shuffled), falling back to already-played ones only once the unseen bank is exhausted, so sessions don't repeat. Answering reveals the `WhyCard` explanation.
- [app/src/stores/progress.js](app/src/stores/progress.js) is the state layer — a Vue `reactive` object persisted via `@capacitor/preferences` (localStorage on web, native SharedPreferences on Android). Tracks daily streak, per-scenario answers, per-`leak_tag` failure counts (basis for a future "Leaks Analyzer"), and locale. This is where the **RevenueCat and Firebase integrations are stubbed** (TODO comments) — the app is fully functional offline without them.
- i18n: Spanish is the priority/default and fallback locale ([app/src/main.js](app/src/main.js)). Scenario prose is stored bilingually inside each scenario (`accion_previa[locale]`, `desglose[locale]`), not in the i18n message files — the i18n JSON only covers UI chrome.
- Styling: Tailwind with a custom "casino felt" dark palette (`felt`, `naipe`, `ambar`, `gana`, `pierde`) defined in [app/tailwind.config.js](app/tailwind.config.js).

## Conventions

- Domain vocabulary and code identifiers are **Spanish** (`escenarios`, `posicion_heroe`, `pozo_bb`, `dificultad`, `opcion_correcta_index`, `desglose`). Match this when extending the scenario schema; both the pipeline and app depend on these exact keys.
- Each scenario carries a `tipo` discriminator; `validate.py` branches on it. Four variants exist, all still deriving the correct answer from a verifiable source (Regla de Oro):
  - `push_fold` (Torneo, `[Fold, All-In]`) — hero jams; source of truth = `nash.correct_action`.
  - `overcall` (Torneo, `[Fold, Call]`) — hero in BB **calls or folds vs a single all-in**. The jammer's range comes from `nash.jam_range` (same thresholds), and the call is derived from `equity_vs_range >= pot_odds` (chip-EV, not ICM). Added by `generator.generate_overcall`.
  - `river_hu` (Cash, `[Fold, Call]`) — the original 1v1 river.
  - `river_3way` (Cash, `[Fold, Call]`) — **3-way river**, hero closing vs an aggressor + a cold-caller. Equity = `poker_math.equity_river_exact_multiway` (exact enumeration of the union of both ranges; hero must beat all to win, splits handled), caller range = `cash_ranges.build_cold_call_range` (one-pair combos). Added by `cash_generator.generate_multiway`.
  - Multiway/overcall are opt-in via `build.py --n-overcall N` / `--n-multiway N`.
- Cash scenarios only ever offer `[Fold, Call]` and push/fold Torneo only `[Fold, All-In]` — Raise and live-multiway-with-open-action are intentionally excluded because their correctness isn't verifiable without a solver.
- Presentation-only keys (do not affect any answer): `oponentes` (list of `{posicion, rol, pos_label}` villain badges) and `asientos_vacios` (int, dimmed empty seats). `PokerTable.vue` renders them, falling back to the single `posicion_villano` badge when `oponentes` is absent.

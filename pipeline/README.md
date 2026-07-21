# Pipeline de escenarios push/fold (Torneos)

1. `pip install -r requirements.txt`
2. `export ANTHROPIC_API_KEY=sk-...` (opcional: `ANTHROPIC_MODEL`)
3. `python build.py --modo ambos --n 2000 --n-cash 500` → `scenarios_db.json` validado
4. Sin API: añade `--offline` (plantillas deterministas de prueba)
   Modos: `--modo torneo|cash|ambos`. Torneo = push/fold Nash (UTG–SB, 4–20 BB);
   Cash = river Fold/Call, equidad exacta vs rango construido con ratio de Janda.
5. Copia el JSON a `app/src/data/scenarios_db.json`

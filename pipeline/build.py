"""build.py — Orquestador maestro del pipeline.

Uso:
  python build.py --modo torneo --n 2000       # solo Torneos
  python build.py --modo cash --n 500          # solo Cash
  python build.py --modo ambos --n 2000 --n-cash 500
  python build.py --modo ambos --n 100 --offline   # sin API (plantillas)
Salida: scenarios_db.json (ambos modos fusionados, campo "modo" incluido).
"""
from __future__ import annotations

import argparse
import json
import sys

import cash_generator
import explain
import generator
import hand_generator
import outs_generator
import validate


def _redact(scenarios: list[dict], offline: bool, label: str) -> None:
    print(f"[·] Redactando {label} "
          f"({'plantilla offline' if offline else 'LLM'})...")
    for i, s in enumerate(scenarios, 1):
        s.update(explain.explain(s, offline=offline))
        if i % 100 == 0:
            print(f"    {i}/{len(scenarios)}")
    for s in scenarios:
        s.pop("_meta", None)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--modo", choices=["torneo", "cash", "ambos"],
                    default="torneo")
    ap.add_argument("--n", type=int, default=100,
                    help="nº de escenarios de Torneo (o de Cash si --modo cash)")
    ap.add_argument("--n-cash", type=int, default=None,
                    help="nº de escenarios de Cash cuando --modo ambos")
    ap.add_argument("--n-overcall", type=int, default=0,
                    help="nº de escenarios de Torneo de overcall (pagar un jam)")
    ap.add_argument("--n-multiway", type=int, default=0,
                    help="nº de escenarios de Cash a 3 bandas (river)")
    ap.add_argument("--n-hands", type=int, default=0,
                    help="nº de escenarios de Mano Completa (flop→turn→river)")
    ap.add_argument("--n-outs", type=int, default=0,
                    help="nº de escenarios de Outs (probabilidad de proyecto)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--out", default="scenarios_db.json")
    args = ap.parse_args()

    scenarios: list[dict] = []

    if args.modo in ("torneo", "ambos"):
        print(f"[1] Generando {args.n} escenarios de Torneo "
              f"(seed={args.seed})...")
        mtt = generator.generate(args.n, args.seed)
        print(f"    {len(mtt)} crudos")
        _redact(mtt, args.offline, "Torneo")
        scenarios += mtt

        if args.n_overcall > 0:
            print(f"[1b] Generando {args.n_overcall} escenarios de overcall "
                  f"(seed={args.seed + 500})...")
            oc = generator.generate_overcall(args.n_overcall, args.seed + 500)
            print(f"    {len(oc)} crudos")
            _redact(oc, args.offline, "Torneo/overcall")
            scenarios += oc

    if args.modo in ("cash", "ambos"):
        n_cash = args.n if args.modo == "cash" else (args.n_cash or args.n)
        print(f"[2] Generando {n_cash} escenarios de Cash "
              f"(seed={args.seed + 1000})...")
        cash = cash_generator.generate(n_cash, args.seed + 1000)
        print(f"    {len(cash)} crudos")
        _redact(cash, args.offline, "Cash")
        scenarios += cash

        if args.n_multiway > 0:
            print(f"[2b] Generando {args.n_multiway} escenarios de Cash 3-bandas "
                  f"(seed={args.seed + 2000})...")
            mw = cash_generator.generate_multiway(args.n_multiway,
                                                  args.seed + 2000)
            print(f"    {len(mw)} crudos")
            _redact(mw, args.offline, "Cash/3-bandas")
            scenarios += mw

    if args.n_hands > 0:
        print(f"[3] Generando {args.n_hands} escenarios de Mano Completa "
              f"(seed={args.seed + 3000})...")
        hands = hand_generator.generate(args.n_hands, args.seed + 3000)
        print(f"    {len(hands)} crudos")
        _redact(hands, args.offline, "Mano Completa")
        scenarios += hands

    if args.n_outs > 0:
        print(f"[3b] Generando {args.n_outs} escenarios de Outs "
              f"(seed={args.seed + 4000})...")
        outs = outs_generator.generate(args.n_outs, args.seed + 4000)
        print(f"    {len(outs)} crudos")
        _redact(outs, args.offline, "Outs")
        scenarios += outs

    print("[4] Validando esquema y coherencia...")
    ok, log = validate.filter_valid(scenarios)
    for line in log[:20]:
        print(f"    DESCARTADO {line}")
    if len(log) > 20:
        print(f"    (+{len(log) - 20} más)")
    print(f"    {len(ok)} válidos / {len(scenarios)} generados")

    print(f"[5] Escribiendo {args.out}...")
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"version": 2, "escenarios": ok}, f,
                  ensure_ascii=False, indent=1)

    stats: dict = {}
    for s in ok:
        k = (s["modo"], s["dificultad"])
        stats[k] = stats.get(k, 0) + 1
    for (modo, diff), c in sorted(stats.items()):
        print(f"    {modo:10s} {diff:12s} {c}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

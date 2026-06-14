#!/usr/bin/env python3
"""Running-coach CLI.

Leest het Excel-logboek + Garmin .fit-bestanden, berekent belasting/fitheid,
maakt grafieken, schrijft (optioneel via Claude) een weeknotitie en ververst
het dashboard-rapport.

Gebruik:
    python running_coach.py                # alles: data + metrieken + grafieken + rapport
    python running_coach.py --no-charts    # sla grafieken over (sneller)
    python running_coach.py --coach        # incl. Claude weeknotitie (vereist ANTHROPIC_API_KEY)
    python running_coach.py --cache        # gebruik runs.json i.p.v. opnieuw inlezen
    python running_coach.py --status       # alleen status naar de terminal
"""
import argparse

from coach import loader, metrics, charts, coachnote, report, weekly


def print_status(runs):
    fit = metrics.fitness_series(runs)
    acwr = metrics.acwr_series(runs)
    print(f"\nLopen: {len(runs)}  ({runs[0].d} → {runs[-1].d})")
    if fit:
        d, ctl, atl, tsb = fit[-1]
        print(f"CTL {ctl:.0f} | ATL {atl:.0f} | TSB {tsb:+.0f}")
    if acwr:
        a = acwr[-1][1]
        print(f"ACWR {a:.2f}  -> {metrics.acwr_flag(a)}")
    print("\nLaatste 6 weken:")
    for w in metrics.weekly_summary(runs, 6):
        print(f"  {w['year']}-W{w['week']:02d}  {w['runs']:2d}x  {w['km']:5.1f} km  "
              f"HS {w['avg_hr'] or '-'}  load {w['load']}")


def main():
    ap = argparse.ArgumentParser(description="Running-coach analyse & rapport")
    ap.add_argument("--cache", action="store_true", help="gebruik runs.json cache")
    ap.add_argument("--no-charts", action="store_true", help="grafieken overslaan")
    ap.add_argument("--coach", action="store_true", help="Claude weeknotitie genereren")
    ap.add_argument("--status", action="store_true", help="alleen terminalstatus")
    ap.add_argument("--weeks-all", action="store_true",
                    help="(her)genereer een weekbestand voor elke ISO-week met lopen")
    args = ap.parse_args()

    print("Data inlezen...")
    runs = loader.load_runs(use_cache=args.cache)
    print(f"  {len(runs)} lopen geladen.")

    if args.status:
        print_status(runs)
        return

    chart_names = []
    if not args.no_charts:
        print("Grafieken maken...")
        chart_names = charts.generate_all(runs)
        print(f"  {len(chart_names)} grafieken in {charts.config.CHART_DIR}")

    note = "_(coach-laag niet uitgevoerd — start met --coach)_"
    if args.coach:
        print("Claude weeknotitie genereren...")
        note = coachnote.weekly_note(runs)

    print("Rapport schrijven...")
    path = report.build(runs, chart_names, note)
    print(f"  -> {path}")

    print("Weekbestand schrijven...")
    if args.weeks_all:
        seen = sorted({r.d.isocalendar()[:2] for r in runs})
        n = sum(weekly.build_week(runs, iso) is not None for iso in seen)
        print(f"  -> {n} weekbestanden in {weekly.config.WEEK_DIR}")
    else:
        for wp in weekly.build_latest(runs):
            print(f"  -> {wp}")

    print_status(runs)


if __name__ == "__main__":
    main()

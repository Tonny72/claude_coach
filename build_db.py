#!/usr/bin/env python3
"""Bouw/ververs de SQLite-databank (`garmin.db`) uit alle Garmin-bronnen + het Excel-logboek.

    python build_db.py            # incrementeel (alleen gewijzigde/nieuwe bronbestanden)
    python build_db.py --rebuild  # alles weggooien en opnieuw inlezen
    python build_db.py --status   # alleen de inhoudsopgave tonen

Zie coach/db.py voor het schema en de bronnen.
"""
import argparse

from coach import config, db


def main():
    ap = argparse.ArgumentParser(description="Garmin → SQLite databank")
    ap.add_argument("--rebuild", action="store_true", help="volledig opnieuw opbouwen")
    ap.add_argument("--status", action="store_true", help="alleen inhoudsopgave tonen")
    args = ap.parse_args()

    if args.status:
        print(db.summary())
        return

    print(f"Databank bouwen → {config.DB_PATH}" + ("  (volledig opnieuw)" if args.rebuild else "  (incrementeel)"))
    res = db.build(rebuild=args.rebuild)
    print("Ingelezen:")
    print(f"  activiteiten (FIT) : {res['fit_act']:>5}  uit {res['fit_files']} bestanden")
    print(f"  activiteiten (log) : {res['log']:>5}")
    print(f"  wellness-dagen     : {res['wellness_days']:>5}  uit {res['wellness_files']} bestanden")
    print(f"  persoonlijke rec.  : {res['pr']:>5}")
    print(f"  gear               : {res['gear']:>5}")
    print()
    print(db.summary())


if __name__ == "__main__":
    main()

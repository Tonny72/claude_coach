# Running-coach

Analyseert je hardloophistorie uit `Conditie verloop.xlsx` (tab *Reeksen*, 2001–2025) +
de Garmin Fenix `.fit`-bestanden (2025–heden), berekent belasting/fitheid en ververst
het dashboard-rapport.

## Installatie
De venv staat lokaal (buiten de OneDrive/HGFS-map, want die ondersteunt geen symlinks):
```bash
python -m venv ~/.venvs/garmin-coach
source ~/.venvs/garmin-coach/bin/activate
pip install fitparse openpyxl matplotlib anthropic pandas
```

## Gebruik
```bash
cd "/mnt/hgfs/D/OneDrive/Running/claude coach" && source ~/.venvs/garmin-coach/bin/activate
python running_coach.py            # data + metrieken + grafieken + rapport + weekbestand
python running_coach.py --cache    # sneller: gebruik runs.json i.p.v. opnieuw inlezen
python running_coach.py --no-charts
python running_coach.py --status   # alleen status in de terminal
python running_coach.py --coach    # incl. Claude weeknotitie (vereist ANTHROPIC_API_KEY)
python running_coach.py --weeks-all  # (her)genereer alle historische weekbestanden
```

Voor de Claude coach-laag:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
python running_coach.py --coach
```

## Uitvoer (in de projectmap `claude coach/`)
- `Analyse_Looptraining.md` — het levende verslag (auto + handmatig logboek dat behouden blijft).
- `Weken/<jaar>-W<week>.md` — één bestand per week: analyse van die week +
  schema voor de week erna. De `COACH-ANALYSE`-sectie blijft behouden bij verversen.
- `charts/*.png` — grafieken.

## Wat wordt berekend
| Metriek | Betekenis |
|---|---|
| **TRIMP** (Banister) | trainingsbelasting per loop uit HS-reserve |
| **CTL / ATL / TSB** | fitness / vermoeidheid / vorm (impulse-respons) |
| **ACWR** | acuut:chronisch (7d:28d) → blessurerisico, optimaal 0,8–1,3 |
| **Efficiency Factor** | snelheid per hartslag → aerobe vorm |

Zones (Karvonen) en richttempo's worden uit je recente data afgeleid en passen zich
automatisch aan zodra je nieuwe `.fit`-bestanden synct.

## Structuur
```
coach/
  config.py     # paden + atleetparameters (geboortejaar, rust-HS, modelconstanten)
  loader.py     # inlezen Excel + .fit -> Run-objecten
  metrics.py    # TRIMP, CTL/ATL/TSB, ACWR, efficiency
  zones.py      # HS-zones + richttempo's uit recente data
  charts.py     # 6 PNG-grafieken
  coachnote.py  # Claude-API weeknotitie (optioneel)
  report.py     # bouwt het levende verslag-markdown
  weekly.py     # bouwt één weekbestand per ISO-week (analyse + schema)
running_coach.py  # CLI
```

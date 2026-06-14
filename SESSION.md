# Sessie-overzicht — Running-coach

_Laatst bijgewerkt: 2026-06-14_

## Locatie & venv (BELANGRIJK)
- **Projectcode:** `/mnt/hgfs/D/OneDrive/Running/claude coach/` (verhuisd van `~/dev/Garmin` → `…/Running/claude/` → `…/Running/claude coach/`, synct via OneDrive).
- **Brondata vs. output:** brondata blijft in de parent `…/Running/` (Excel + `Garmin/ACTIVITY/*.fit`);
  álle output (verslag, `Weken/`, `charts/`, `runs.json`) wordt in de projectmap `claude coach/` geschreven.
- **Virtualenv:** `~/.venvs/garmin-coach` — bewust **buiten** de gedeelde map: HGFS ondersteunt
  geen symlinks, dus een venv daar breekt (en OneDrive zou de venv onnodig syncen).
  Activeren: `source ~/.venvs/garmin-coach/bin/activate`. Herbouwen indien nodig:
  `python -m venv ~/.venvs/garmin-coach && pip install fitparse openpyxl matplotlib anthropic pandas`.
- **Horloge syncen:** `claude coach/sync_garmin.sh` kopieert nieuwe `.fit` van de Garmin Fenix (MTP/gvfs)
  naar `…/Running/Garmin/ACTIVITY/` — precies waar de tool ze inleest.

## Wat dit project doet
Analyseert de volledige hardloophistorie (Excel-logboek 2001–2025 + Garmin Fenix `.fit`
2025–heden) en produceert **één** levend verslag met blessure-monitor, trainingszones,
een gedetailleerd plan en grafieken.

## Bestanden
| Bestand | Inhoud |
|---|---|
| `running_coach.py` | CLI-entrypoint |
| `coach/` | package: loader, metrics, zones, history, charts, coachnote, report |
| `coach/weekly.py` | **weekrapport-generator** — één bestand per ISO-week |
| `runs.json` | cache van alle ingelezen lopen |
| `claude coach/Analyse_Looptraining.md` | **het verslag** (auto + handmatig logboek) |
| `claude coach/Weken/2026-Wxx.md` | **per-week** analyse + schema komende week (coach-blok blijft behouden) |
| `claude coach/charts/*.png` | grafieken |

## Hoe ik na nieuwe trainingen opnieuw advies vraag
1. Zorg dat het horloge gesynct is (nieuwe `.fit` in `Garmin/ACTIVITY/`).
2. Draai opnieuw:
   ```bash
   cd "/mnt/hgfs/D/OneDrive/Running/claude coach" && source ~/.venvs/garmin-coach/bin/activate
   python running_coach.py            # ververst verslag + grafieken + weekbestand
   python running_coach.py --coach    # + AI-weeknotitie (vereist ANTHROPIC_API_KEY)
   python running_coach.py --weeks-all  # (her)genereer alle historische weekbestanden
   ```
3. Het verslag herberekent status (ACWR/CTL/ATL/TSB), zones, richttempo's en het
   6-wekenschema op basis van de nieuwste data. **Het logboek blijft behouden.**
   Daarnaast wordt het weekbestand `claude/Weken/<jaar>-W<week>.md` (her)geschreven met
   de analyse van die week + schema voor de week erna; de **coach-analyse** in dat bestand
   blijft behouden tussen de `COACH-ANALYSE`-markers.
4. Vraag Claude gerust om interpretatie: _"lees Analyse_Looptraining.md en geef advies voor
   de komende weken"_ — of laat de `--coach` notitie het automatisch doen.

## Belangrijkste bevinding (vasthouden over sessies heen)
Terugkerende **crash-cyclus**: opbouwen tot ~200 km/maand → blessure → maandenlang stil.
Prioriteit = consistentie/blessurevrij boven pieken. Plafond voorlopig ~40–45 km/week,
elke 4e week terugloop, 2× kracht/week. Huidige status (jun 2026): ACWR 0,95 🟢, gezond.

## Mogelijke volgende stappen
- AI-weeknotitie activeren (`ANTHROPIC_API_KEY` zetten).
- Wekelijkse automatische verversing via `/loop` of een scheduled agent.
- Voortgang van het 6-wekenschema evalueren zodra het logboek gevuld is.

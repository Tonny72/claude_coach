# MEMORY — Running-coach (context die over sessies heen blijft)

_Laatst bijgewerkt: 2026-06-14. Dit bestand vat de duurzame context samen zodat Claude
als persoonlijke trainingscoach niet telkens opnieuw hoeft te beginnen. Werk het bij
zodra er iets structureels verandert._

## Atleet
- ~54 jaar (geboortejaar 1972), rust-HS ~52, HRmax-model ~176.
- Loopt sinds 2001; carrière ±21.300 km / 1.706 lopen. Gouden jaren 2001–2005 (10 km 32:42,
  halve 1:04:34), marathon 3:11 in 2014. Nu rustig & consistent (~6:00–6:30/km, HS 130–141).
- **Grootste valkuil = de crash-cyclus** (niet snelheid): agressief opbouwen → blessure/burn-out
  → maandenlang stil. Laatste gat 188 d (2025-09-13 → 2026-03-20). Herstart 20-03-2026.

## Trainingsfilosofie (afgesproken)
- Consistentie > pieken. Doel: 12 maanden onafgebroken trainen.
- Plafond voorlopig **40–45 km/week** (historisch breekpunt ~50). Max +10% volume/week.
- Elke 4e week terugloop (−30%, ~28 km). 80% rustig / 20% intensief. Max 1 harde dag zolang CTL < ~40.
- **2× kracht/week** = dé blessurebuffer op deze leeftijd (kuit + heup belangrijkst).
- Easy écht easy: grijze zone HS 142–152 actief mijden op rustige dagen.
- Cadans-doel 168–172 (nu ~164–166) voor minder impact per stap.

## Status (eind W24, 14-06-2026)
- ACWR 0,95 🟢 · CTL 33 · ATL 49 · TSB −10. Gezond, lichte vermoeidheid, fitnessbasis nog dun.

## Werkwijze "Claude als wekelijkse coach"
1. Horloge koppelen → `bash sync_garmin.sh` kopieert nieuwe `.fit` naar `…/Running/Garmin/ACTIVITY/`.
2. Tool draaien (zie README): `python running_coach.py --cache` ververst charts + weekdocument
   (Claude doet dit voor je; jij hoeft alleen te syncen).
3. Vraag Claude "analyseer mijn nieuwe runs" zodra een week gelopen is.

**Eén document per week** in `Weken/`, **vooruit-benoemd naar de plan-week** die je gaat
trainen (bv. `2026-W25.md` = terugblik W24 + schema W25). **2 weken vooruit gepland:** de tool
maakt ook alvast het document voor de week daarna (bv. `2026-W26.md`, plan-only — terugblik/runs/
analyse vullen zich later vanzelf). Zelfstandig leesbaar, met:
1. Terugblik — runs van de vorige week · 2. Huidige status (CTL/ATL/TSB/ACWR) · 3. Actuele trainingszones ·
4. Trainingsschema deze week · 5. Coach-analyse (handmatig, blijft behouden tussen de markers —
hier zet Claude de uitgebreide per-run-analyse + gedetailleerde sessie-uitwerking).
Excel = bevroren historie; de weekdocumenten zijn het levende document.

## Paden (BELANGRIJK)
- **Projectmap / alle output:** `…/Running/claude coach/` (verslag, `Weken/`, `charts/`, `runs.json`).
- **Brondata (blijft in parent):** Excel `…/Running/Conditie verloop.xlsx` +
  Garmin `…/Running/Garmin/ACTIVITY/*.fit`.
- **Venv (buiten de map, want HGFS heeft geen symlinks):** `~/.venvs/garmin-coach`.
- Config: `coach/config.py` — outputs afgeleid van `PROJECT_DIR`, brondata van `RUNNING_DIR`.

## Laatst gedaan
- 2026-06-14: padwijziging `claude` → `claude coach` doorgevoerd in `config.py` (output nu in projectmap).
  `weekly.py` uitgebreid met sectie "Actuele trainingszones"; secties hernummerd (nu 5);
  documenten vooruit-benoemd naar de plan-week; 2 weken vooruit gepland (`build_plan_only`).
  Nu: `Weken/2026-W25.md` (terugblik W24 + schema/uitwerking W25) + `2026-W26.md` (vooruit, ~42 km interval).

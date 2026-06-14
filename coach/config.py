"""Centrale configuratie voor de running-coach tool."""
from pathlib import Path

# --- Bronpaden (blijven in de OneDrive Running-map) ---
RUNNING_DIR = Path("/mnt/hgfs/D/OneDrive/Running")
XLSX        = RUNNING_DIR / "Conditie verloop.xlsx"
ACT_DIR     = RUNNING_DIR / "Garmin" / "ACTIVITY"

# --- Uitvoer (ALLES in de projectmap zelf: .../Running/claude coach/) ---
PROJECT_DIR = Path(__file__).resolve().parent.parent
CHART_DIR   = PROJECT_DIR / "charts"
REPORT      = PROJECT_DIR / "Analyse_Looptraining.md"   # één samengevoegd verslag
WEEK_DIR    = PROJECT_DIR / "Weken"                     # één markdown-bestand per ISO-week
CACHE_JSON  = PROJECT_DIR / "runs.json"

# Markers waarbinnen het handmatig ingevulde logboek bij elke verversing behouden blijft
LOG_START   = "<!-- LOGBOEK:START — alles tussen deze markers blijft behouden -->"
LOG_END     = "<!-- LOGBOEK:END -->"
# Markers in een weekbestand waarbinnen de handmatige coach-analyse behouden blijft
WK_START    = "<!-- COACH-ANALYSE:START — handmatig, blijft behouden bij verversen -->"
WK_END      = "<!-- COACH-ANALYSE:END -->"

# --- Atleet ---
BIRTH_YEAR  = 1972          # ~54 in 2026
HR_REST     = 52
# Leeftijdsafhankelijke HRmax (Nes 2013): 211 - 0.64*leeftijd
def hr_max_for_year(year: int) -> float:
    age = year - BIRTH_YEAR
    return 211 - 0.64 * age

# --- Belastingsmodel ---
CTL_TAU = 42                # chronische belasting (fitness) tijdsconstante in dagen
ATL_TAU = 7                 # acute belasting (vermoeidheid)
ACWR_ACUTE = 7              # dagen
ACWR_CHRONIC = 28           # dagen

# ACWR risicozones
ACWR_SWEET = (0.8, 1.3)     # optimaal
ACWR_DANGER = 1.5           # hoog blessurerisico erboven

# --- Claude coach-laag ---
COACH_MODEL = "claude-sonnet-4-6"   # weeknotitie; 'claude-opus-4-8' voor diepere analyse
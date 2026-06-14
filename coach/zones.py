"""Leidt actuele HS-zones (Karvonen) en richttempo's af uit recente data."""
import datetime
from . import config


def hr_zones(year):
    """Karvonen-zones op basis van leeftijds-HRmax en rust-HS."""
    hrmax = config.hr_max_for_year(year)
    rest = config.HR_REST
    def hr(p):
        return round(rest + p * (hrmax - rest))
    # %HS-reserve (Karvonen). Geijkt op zijn werkelijke rustige lopen (HS 130-140 = 60-72%).
    return {
        "herstel":   (hr(0.50), hr(0.60)),
        "rustig":    (hr(0.60), hr(0.72)),   # Z2 - basis
        "matig":     (hr(0.72), hr(0.80)),   # grijze zone - vermijden
        "drempel":   (hr(0.80), hr(0.88)),   # tempo
        "interval":  (hr(0.88), hr(0.95)),   # VO2max
    }


def _fmt(sec):
    return f"{int(sec // 60)}:{int(sec % 60):02d}"


def threshold_pace(runs, days=150):
    """Schat huidig drempeltempo: snelste degelijke inspanning (>=5 km) recent."""
    cutoff = runs[-1].d - datetime.timedelta(days=days)
    recent = [r for r in runs if r.d >= cutoff and r.dist >= 5]
    if not recent:
        recent = [r for r in runs[-20:] if r.dist >= 5] or runs[-20:]
    # snelste tempo onder de recente inspanningen ~ drempel/10k-tempo
    best = min(recent, key=lambda r: r.pace)
    return best.pace, best.d


def easy_pace(runs, zones, year, days=120):
    """Mediaan tempo van recente aerobe (Z2) lopen."""
    cutoff = runs[-1].d - datetime.timedelta(days=days)
    lo, hi = zones["rustig"]
    cand = [r.pace for r in runs if r.d >= cutoff and r.hr and lo - 5 <= r.hr <= hi + 3]
    if not cand:
        cand = [r.pace for r in runs[-15:]]
    cand.sort()
    return cand[len(cand) // 2]


def pace_targets(runs, year):
    """Richttempo's per trainingstype (s/km) afgeleid van drempel + aerobe data."""
    thr, thr_date = threshold_pace(runs)
    z = hr_zones(year)
    easy = easy_pace(runs, z, year)
    return {
        "_threshold_date": thr_date,
        "herstel":   (easy + 25, easy + 50),
        "rustig":    (easy - 5, easy + 25),
        "lange":     (easy, easy + 35),
        "drempel":   (thr, thr + 15),
        "interval":  (thr - 18, thr - 3),
        "strides":   (thr - 60, thr - 35),
    }, thr, thr_date


def fmt_range(lo_hi):
    lo, hi = lo_hi
    return f"{_fmt(lo)}–{_fmt(hi)}"

"""Sportwetenschappelijke belastings- en fitheidsmetrieken.

Geen black-box ML, maar gevestigde modellen:
- TRIMP (Banister)            : trainingsbelasting per loop uit HS-reserve
- CTL / ATL / TSB             : fitness / vermoeidheid / vorm (impulse-respons)
- ACWR                        : acuut:chronisch verhouding -> blessurerisico
- Efficiency Factor (EF)      : snelheid per hartslag -> aerobe vorm
"""
import math, datetime
from collections import defaultdict

from . import config


# ---------------------------------------------------------------- TRIMP
def trimp(run) -> float:
    """Banister TRIMP voor een loop. Valt terug op matige intensiteit zonder HS."""
    dur_min = run.sec / 60.0
    hrmax = config.hr_max_for_year(run.d.year)
    if run.hr:
        hrr = (run.hr - config.HR_REST) / (hrmax - config.HR_REST)
    else:
        hrr = 0.70  # aanname: rustige-matige duurloop
    hrr = min(max(hrr, 0.0), 1.0)
    return dur_min * hrr * 0.64 * math.exp(1.92 * hrr)


# ---------------------------------------------------------------- daglast-reeks
def daily_load(runs, metric="trimp"):
    """Dict date->last over de volledige kalender (rustdagen = 0)."""
    if not runs:
        return {}
    per_day = defaultdict(float)
    for r in runs:
        per_day[r.d] += trimp(r) if metric == "trimp" else r.dist
    start, end = runs[0].d, runs[-1].d
    days = (end - start).days
    return {start + datetime.timedelta(d): per_day.get(start + datetime.timedelta(d), 0.0)
            for d in range(days + 1)}


# ---------------------------------------------------------------- CTL/ATL/TSB
def fitness_series(runs):
    """Geeft lijst (date, ctl, atl, tsb) over de volledige historie."""
    load = daily_load(runs, "trimp")
    if not load:
        return []
    dates = sorted(load)
    ctl = atl = 0.0
    out = []
    for dt in dates:
        l = load[dt]
        # TSB = vorm van gisteren (vóór de last van vandaag)
        tsb = ctl - atl
        ctl += (l - ctl) / config.CTL_TAU
        atl += (l - atl) / config.ATL_TAU
        out.append((dt, ctl, atl, tsb))
    return out


# ---------------------------------------------------------------- ACWR
def acwr_series(runs, metric="trimp"):
    """Rollend acuut(7d-gem):chronisch(28d-gem). Lijst (date, acwr, acute, chronic)."""
    load = daily_load(runs, metric)
    if not load:
        return []
    dates = sorted(load)
    vals = [load[d] for d in dates]
    a, c = config.ACWR_ACUTE, config.ACWR_CHRONIC
    out = []
    for i, dt in enumerate(dates):
        if i < c:
            continue
        acute = sum(vals[i - a + 1:i + 1]) / a
        chronic = sum(vals[i - c + 1:i + 1]) / c
        if chronic > 0:
            out.append((dt, acute / chronic, acute, chronic))
    return out


# ---------------------------------------------------------------- Efficiency
def efficiency_factor(run):
    """Genormaliseerde snelheid (m/min) per hartslag. Hoger = fitter."""
    if not run.hr:
        return None
    speed_m_min = (run.dist * 1000) / (run.sec / 60.0)
    return speed_m_min / run.hr


# ---------------------------------------------------------------- weeksamenvatting
def weekly_summary(runs, weeks=8):
    """Laatste N ISO-weken: km, aantal, gem HS, belasting."""
    wk = defaultdict(lambda: {"km": 0.0, "n": 0, "load": 0.0, "hr": [], "sec": 0.0})
    for r in runs:
        iso = r.d.isocalendar()
        key = (iso[0], iso[1])
        w = wk[key]
        w["km"] += r.dist
        w["n"] += 1
        w["sec"] += r.sec
        w["load"] += trimp(r)
        if r.hr:
            w["hr"].append(r.hr)
    keys = sorted(wk)[-weeks:]
    rows = []
    for k in keys:
        w = wk[k]
        rows.append({
            "year": k[0], "week": k[1], "km": round(w["km"], 1), "runs": w["n"],
            "load": round(w["load"]), "hours": round(w["sec"] / 3600, 1),
            "avg_hr": round(sum(w["hr"]) / len(w["hr"])) if w["hr"] else None,
        })
    return rows


def acwr_flag(acwr: float) -> str:
    lo, hi = config.ACWR_SWEET
    if acwr > config.ACWR_DANGER:
        return "HOOG RISICO"
    if acwr > hi:
        return "verhoogd"
    if acwr < lo:
        return "laag/detraining"
    return "optimaal"

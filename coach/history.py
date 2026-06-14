"""Historische cijfers uit de volledige loophistorie (voor het verslag)."""
import datetime
from collections import defaultdict


def career_totals(runs):
    km = sum(r.dist for r in runs)
    hours = sum(r.sec for r in runs) / 3600
    return {"runs": len(runs), "km": km, "hours": hours,
            "first": runs[0].d, "last": runs[-1].d}


def per_year(runs):
    yr = defaultdict(list)
    for r in runs:
        yr[r.d.year].append(r)
    rows = []
    for y in sorted(yr):
        rs = yr[y]
        km = sum(r.dist for r in rs)
        avg_pace = sum(r.sec for r in rs) / sum(r.dist for r in rs)
        hrs = [r.hr for r in rs if r.hr]
        longish = [r.pace for r in rs if r.dist >= 5] or [r.pace for r in rs]
        rows.append({"year": y, "runs": len(rs), "km": km,
                     "avg_pace": avg_pace, "avg_hr": sum(hrs) / len(hrs) if hrs else None,
                     "fastest": min(longish)})
    return rows


def prs(runs):
    bands = [(4.5, 5.5, "≈ 5 km"), (8, 11, "≈ 10 km"),
             (18, 22, "≈ halve (20 km)"), (40, 44, "marathon")]
    out = []
    for lo, hi, lbl in bands:
        cand = [r for r in runs if lo <= r.dist <= hi]
        if not cand:
            continue
        best = min(cand, key=lambda r: r.pace)
        out.append({"label": lbl, "run": best})
    return out


def longest(runs, n=5):
    return sorted(runs, key=lambda r: -r.dist)[:n]


def crash_months(runs, peak=150, drop=0.6):
    """Maanden >peak km gevolgd door een inzinking <drop*piek."""
    mo = defaultdict(float)
    for r in runs:
        mo[(r.d.year, r.d.month)] += r.dist
    keys = sorted(mo)
    out = []
    for i, k in enumerate(keys[:-1]):
        after = [mo[j] for j in keys[i + 1:i + 3]]
        if not (mo[k] > peak and after and after[0] < drop * mo[k]):
            continue
        # alleen een ÉCHTE inzinking: ook het 2-maands-gemiddelde erna blijft laag
        if sum(after) / len(after) < drop * mo[k]:
            out.append({"month": f"{k[0]}-{k[1]:02d}", "km": mo[k], "after": after})
    return out


def big_gaps(runs, min_days=60):
    out = []
    prev = None
    for r in runs:
        if prev:
            gap = (r.d - prev).days
            if gap >= min_days:
                out.append({"days": gap, "from": prev, "to": r.d})
        prev = r.d
    return out


def max_hr_per_year(runs):
    mx = defaultdict(list)
    for r in runs:
        if r.mx:
            mx[r.d.year].append(r.mx)
    return {y: max(v) for y, v in sorted(mx.items())}

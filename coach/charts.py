"""Genereert PNG-grafieken uit de loopdata."""
import datetime
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from . import config, metrics

plt.rcParams.update({"figure.autolayout": True, "axes.grid": True,
                     "grid.alpha": 0.3, "font.size": 10})


def _save(fig, name):
    config.CHART_DIR.mkdir(parents=True, exist_ok=True)
    path = config.CHART_DIR / name
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return name


def chart_monthly_volume(runs):
    """Maandvolume met crash-maanden (>40% daling na >150 km) rood."""
    mo = defaultdict(float)
    for r in runs:
        mo[(r.d.year, r.d.month)] += r.dist
    keys = sorted(mo)
    x = [datetime.date(y, m, 1) for y, m in keys]
    vals = [mo[k] for k in keys]
    colors = []
    for i, k in enumerate(keys):
        crash = i > 0 and mo[keys[i - 1]] > 150 and mo[k] < 0.6 * mo[keys[i - 1]]
        colors.append("#c0392b" if crash else "#3498db")
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.bar(x, vals, width=20, color=colors)
    ax.set_title("Maandvolume (km) — rood = inzinking na piek (crash-cyclus)")
    ax.set_ylabel("km / maand")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    return _save(fig, "01_maandvolume.png")


def chart_efficiency(runs):
    """Jaarlijkse mediane Efficiency Factor + gemiddeld tempo."""
    ef_year = defaultdict(list)
    pace_year = defaultdict(list)
    for r in runs:
        ef = metrics.efficiency_factor(r)
        if ef and r.dist >= 4:
            ef_year[r.d.year].append(ef)
        pace_year[r.d.year].append(r.pace)
    yrs = sorted(ef_year)
    ef = [sorted(ef_year[y])[len(ef_year[y]) // 2] for y in yrs]
    pace = [sum(pace_year[y]) / len(pace_year[y]) / 60 for y in yrs]
    fig, ax1 = plt.subplots(figsize=(11, 4))
    ax1.plot(yrs, ef, "o-", color="#27ae60", label="Efficiency Factor (m/min per HS)")
    ax1.set_ylabel("Efficiency Factor", color="#27ae60")
    ax1.set_title("Aerobe efficiëntie & tempo per jaar (hoger EF = fitter)")
    ax2 = ax1.twinx()
    ax2.plot(yrs, pace, "s--", color="#e67e22", label="gem. tempo (min/km)")
    ax2.set_ylabel("min/km", color="#e67e22")
    ax2.invert_yaxis()
    ax2.grid(False)
    return _save(fig, "02_efficientie.png")


def chart_hrmax(runs):
    """Hoogst waargenomen HS per jaar vs leeftijdsmodel."""
    mx = defaultdict(list)
    for r in runs:
        if r.mx:
            mx[r.d.year].append(r.mx)
    yrs = sorted(mx)
    obs = [max(mx[y]) for y in yrs]
    pred = [config.hr_max_for_year(y) for y in yrs]
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(yrs, obs, "o-", color="#c0392b", label="hoogst gemeten")
    ax.plot(yrs, pred, "--", color="#7f8c8d", label="leeftijdsmodel 211−0,64·leeftijd")
    ax.set_title("Maximale hartslag over de jaren")
    ax.set_ylabel("HS")
    ax.legend()
    return _save(fig, "03_maxhartslag.png")


def chart_fitness(runs, months=24):
    """CTL/ATL/TSB van de laatste N maanden."""
    series = metrics.fitness_series(runs)
    if not series:
        return None
    cutoff = series[-1][0] - datetime.timedelta(days=months * 30)
    series = [s for s in series if s[0] >= cutoff]
    dts = [s[0] for s in series]
    ctl = [s[1] for s in series]
    atl = [s[2] for s in series]
    tsb = [s[3] for s in series]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 6), sharex=True,
                                   gridspec_kw={"height_ratios": [2, 1]})
    ax1.plot(dts, ctl, color="#2980b9", label="CTL (fitness)")
    ax1.plot(dts, atl, color="#e67e22", label="ATL (vermoeidheid)")
    ax1.fill_between(dts, ctl, alpha=0.1, color="#2980b9")
    ax1.set_title("Fitness (CTL) · Vermoeidheid (ATL) · Vorm (TSB)")
    ax1.legend(loc="upper left")
    ax2.fill_between(dts, tsb, 0, where=[t >= 0 for t in tsb], color="#27ae60", alpha=0.5)
    ax2.fill_between(dts, tsb, 0, where=[t < 0 for t in tsb], color="#c0392b", alpha=0.5)
    ax2.axhline(0, color="k", lw=0.6)
    ax2.set_ylabel("TSB (vorm)")
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    return _save(fig, "04_fitness_ctl_atl_tsb.png")


def chart_acwr(runs, months=18):
    """ACWR met risicozones, laatste N maanden."""
    series = metrics.acwr_series(runs)
    if not series:
        return None
    cutoff = series[-1][0] - datetime.timedelta(days=months * 30)
    series = [s for s in series if s[0] >= cutoff]
    dts = [s[0] for s in series]
    acwr = [s[1] for s in series]
    fig, ax = plt.subplots(figsize=(11, 4))
    lo, hi = config.ACWR_SWEET
    ax.axhspan(lo, hi, color="#27ae60", alpha=0.15, label="optimaal 0,8–1,3")
    ax.axhspan(hi, config.ACWR_DANGER, color="#f1c40f", alpha=0.15, label="verhoogd")
    ax.axhspan(config.ACWR_DANGER, max(2.0, max(acwr) + 0.1), color="#c0392b",
               alpha=0.15, label="hoog risico >1,5")
    ax.plot(dts, acwr, color="#34495e")
    ax.set_title("ACWR — acuut:chronische belasting (blessurerisico)")
    ax.set_ylabel("ACWR")
    ax.legend(loc="upper left", fontsize=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    return _save(fig, "05_acwr.png")


def chart_pace_hr_zones(runs, year=None):
    """Pace vs HS spreidingsdiagram (recent jaar), met zonegrenzen."""
    if year is None:
        year = runs[-1].d.year
    pts = [(r.hr, r.pace / 60) for r in runs if r.hr and r.d.year == year and r.dist >= 3]
    if not pts:
        return None
    hrs, paces = zip(*pts)
    hrmax = config.hr_max_for_year(year)
    z2 = config.HR_REST + 0.70 * (hrmax - config.HR_REST)
    z4 = config.HR_REST + 0.88 * (hrmax - config.HR_REST)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.axvspan(0, z2, color="#27ae60", alpha=0.10)
    ax.axvspan(z2, z4, color="#f1c40f", alpha=0.10)
    ax.axvspan(z4, 200, color="#c0392b", alpha=0.10)
    ax.scatter(hrs, paces, alpha=0.6, color="#2980b9")
    ax.axvline(z2, ls="--", color="#27ae60")
    ax.axvline(z4, ls="--", color="#c0392b")
    ax.set_xlim(min(hrs) - 5, max(hrs) + 5)
    ax.invert_yaxis()
    ax.set_xlabel("gem. hartslag")
    ax.set_ylabel("tempo (min/km)")
    ax.set_title(f"Tempo vs hartslag {year} — groen=Z2, geel=grijze zone, rood=drempel+")
    return _save(fig, "06_pace_vs_hr.png")


def _smooth_pace(speed_ms, w=8):
    """Mediaan-gefilterd tempo (s/km) uit de speed-stroom; None waar stilstand/ontbreekt."""
    import statistics
    raw = [(1000.0 / v) if (v and v > 0.5) else None for v in speed_ms]
    out = []
    for i in range(len(raw)):
        seg = [v for v in raw[max(0, i - w):i + w + 1] if v is not None]
        out.append(statistics.median(seg) if seg else None)
    return out


def _work_blocks(elapsed_s, pace_s, hr, dist_m, threshold=330, min_dur=60):
    """Detecteer werkblokken (tempo < `threshold` s/km, > `min_dur` s) als analyse-segmenten."""
    blocks, cur = [], None
    for i, p in enumerate(pace_s):
        work = p is not None and p < threshold
        if cur is None or cur["work"] != work:
            if cur:
                blocks.append(cur)
            cur = {"work": work, "i0": i, "i1": i}
        else:
            cur["i1"] = i
    if cur:
        blocks.append(cur)
    out = []
    for b in blocks:
        dur = elapsed_s[b["i1"]] - elapsed_s[b["i0"]]
        if not b["work"] or dur < min_dur:
            continue
        ps = [p for p in pace_s[b["i0"]:b["i1"] + 1] if p]
        hrs = [h for h in hr[b["i0"]:b["i1"] + 1] if h]
        out.append({
            "t0": elapsed_s[b["i0"]] / 60, "t1": elapsed_s[b["i1"]] / 60,
            "dur": dur, "dist": (dist_m[b["i1"]] or 0) - (dist_m[b["i0"]] or 0),
            "pace": sum(ps) / len(ps) if ps else None,
            "hr_avg": round(sum(hrs) / len(hrs)) if hrs else None,
            "hr_peak": max(hrs) if hrs else None,
        })
    return out


def chart_workout_vs_plan(stream, plan, name, title):
    """Uitgevoerde kwaliteitssessie (tempo + HS over tijd) tegen het geplande doel.

    `stream` = dict uit db.run_stream; `plan` = {pace_lo, pace_hi, hr_lo, hr_hi, reps, minutes}
    (tempo-grenzen in s/km). Tekent het geplande doelvenster als groene band en markeert de
    gedetecteerde werkblokken. Geeft de bestandsnaam terug (in CHART_DIR).
    """
    t = [e / 60 for e in stream["elapsed_s"]]
    pace_s = _smooth_pace(stream["speed_ms"])
    pace_min = [p / 60 if p else None for p in pace_s]
    blocks = _work_blocks(stream["elapsed_s"], pace_s, stream["hr"], stream["distance_m"])

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True,
                                   gridspec_kw={"height_ratios": [3, 2]})
    # --- tempo ---
    ax1.axhspan(plan["pace_lo"] / 60, plan["pace_hi"] / 60, color="#27ae60", alpha=0.18,
                label=f"gepland drempeltempo {_mmss(plan['pace_lo'])}–{_mmss(plan['pace_hi'])}/km "
                      f"({plan['reps']}×{plan['minutes']}′)")
    ax1.plot(t, pace_min, color="#2980b9", lw=0.7, label="uitgevoerd tempo")
    for n, b in enumerate(blocks, 1):
        ax1.axvspan(b["t0"], b["t1"], color="#2980b9", alpha=0.08)
        if b["pace"]:
            ax1.annotate(f"blok {n}\n{_mmss(b['pace'])}", (b["t0"] + (b["t1"] - b["t0"]) / 2, 4.55),
                         ha="center", va="top", fontsize=8, color="#21618c")
    ax1.set_ylabel("tempo (min/km)")
    ax1.set_ylim(8.2, 4.4)              # omgekeerd: sneller = boven
    ax1.set_title(title)
    ax1.legend(loc="lower right", fontsize=8)
    # --- hartslag ---
    ax2.axhspan(plan["hr_lo"], plan["hr_hi"], color="#27ae60", alpha=0.18,
                label=f"gepland HS-doel {plan['hr_lo']}–{plan['hr_hi']}")
    ax2.plot(t, stream["hr"], color="#c0392b", lw=0.7, label="uitgevoerde HS")
    for b in blocks:
        ax2.axvspan(b["t0"], b["t1"], color="#2980b9", alpha=0.08)
    ax2.set_ylabel("HS (bpm)")
    ax2.set_xlabel("tijd (min)")
    ax2.legend(loc="lower right", fontsize=8)
    return _save(fig, name)


def _mmss(sec):
    return f"{int(sec // 60)}:{int(round(sec % 60)):02d}"


def generate_all(runs):
    out = []
    for fn in (chart_monthly_volume, chart_efficiency, chart_hrmax,
               chart_fitness, chart_acwr, chart_pace_hr_zones):
        try:
            name = fn(runs)
            if name:
                out.append(name)
        except Exception as e:
            print(f"  grafiek {fn.__name__} mislukt: {e}")
    return out

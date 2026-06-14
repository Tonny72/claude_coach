"""Genereert ÉÉN markdown-bestand per ISO-week.

Elk weekbestand bevat:
  1. Analyse van de voorbije week (runs, splits, zoneverdeling, belasting, status)
  2. Trainingsschema voor de week erna (met richttempo + hartslag)

Een handmatige coach-analyse tussen de WK_START/WK_END-markers blijft behouden bij
elke verversing (zelfde principe als het logboek in het hoofdverslag).
"""
import datetime
import glob
from collections import defaultdict

from . import config, metrics, zones as Z

_WEEKDAY = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]
_WD_KORT = ["Ma", "Di", "Wo", "Do", "Vr", "Za", "Zo"]


# ---------------------------------------------------------------- helpers
def _pace(sec):
    return f"{int(sec // 60)}:{int(sec % 60):02d}"


def _fmt_hms(sec):
    sec = int(sec)
    h, m, s = sec // 3600, sec % 3600 // 60, sec % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def _hsr(hr, year):
    """Hartslagreserve-percentage (Karvonen)."""
    hrmax = config.hr_max_for_year(year)
    return (hr - config.HR_REST) / (hrmax - config.HR_REST)


def _zone_of(hr, year):
    """Naam van de HS-zone waarin een hartslag valt."""
    z = Z.hr_zones(year)
    for name in ("herstel", "rustig", "matig", "drempel", "interval"):
        lo, hi = z[name]
        if hr < hi:
            return name
    return "interval"


def _fit_paths(date):
    return sorted(glob.glob(str(config.ACT_DIR / f"{date.isoformat()}-*.fit")))


def _load_detail(date):
    """(session-dict, [lap-dicts]) voor de loop op die datum, of (None, [])."""
    try:
        from fitparse import FitFile
    except Exception:
        return None, []
    sess, laps = None, []
    for f in _fit_paths(date):
        try:
            ff = FitFile(f)
        except Exception:
            continue
        s = {}
        for m in ff.get_messages("session"):
            s = {x.name: x.value for x in m}
        if s.get("sport") != "running":
            continue
        sess = s
        for m in ff.get_messages("lap"):
            laps.append({x.name: x.value for x in m})
        break
    return sess, laps


def _classify(run, sess, laps, year):
    """Bepaal trainingstype uit hartslag, snelheidsvariatie en anaerobe TE."""
    mx = run.mx or (sess.get("max_heart_rate") if sess else None)
    anaer = (sess or {}).get("total_anaerobic_training_effect") or 0
    # snelheidsvariatie tussen volledige (>=0.8 km) laps wijst op intervallen
    lap_paces = [(l.get("total_timer_time") or 0) / ((l.get("total_distance") or 1) / 1000)
                 for l in laps if (l.get("total_distance") or 0) >= 800]
    spread = (max(lap_paces) - min(lap_paces)) if len(lap_paces) >= 3 else 0
    if anaer >= 1.5 or spread >= 60:
        return "🔴 Intervaltraining", "kwaliteit"
    if run.hr and _hsr(run.hr, year) >= 0.74:
        return "🟠 Tempo/drempel", "kwaliteit"
    if run.dist >= 14:
        return "🟢 Lange duurloop", "duur"
    if run.hr and _hsr(run.hr, year) < 0.62:
        return "🔵 Herstelloop", "herstel"
    return "🟢 Rustige duurloop", "duur"


def _week_runs(runs, iso):
    return [r for r in runs if r.d.isocalendar()[:2] == iso]


def _zone_distribution(week_runs, details, year):
    """Minuten per HS-zone over de week (geschat uit lap-gemiddelden)."""
    mins = defaultdict(float)
    for r in week_runs:
        _, laps = details.get(r.d, (None, []))
        if laps and any(l.get("avg_heart_rate") for l in laps):
            for l in laps:
                t = (l.get("total_timer_time") or 0) / 60.0
                hr = l.get("avg_heart_rate")
                if hr:
                    mins[_zone_of(hr, year)] += t
        elif r.hr:
            mins[_zone_of(r.hr, year)] += r.sec / 60.0
    return mins


# ---------------------------------------------------------------- analyse
def _run_table(week_runs, details, year):
    rows = []
    for r in sorted(week_runs, key=lambda x: x.d):
        sess, laps = details.get(r.d, (None, []))
        typ, _ = _classify(r, sess, laps, year)
        hsr = f"{_hsr(r.hr, year) * 100:.0f}%" if r.hr else "—"
        mx = r.mx or (sess.get("max_heart_rate") if sess else None)
        te = (sess or {}).get("total_training_effect")
        cad = (sess or {}).get("avg_running_cadence")
        cad_s = f"{cad * 2:.0f}" if cad else "—"     # beide benen
        rows.append(
            f"| {_WD_KORT[r.d.weekday()]} {r.d.strftime('%d-%m')} | {typ} | {r.dist:.1f} | "
            f"{_pace(r.pace)} | {r.hr or '—'} ({hsr}) | {mx or '—'} | {cad_s} | "
            f"{metrics.trimp(r):.0f} | {te or '—'} |")
    return ("| Dag | Type | km | Tempo | Gem HS | Max | Cadans | TRIMP | TE |\n"
            "|---|---|---|---|---|---|---|---|---|\n" + "\n".join(rows))


def _splits_block(week_runs, details):
    out = []
    for r in sorted(week_runs, key=lambda x: x.d):
        _, laps = details.get(r.d, (None, []))
        full = [l for l in laps if (l.get("total_distance") or 0) >= 300]
        if not full:
            continue
        parts = []
        for l in full:
            d = (l.get("total_distance") or 0) / 1000
            t = l.get("total_timer_time") or 0
            p = _pace(t / d) if d else "—"
            parts.append(f"{p}({l.get('avg_heart_rate') or '—'})")
        out.append(f"- **{_WD_KORT[r.d.weekday()]} {r.d.strftime('%d-%m')}** "
                   f"({r.dist:.1f} km): " + " · ".join(parts))
    if not out:
        return ""
    return ("\n### Splits per km — _tempo(HS)_\n\n" + "\n".join(out) + "\n")


def _zone_block(week_runs, details, year):
    mins = _zone_distribution(week_runs, details, year)
    total = sum(mins.values())
    if total <= 0:
        return ""
    order = [("herstel", "Herstel"), ("rustig", "Rustig (Z2)"),
             ("matig", "Matig (grijs)"), ("drempel", "Drempel"), ("interval", "Interval")]
    rows = []
    for key, label in order:
        m = mins.get(key, 0)
        if m <= 0:
            continue
        bar = "█" * max(1, round(20 * m / total))
        rows.append(f"| {label} | {m:.0f} | {100 * m / total:.0f}% | {bar} |")
    easy = (mins.get("herstel", 0) + mins.get("rustig", 0)) / total * 100
    grey = mins.get("matig", 0) / total * 100
    note = (f"\n**Intensiteitsverdeling:** {easy:.0f}% rustig/aeroob, "
            f"{100 - easy:.0f}% matig+intensief. ")
    note += ("Grijze zone verwaarloosbaar 👍" if grey < 8
             else f"⚠️ {grey:.0f}% in de grijze zone (142–152) — mijden op easy dagen.")
    return ("\n### Tijd per hartslagzone\n\n"
            "| Zone | Min | Aandeel | |\n|---|---|---|---|\n"
            + "\n".join(rows) + "\n" + note + "\n")


def _status_at(runs, iso):
    """CTL/ATL/TSB en ACWR op de laatste dag van de gevraagde week."""
    last = max(r.d for r in _week_runs(runs, iso))
    fit = [x for x in metrics.fitness_series(runs) if x[0] <= last]
    acwr = [x for x in metrics.acwr_series(runs) if x[0] <= last]
    ctl, atl, tsb = (fit[-1][1], fit[-1][2], fit[-1][3]) if fit else (0, 0, 0)
    a = acwr[-1][1] if acwr else None
    flag = metrics.acwr_flag(a) if a is not None else "—"
    icon = {"optimaal": "🟢", "verhoogd": "🟡", "HOOG RISICO": "🔴",
            "laag/detraining": "🔵"}.get(flag, "⚪")
    arow = f"| **ACWR** | **{a:.2f}** {icon} | {flag} |" if a is not None else "| ACWR | — | |"
    return (
        "| Indicator | Waarde | Betekenis |\n|---|---|---|\n"
        f"{arow}\n"
        f"| CTL (fitness) | {ctl:.0f} | rustig opbouwen is goed |\n"
        f"| ATL (vermoeidheid) | {atl:.0f} | |\n"
        f"| TSB (vorm) | {tsb:+.0f} | >0 fris · <−20 vermoeid |"
    ), (ctl, atl, tsb, a, flag)


def _auto_flags(week_runs, details, year, stat):
    """Data-gedreven observaties (geen black box)."""
    ctl, atl, tsb, a, flag = stat
    mins = _zone_distribution(week_runs, details, year)
    total = sum(mins.values()) or 1
    easy = (mins.get("herstel", 0) + mins.get("rustig", 0)) / total * 100
    grey = mins.get("matig", 0) / total * 100
    has_quality = any(_classify(r, *details.get(r.d, (None, [])), year)[1] == "kwaliteit"
                      for r in week_runs)
    cads = []
    for r in week_runs:
        s, _ = details.get(r.d, (None, []))
        c = (s or {}).get("avg_running_cadence")
        if c:
            cads.append(c * 2)
    out = []
    out.append(f"- **Intensiteitsverdeling {easy:.0f}/{100 - easy:.0f}** "
               + ("(mooi polair — easy is easy) ✅" if easy >= 75 else "→ houd minstens 80% rustig."))
    out.append("- **Kwaliteitsprikkel aanwezig** deze week ✅" if has_quality
               else "- **Geen kwaliteitssessie** — voeg er één toe als je fris bent.")
    if grey >= 8:
        out.append(f"- ⚠️ **{grey:.0f}% grijze zone** — historisch jouw valkuil; easy écht easy houden.")
    if cads:
        avg_cad = sum(cads) / len(cads)
        if avg_cad < 168:
            out.append(f"- **Cadans ~{avg_cad:.0f}/min** (aan de lage kant) → richt op 168–172 "
                       "voor minder impact per stap (blessurerem).")
        else:
            out.append(f"- **Cadans ~{avg_cad:.0f}/min** — prima.")
    if a is not None:
        out.append(f"- **ACWR {a:.2f} ({flag})** · TSB {tsb:+.0f} → "
                   + ("vorm fris, ruimte om door te bouwen." if tsb > -5
                      else "wat vermoeidheid in de benen; geen tweede harde dag stapelen."))
    return "\n".join(out)


# ---------------------------------------------------------------- actuele trainingszones
def _zones_block(runs, year):
    """Actuele HS-zones (Karvonen) + richttempo's, afgeleid uit recente data."""
    z = Z.hr_zones(year)
    targets, thr, thr_date = Z.pace_targets(runs, year)
    rng = Z.fmt_range
    def hr(name):
        lo, hi = z[name]
        return f"{lo}–{hi}"
    rows = [
        f"| Herstel | {hr('herstel')} | {rng(targets['herstel'])} |",
        f"| **Rustig (Z2 — basis)** | **{hr('rustig')}** | **{rng(targets['rustig'])}** |",
        f"| Matig (grijze zone — mijden) | {hr('matig')} | — |",
        f"| Lange duurloop | {hr('rustig')} | {rng(targets['lange'])} |",
        f"| **Drempel/tempo** | **{hr('drempel')}** | **{rng(targets['drempel'])}** |",
        f"| **Interval (VO2max)** | **{hr('interval')}** | **{rng(targets['interval'])}** (1000 m) |",
        f"| Strides (15 s) | — | {rng(targets['strides'])} |",
    ]
    note = (f"\n_Afgeleid uit je recente lopen (rust-HS {config.HR_REST}, HRmax-model "
            f"{config.hr_max_for_year(year):.0f}); drempeltempo geschat op **{Z._fmt(thr)}/km** "
            f"uit je beste recente inspanning op {thr_date.isoformat()}. Past zich automatisch aan._")
    return ("| Zone | Hartslag | Richttempo |\n|---|---|---|\n"
            + "\n".join(rows) + "\n" + note + "\n")


# ---------------------------------------------------------------- schema volgende week
def _next_plan(runs, year, this_km, had_interval):
    """7-daags schema voor de komende week met richttempo + HS."""
    targets, thr, _ = Z.pace_targets(runs, year)
    hz = Z.hr_zones(year)
    rng = Z.fmt_range
    hr_easy = f"{hz['rustig'][0]}–{hz['rustig'][1]}"
    hr_rec = f"<{hz['rustig'][0]}"
    hr_thr = f"{hz['drempel'][0]}–{hz['drempel'][1]}"
    hr_itv = f"{hz['interval'][0]}–{hz['interval'][1]}"

    # volumedoel: +10% op de voorbije week, plafond 42 km
    weeks = metrics.weekly_summary(runs, 3)
    rising = len(weeks) >= 3 and weeks[-1]["km"] >= weeks[-2]["km"] >= weeks[-3]["km"]
    if rising and this_km >= 40:
        target, deload = round(this_km * 0.7), True
    else:
        target, deload = min(round(this_km * 1.1), 42), False

    lang = max(12, min(16, round(target - 24)))
    # kwaliteit afwisselen t.o.v. afgelopen week
    if deload:
        q_title = "Terugloop — alleen 6× strides"
        q_detail = f"6× 15 s strides @ {rng(targets['strides'])}/km, volledige rust. Geen reps."
        q_km = 6
    elif had_interval:
        q_title = "Drempel/tempo 3×8′"
        q_detail = (f"Inlopen 2 km → **3 × 8′** @ {rng(targets['drempel'])}/km (HS {hr_thr}), "
                    f"2′ dribbel ertussen → 1,5 km uitlopen.")
        q_km = 9
    else:
        q_title = "Interval 5×1000 m"
        q_detail = (f"Inlopen 2,5 km + strides → **5 × 1000 m** @ {rng(targets['interval'])}/km "
                    f"(HS {hr_itv}), 2:30–3:00′ dribbel → 1,5 km uitlopen.")
        q_km = 9

    rust_km = max(4, round(target - lang - q_km - 10))
    plan = [
        ("Maandag", "Rust of kracht", "20–30′ kracht (squat/lunge/calf/romp) óf volledige rust.", 0),
        ("Dinsdag", "Rustige duurloop", f"~10 km @ {rng(targets['rustig'])}/km — HS {hr_easy}.", 10),
        ("Woensdag", "Kracht", "Krachttraining 25–30′ — dé blessurebuffer op 54 j.", 0),
        ("Donderdag", f"Herstelloop ~{rust_km} km",
         f"{rust_km} km heel rustig @ {rng(targets['herstel'])}/km — HS {hr_rec}, óf rust.", rust_km),
        ("Vrijdag", q_title, q_detail, q_km),
        ("Zaterdag", "Rust", "Volledige rustdag (min. 48 u tot de lange duurloop).", 0),
        ("Zondag", f"Lange duurloop ~{lang} km",
         f"{lang} km gelijkmatig @ {rng(targets['lange'])}/km — HS {hr_easy}. "
         "Laatste 2 km iets vlotter mag.", lang),
    ]
    body = "\n".join(f"| {p[0]} | **{p[1]}** | {p[2]} |" for p in plan)
    est = sum(p[3] for p in plan)
    head = (f"**Doelvolume: ~{target} km** "
            + ("(⬇️ terugloopweek — bewust minder) " if deload else "(+10%-regel) ")
            + f"· geschat schema ~{est} km · max één harde dag · 2× kracht.")
    md = head + "\n\n| Dag | Sessie | Detail |\n|---|---|---|\n" + body + "\n"
    quality = "deload" if deload else ("drempel" if had_interval else "interval")
    return md, target, quality


# ---------------------------------------------------------------- behoud handmatig blok
def _extract_coach(path):
    if path.exists():
        txt = path.read_text(encoding="utf-8")
        if config.WK_START in txt and config.WK_END in txt:
            inner = txt.split(config.WK_START, 1)[1].split(config.WK_END, 1)[0]
            return f"{config.WK_START}{inner}{config.WK_END}\n"
    return (f"{config.WK_START}\n\n_Nog geen handmatige analyse — vul hier aan of vraag "
            "Claude om een diepere coach-analyse. Dit blok blijft behouden bij verversen._\n\n"
            f"{config.WK_END}\n")


# ---------------------------------------------------------------- bouw één week
def build_week(runs, iso):
    """Bouw het document voor de week ná `iso`: terugblik op week `iso` + schema voor de
    plan-week erna. Het bestand heet naar de plan-week (bv. runs in W24 → `2026-W25.md`)."""
    week_runs = _week_runs(runs, iso)
    if not week_runs:
        return None
    year = week_runs[-1].d.year
    details = {r.d: _load_detail(r.d) for r in week_runs}

    monday = datetime.date.fromisocalendar(iso[0], iso[1], 1)
    sunday = monday + datetime.timedelta(days=6)
    km = sum(r.dist for r in week_runs)
    sec = sum(r.sec for r in week_runs)
    load = sum(metrics.trimp(r) for r in week_runs)
    hrs = [r.hr for r in week_runs if r.hr]
    had_interval = any(_classify(r, *details.get(r.d, (None, [])), year)[0].endswith("Intervaltraining")
                       for r in week_runs)

    status_tbl, stat = _status_at(runs, iso)
    # Het document wordt benoemd naar de week die je gáát trainen (plan-week) en bevat
    # de terugblik op de zojuist voltooide week (iso) + het schema voor die plan-week.
    plan_iso = (sunday + datetime.timedelta(days=1)).isocalendar()[:2]
    p_monday = datetime.date.fromisocalendar(plan_iso[0], plan_iso[1], 1)
    p_sunday = p_monday + datetime.timedelta(days=6)

    plan_md, _plan_target, _plan_quality = _next_plan(runs, year, km, had_interval)

    config.WEEK_DIR.mkdir(parents=True, exist_ok=True)
    path = config.WEEK_DIR / f"{plan_iso[0]}-W{plan_iso[1]:02d}.md"
    coach_block = _extract_coach(path)

    md = "\n".join([
        f"# Trainingsweek {plan_iso[0]}-W{plan_iso[1]:02d}  ·  "
        f"{p_monday.strftime('%d-%m')} → {p_sunday.strftime('%d-%m-%Y')}",
        "",
        f"> **Terugblik week {iso[0]}-W{iso[1]:02d}** ({monday.strftime('%d-%m')} → {sunday.strftime('%d-%m')}): "
        f"{len(week_runs)} runs · **{km:.1f} km** · {_fmt_hms(sec)} · "
        f"gem HS {round(sum(hrs) / len(hrs)) if hrs else '—'} · belasting {load:.0f} TRIMP",
        "> Eén document per week: terugblik op de vorige week + trainingsschema voor deze week. "
        "De coach-analyse onderaan blijft behouden bij verversen.",
        "",
        "---", "",
        f"## 1. Terugblik — de runs van week W{iso[1]:02d}", "",
        _run_table(week_runs, details, year),
        _splits_block(week_runs, details),
        _zone_block(week_runs, details, year),
        "---", "",
        "## 2. Huidige status & observaties", "",
        status_tbl, "",
        _auto_flags(week_runs, details, year, stat), "",
        "---", "",
        "## 3. Actuele trainingszones", "",
        _zones_block(runs, year),
        "---", "",
        f"## 4. Trainingsschema deze week ({plan_iso[0]}-W{plan_iso[1]:02d})", "",
        plan_md, "",
        "> Richttempo's passen zich automatisch aan je nieuwste data aan. Grijze zone "
        f"({Z.hr_zones(year)['matig'][0]}–{Z.hr_zones(year)['matig'][1]} HS) bewust mijden op easy dagen.",
        "", "---", "",
        "## 5. Coach-analyse (handmatig)", "",
        coach_block, "",
        "---",
        f"\n*Gegenereerd {datetime.date.today().isoformat()} · TRIMP/CTL/ATL/TSB/ACWR · "
        "`python running_coach.py`*", "",
    ])
    path.write_text(md, encoding="utf-8")
    return path


def build_plan_only(runs, year, plan_iso, prev_km, prev_had_interval):
    """Vooruitgepland document (alleen zones + schema) voor een week die nog moet komen.
    Terugblik, runs en analyse worden automatisch ingevuld zodra de voorgaande week
    gelopen is en `build_week` dit bestand opnieuw schrijft. Coach-blok blijft behouden."""
    p_monday = datetime.date.fromisocalendar(plan_iso[0], plan_iso[1], 1)
    p_sunday = p_monday + datetime.timedelta(days=6)
    plan_md, _t, _q = _next_plan(runs, year, prev_km, prev_had_interval)

    config.WEEK_DIR.mkdir(parents=True, exist_ok=True)
    path = config.WEEK_DIR / f"{plan_iso[0]}-W{plan_iso[1]:02d}.md"
    coach_block = _extract_coach(path)

    md = "\n".join([
        f"# Trainingsweek {plan_iso[0]}-W{plan_iso[1]:02d}  ·  "
        f"{p_monday.strftime('%d-%m')} → {p_sunday.strftime('%d-%m-%Y')}",
        "",
        "> 🔭 **Vooruitgepland** (2 weken vooruit). Terugblik op de vorige week + analyse van de "
        "runs volgen automatisch zodra die week gelopen is. Het volume is een projectie en kan nog schuiven.",
        "",
        "---", "",
        "## 1. Actuele trainingszones", "",
        _zones_block(runs, year),
        "---", "",
        f"## 2. Trainingsschema deze week ({plan_iso[0]}-W{plan_iso[1]:02d})", "",
        plan_md, "",
        "> Richttempo's passen zich automatisch aan je nieuwste data aan. Grijze zone "
        f"({Z.hr_zones(year)['matig'][0]}–{Z.hr_zones(year)['matig'][1]} HS) bewust mijden op easy dagen.",
        "", "---", "",
        "## 3. Coach-analyse (handmatig)", "",
        coach_block, "",
        "---",
        f"\n*Vooruitgepland {datetime.date.today().isoformat()} · `python running_coach.py`*", "",
    ])
    path.write_text(md, encoding="utf-8")
    return path


def build_latest(runs):
    """Bouw het document voor de komende week (terugblik + plan) én, 2 weken vooruit, een
    plan-only document voor de week daarna. Geeft de lijst met geschreven paden terug."""
    if not runs:
        return []
    iso = runs[-1].d.isocalendar()[:2]
    paths = [build_week(runs, iso)]

    # Plan van de eerstvolgende week bepalen om de week daarna op te baseren.
    year = runs[-1].d.year
    week_runs = _week_runs(runs, iso)
    details = {r.d: _load_detail(r.d) for r in week_runs}
    km0 = sum(r.dist for r in week_runs)
    had_itv0 = any(_classify(r, *details.get(r.d, (None, [])), year)[0].endswith("Intervaltraining")
                   for r in week_runs)
    _md, t1, q1 = _next_plan(runs, year, km0, had_itv0)

    # 2 weken vooruit: de week ná de plan-week van `iso`.
    sunday = datetime.date.fromisocalendar(iso[0], iso[1], 7)
    plan2_iso = (sunday + datetime.timedelta(days=8)).isocalendar()[:2]
    paths.append(build_plan_only(runs, year, plan2_iso,
                                 prev_km=t1, prev_had_interval=(q1 == "interval")))
    return paths
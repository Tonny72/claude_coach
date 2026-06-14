"""Bouwt ÉÉN samengevoegd verslag: historische analyse + live dashboard + plan + logboek.

Het logboek (handmatig ingevuld) blijft behouden tussen de markers uit config.
"""
import datetime

from . import config, metrics, history, zones as Z


def _fmt_hms(sec):
    sec = int(sec)
    h, m, s = sec // 3600, sec % 3600 // 60, sec % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def _pace(sec):
    return f"{int(sec // 60)}:{int(sec % 60):02d}"


# ---------------------------------------------------------------- secties
def _sec_career(runs):
    c = history.career_totals(runs)
    return (
        "## 0. Kerncijfers (carrière)\n\n"
        "| | |\n|---|---|\n"
        f"| Geregistreerde lopen | **{c['runs']:,}** |\n"
        f"| Totale afstand | **±{c['km']:,.0f} km** |\n"
        f"| Totale looptijd | **±{c['hours']:,.0f} uur** |\n"
        f"| Periode | {c['first']} → {c['last']} |\n"
        f"| Rust-HS (recent) | ~{config.HR_REST} |\n"
        f"| HRmax-model (leeftijd) | ~{config.hr_max_for_year(c['last'].year):.0f} |\n"
    ).replace(",", ".")


def _sec_history(runs):
    pr = history.prs(runs)
    pr_rows = "\n".join(
        f"| {p['label']} | {_fmt_hms(p['run'].sec)} | {_pace(p['run'].pace)}/km | "
        f"{p['run'].d} | {p['run'].hr or '—'} |" for p in pr)
    long_rows = "\n".join(
        f"| {r.d} | {r.dist:.1f} km | {_pace(r.pace)}/km | {r.hr or '—'} |"
        for r in history.longest(runs))
    return (
        "## 1. Wat je vroeger hebt gepresteerd\n\n"
        "**De gouden jaren 2001–2005 (leeftijd ~29–33).** Je absolute piek: "
        "2.200–3.300 km per jaar op een gemiddeld tempo van 4:00–4:30/km — voor élke training. "
        "In 2013–2014 kwam je sterk terug met opnieuw ~1.700 km/jaar en een marathon van 3:11. "
        "Nu (2025–2026) loop je rustiger (~6:00–6:30/km, HS 130–141, mooi aeroob) en heel consistent.\n\n"
        "**Persoonlijke records (uit de data):**\n\n"
        "| Afstand | Prestatie | Tempo | Datum | HS |\n|---|---|---|---|---|\n"
        f"{pr_rows}\n\n"
        "Een 10 km in 32:42 en een halve aan 3:20/km zijn prestaties op sterk regionaal niveau.\n\n"
        "**Langste lopen ooit:**\n\n"
        "| Datum | Afstand | Tempo | HS |\n|---|---|---|---|\n"
        f"{long_rows}\n"
    )


def _sec_mistakes(runs):
    crashes = history.crash_months(runs)
    crows = "\n".join(
        f"| {c['month']} | {c['km']:.0f} km | {' → '.join(f'{a:.0f}' for a in c['after'])} km |"
        for c in crashes[-8:])
    gaps = [g for g in history.big_gaps(runs, 120)]
    grow = ", ".join(f"**{g['days']} d** ({g['from']}→{g['to']})" for g in gaps[-5:])
    return (
        "## 2. Waar je vroeger fouten hebt gemaakt\n\n"
        "Eén patroon herhaalt zich al 20 jaar: **agressief opbouwen naar een piek "
        "(180–350 km/maand), dan instorten naar bijna nul — gevolgd door een lange pauze.** "
        "Het klassieke signatuur van overbelasting → blessure/burn-out → gedwongen rust.\n\n"
        "**Piekmaanden gevolgd door een inzinking (laatste 8):**\n\n"
        "| Piekmaand | Volume | Direct daarna |\n|---|---|---|\n"
        f"{crows}\n\n"
        f"De lange gaten bevestigen het: {grow} — telkens vlak ná een sterk blok.\n\n"
        "> **Dit is je grootste valkuil, niet je snelheid.** Je verliest steeds maandenlang "
        "fitheid omdat je over de rand gaat. Daarnaast: vroeger te vaak te hard "
        "(gem. HS 165–184 in 2001–2005) en zelden een bewuste terugloopweek.\n\n"
        "_Dataopmerking: enkele meetfouten (max-HS 245, tempo 15:37) zijn uit de analyse gefilterd._\n"
    )


def _status_block(runs):
    fit = metrics.fitness_series(runs)
    acwr = metrics.acwr_series(runs)
    ctl, atl, tsb = (fit[-1][1], fit[-1][2], fit[-1][3]) if fit else (0, 0, 0)
    a = acwr[-1][1] if acwr else None
    flag = metrics.acwr_flag(a) if a is not None else "—"
    icon = {"optimaal": "🟢", "verhoogd": "🟡", "HOOG RISICO": "🔴",
            "laag/detraining": "🔵"}.get(flag, "⚪")
    arow = (f"| **ACWR** (7d:28d) | **{a:.2f}** {icon} | {flag} |"
            if a is not None else "| ACWR | n.v.t. | |")
    return (
        "| Indicator | Waarde | Betekenis |\n|---|---|---|\n"
        f"{arow}\n"
        f"| CTL (fitness) | {ctl:.0f} | langzaam opbouwen is goed |\n"
        f"| ATL (vermoeidheid) | {atl:.0f} | |\n"
        f"| TSB (vorm) | {tsb:+.0f} | >0 fris, <−20 vermoeid |"
    )


def _weekly_table(runs):
    rows = metrics.weekly_summary(runs, weeks=8)
    body = "\n".join(
        f"| {r['year']}-W{r['week']:02d} | {r['runs']} | {r['km']} | {r['hours']} | "
        f"{r['avg_hr'] or '—'} | {r['load']} |" for r in rows)
    return ("| Week | Runs | km | Uur | Gem HS | Belasting (TRIMP) |\n"
            "|---|---|---|---|---|---|\n" + body)


def _sec_status(runs):
    return (
        "## 3. Huidige status (blessure-monitor)\n\n"
        f"{_status_block(runs)}\n\n"
        "**ACWR** = acute (7 d) ÷ chronische (28 d) belasting; optimaal 0,8–1,3, boven 1,5 "
        "sterk verhoogd blessurerisico. **TSB** = vorm (fitness − vermoeidheid).\n\n"
        "### Laatste 8 weken\n\n"
        f"{_weekly_table(runs)}\n"
    )


def _sec_zones(runs, year, targets, thr, thr_date):
    hz = Z.hr_zones(year)
    zt = "\n".join([
        f"| Herstel | {hz['herstel'][0]}–{hz['herstel'][1]} | {Z.fmt_range(targets['herstel'])} |",
        f"| **Rustig (Z2 — basis)** | **{hz['rustig'][0]}–{hz['rustig'][1]}** | **{Z.fmt_range(targets['rustig'])}** |",
        f"| Matig (grijze zone — mijden) | {hz['matig'][0]}–{hz['matig'][1]} | — |",
        f"| Lange duurloop | {hz['rustig'][0]}–{hz['rustig'][1]} | {Z.fmt_range(targets['lange'])} |",
        f"| **Drempel/tempo** | **{hz['drempel'][0]}–{hz['drempel'][1]}** | **{Z.fmt_range(targets['drempel'])}** |",
        f"| **Interval (VO2max)** | **{hz['interval'][0]}–{hz['interval'][1]}** | **{Z.fmt_range(targets['interval'])}** (1000 m) |",
        f"| Strides (15 s) | — | {Z.fmt_range(targets['strides'])} |",
    ])
    return (
        "## 4. Jouw actuele trainingszones\n\n"
        f"Afgeleid uit je recente data (rust-HS {config.HR_REST}, HRmax-model "
        f"{config.hr_max_for_year(year):.0f}, drempeltempo geschat op **{_pace(thr)}/km** "
        f"uit je beste recente inspanning op {thr_date}).\n\n"
        "| Zone | Hartslag | Richttempo |\n|---|---|---|\n"
        f"{zt}\n"
    )


def _sec_plan(runs, year, targets):
    hz = Z.hr_zones(year)
    rng = Z.fmt_range
    hr_easy = f"{hz['rustig'][0]}–{hz['rustig'][1]}"
    hr_thr = f"{hz['drempel'][0]}–{hz['drempel'][1]}"
    hr_itv = f"{hz['interval'][0]}–{hz['interval'][1]}"
    week = "\n".join([
        "| Ma | Rust of kracht (20–30′) |",
        f"| Di | Rustig 8 km @ {rng(targets['rustig'])} — HS {hr_easy} |",
        "| Wo | **Kwaliteit** (zie 6-wekenschema) |",
        f"| Do | Herstel 6–7 km @ {rng(targets['herstel'])} — HS <{hz['rustig'][0]}, óf rust |",
        "| Vr | Rust of kracht (20–30′) |",
        f"| Za | **Lange duurloop** @ {rng(targets['lange'])} — HS {hr_easy} |",
        f"| Zo | Rustig 8 km + 4–6× strides @ {rng(targets['strides'])} |",
    ])
    lng, thr, itv, strd = rng(targets['lange']), rng(targets['drempel']), rng(targets['interval']), rng(targets['strides'])
    plan_rows = [
        ("1", "35", f"13 km @ {lng} (HS {hr_easy})", f"4×1000 m @ {itv} (HS {hr_itv}), 2′ dribbel"),
        ("2", "38", f"14 km @ {lng} (HS {hr_easy})", f"20′ tempo @ {thr} (HS {hr_thr})"),
        ("3", "42", f"15 km @ {lng} (HS {hr_easy})", f"5×1000 m @ {itv} (HS {hr_itv}), 2′ dribbel"),
        ("**4 (terugloop)**", "**28**", f"12 km @ {lng} (HS {hr_easy})", f"alleen 6× strides @ {strd}"),
        ("5", "42", f"16 km @ {lng} (HS {hr_easy})", f"8×60 s heuvel stevig (HS {hr_itv})"),
        ("6", "45", f"17 km @ {lng} (HS {hr_easy})", f"25′ tempo @ {thr} (HS {hr_thr})"),
    ]
    plan = "\n".join(f"| {w[0]} | {w[1]} | {w[2]} | {w[3]} |" for w in plan_rows)
    return (
        "## 5. Wat je nu moet doen — presteren zónder blessure\n\n"
        "Doel: **de crash-cyclus doorbreken.** 12 maanden onafgebroken trainen verslaat altijd "
        "3 sterke maanden + 6 maanden uitval. Consistentie > pieken.\n\n"
        "**Spelregels:** max +10% volume/week · elke 4e week terugloop (−30%) · voorlopig plafond "
        "~40–45 km/week (jouw historische breekpunt lag rond 50) · 80% rustig / 20% intensief · "
        "**2× kracht/week** (dé blessurebuffer op 54 j) · min. 48 u tussen harde sessies.\n\n"
        "### Weekstructuur (met tempo + HS)\n\n"
        "| Dag | Sessie |\n|---|---|\n"
        f"{week}\n\n"
        "### Kwaliteit op woensdag — volledige sessie-opbouw\n\n"
        "Elke kwaliteitssessie = **opwarming → hoofddeel → cooldown** (totaal ±10 km). "
        "De opwarming en rust zijn op 54 j net zo belangrijk als de reps zelf.\n\n"
        "**Optie A — Intervallen (1000 m)**\n"
        f"- *Opwarming 12–15′:* rustig van ~7:00 → 6:15/km (HS tot ~130) + 3–4× 15 s strides @ {strd}.\n"
        f"- *Hoofddeel:* 1000 m @ {itv} — HS {hr_itv}, gelijkmatig (laatste rep = eerste rep). "
        "**Aantal: week 1 → 4×, week 3 → 5×, later 6×.** Voeg pas een rep toe als de vorige "
        "sessie goed voelde en de HS tussen reps netjes herstelde.\n"
        "- *Rust tussen reps:* **2:30–3:00 min** rustig dribbelen (~350 m @ 7:00–7:30/km); "
        "wacht tot HS onder ~135–140 zakt vóór de volgende. Zwaar? Rust 3:30.\n"
        "- *Cooldown 10′:* heel rustig uitlopen @ ~7:00/km tot HS ~110–120 + licht rekken.\n\n"
        f"**Optie B — Tempo/drempel:** opwarming als boven, dan 20–25′ aaneengesloten @ {thr} "
        f"(HS {hr_thr}), cooldown 10′.\n\n"
        "**Optie C — Heuvels:** opwarming, dan 8–10 × 60 s bergop stevig (HS "
        f"{hr_itv}), terug joggen als rust, cooldown 10′.\n\n"
        "> Vuistregel rust: bij 1000 m neem je ~50–60% van de reptijd als rust "
        "(rep ~4:50 → ~2:30–3:00 min).\n\n"
        "### Gedetailleerd 6-wekenschema\n\n"
        "| Week | Doel-km | Lange duurloop | Kwaliteitssessie (woensdag) |\n|---|---|---|---|\n"
        f"{plan}\n\n"
        "### Waarschuwingssignalen → terugschakelen\n"
        "- Rust-HS 's ochtends >58–60 → rustdag.\n"
        "- Gelijk tempo bij duidelijk hogere HS → onderherstel.\n"
        "- Beginnende zeurpijn (achillespees/knie/scheen) → **direct** 2–3 dagen rust. "
        "Historisch is dít het punt waarop je blokken crashten.\n"
    )


_WEEKDAY = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]


def _planned_detail(i, targets, hz):
    """Geeft (titel, geschatte_km, [detailregels]) voor een geplande weekdag."""
    rng = Z.fmt_range
    hr_easy = f"{hz['rustig'][0]}–{hz['rustig'][1]}"
    hr_itv = f"{hz['interval'][0]}–{hz['interval'][1]}"
    if i in (0, 4):
        return ("Rust of kracht · ~0 km", 0.0,
                ["20–30′ kracht: squats, lunges, calf raises, romp — óf volledige rustdag."])
    if i == 1:
        return ("Rustige duurloop · ~8 km", 8.0,
                [f"8 km gelijkmatig @ {rng(targets['rustig'])}/km — HS {hr_easy}."])
    if i == 2:
        return ("Intervaltraining · ~9 km", 9.0, [
            f"Opwarming: **2,5 km** (12–15′) rustig 7:00→6:15/km + 3–4× 15 s strides @ {rng(targets['strides'])}.",
            f"Hoofddeel: **4 × 1000 m** @ {rng(targets['interval'])}/km (HS {hr_itv}) = **4,0 km**.",
            "Rust: **3 ×** 2:30–3:00′ rustig dribbelen (~0,35 km/stuk) = **~1,0 km** — HS eerst onder ~140.",
            "Cooldown: **1,5 km** (10′) heel rustig @ ~7:00/km.",
        ])
    if i == 3:
        return ("Rust · ~0 km", 0.0,
                [f"Bij voorkeur rust (dag ná de intervallen). Fris en zin? Optioneel "
                 f"5 km heel rustig @ {rng(targets['herstel'])}/km — HS <{hz['rustig'][0]}."])
    if i == 5:
        return ("Lange duurloop · ~13 km", 13.0,
                [f"13 km gelijkmatig @ {rng(targets['lange'])}/km — HS {hr_easy}. "
                 "Laatste 2 km mag iets vlotter als het goed voelt."])
    return ("Rustig + strides · ~7 km", 7.0, [
        f"7 km rustig @ {rng(targets['rustig'])}/km — HS {hr_easy}.",
        f"Daarna 4–6 × 15 s strides @ {rng(targets['strides'])}/km met volledige rust.",
    ])


def _sec_agenda(runs, year, targets):
    """Concrete agenda van de huidige week (ma→zo): voorbije dagen = echte log, rest = gepland detail."""
    hz = Z.hr_zones(year)
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    by_day = {}
    for r in runs:
        by_day.setdefault(r.d, []).append(r)

    done_km = plan_km = 0.0
    blocks = []
    for i in range(7):
        d = monday + datetime.timedelta(days=i)
        head = f"**{_WEEKDAY[i]} {d.strftime('%d-%m')}**"
        if d == today:
            head += " 👉 _(vandaag)_"
        acts = by_day.get(d, [])
        if acts:
            r = max(acts, key=lambda x: x.dist)
            done_km += sum(a.dist for a in acts)
            mx = f"/{r.mx}" if r.mx else ""
            blocks.append(f"{head} — ✅ gelopen: **{r.dist:.1f} km** @ {_pace(r.pace)}/km "
                          f"(HS {r.hr or '—'}{mx})")
        elif d < today:
            blocks.append(f"{head} — rust / geen training")
        else:
            title, km, bullets = _planned_detail(i, targets, hz)
            plan_km += km
            lines = "\n".join(f"  - {b}" for b in bullets)
            blocks.append(f"{head} — {title}\n{lines}")

    total = done_km + plan_km
    warn = ""
    if total > 42:
        warn = ("\n\n> ⚠️ Het weektotaal loopt boven ~40 km. Je deed dinsdag al meer dan gepland — "
                "kort donderdag/zondag in of sla een dag over, om binnen de +10%-opbouwregel te blijven.")
    body = "\n\n".join(blocks)
    return (
        f"## 6. Agenda — deze week (ma {monday.strftime('%d-%m')} → zo "
        f"{(monday + datetime.timedelta(days=6)).strftime('%d-%m')})\n\n"
        "Voorbije dagen tonen je werkelijke training uit de data; vandaag en verder = gepland "
        "met km-schatting (zo kies je je parcours). Verschuift automatisch mee bij elke verversing.\n\n"
        f"{body}\n\n"
        f"**Weektotaal:** reeds gelopen **{done_km:.1f} km** · nog gepland **~{plan_km:.0f} km** "
        f"· samen ~{total:.0f} km (weekdoel 35–40 km)." + warn + "\n"
    )


def _default_logbook():
    return (
        "## 8. Logboek (vul zelf aan — blijft behouden bij verversen)\n\n"
        f"{config.LOG_START}\n\n"
        "> Na elke training aanvullen. Bij een nieuwe adviesronde herberekent de tool alles "
        "en blijft deze tabel staan.\n\n"
        "| Datum | Sessie | Km | Gem. HS | Gevoel (1–5) | Rust-HS | Pijn/opmerkingen |\n"
        "|---|---|---|---|---|---|---|\n"
        "| _2026-06-…_ | | | | | | |\n"
        "| | | | | | | |\n\n"
        f"{config.LOG_END}\n"
    )


def _extract_logbook():
    """Behoud bestaand logboek tussen de markers, anders een leeg sjabloon."""
    if config.REPORT.exists():
        txt = config.REPORT.read_text(encoding="utf-8")
        if config.LOG_START in txt and config.LOG_END in txt:
            inner = txt.split(config.LOG_START, 1)[1].split(config.LOG_END, 1)[0]
            return ("## 8. Logboek (vul zelf aan — blijft behouden bij verversen)\n\n"
                    f"{config.LOG_START}{inner}{config.LOG_END}\n")
    return _default_logbook()


# ---------------------------------------------------------------- hoofd
def build(runs, chart_names, coach_note):
    year = runs[-1].d.year
    targets, thr, thr_date = Z.pace_targets(runs, year)
    today = datetime.date.today().isoformat()
    logbook = _extract_logbook()        # vóór overschrijven uitlezen
    imgs = "\n\n".join(f"![{n}](charts/{n})" for n in chart_names)

    md = "\n".join([
        "# Looptraining — Analyse, Plan & Dashboard",
        "",
        f"> **Bijgewerkt:** {today} · **Atleet:** 54 j · **Lopen in analyse:** {len(runs)} "
        f"({runs[0].d}→{runs[-1].d})",
        "> Eén levend verslag. Verversen na nieuwe trainingen: `python running_coach.py` "
        "(of `--coach` voor de weeknotitie). Het logboek onderaan blijft behouden.",
        "",
        "---", "",
        _sec_career(runs), "", "---", "",
        _sec_history(runs), "", "---", "",
        _sec_mistakes(runs), "", "---", "",
        _sec_status(runs), "", "---", "",
        _sec_zones(runs, year, targets, thr, thr_date), "", "---", "",
        _sec_plan(runs, year, targets), "", "---", "",
        _sec_agenda(runs, year, targets), "", "---", "",
        "## 7. Coach-notitie van de week", "", coach_note, "", "---", "",
        logbook, "", "---", "",
        "## 9. Grafieken", "", imgs, "", "---", "",
        "*Berekend met TRIMP (Banister), CTL/ATL/TSB (impulse-respons) en ACWR. "
        "Zones en richttempo's passen zich automatisch aan je nieuwste lopen aan.*", "",
    ])
    config.REPORT.write_text(md, encoding="utf-8")
    return config.REPORT

"""Optionele Claude-API laag: schrijft een wekelijkse coach-notitie uit de metrieken."""
import json, os

from . import config, metrics


SYSTEM = """Je bent een ervaren hardloopcoach gespecialiseerd in masters-atleten (50+).
Je schrijft beknopt, concreet en in het Nederlands. De atleet is 54 jaar en heeft een
historie van 'opbouwen-tot-blessure-dan-maanden-stil'. Je hoogste prioriteit is
blessurepreventie en consistentie, daarna prestatie. Gebruik de meegeleverde cijfers
(ACWR, CTL/ATL/TSB, weekvolume). Geef: (1) korte stand van zaken, (2) 1-2 concrete
aandachtspunten/waarschuwingen, (3) advies voor de komende week. Max ~200 woorden.
Verwijs naar getallen waar relevant. Geen disclaimers."""


def build_context(runs) -> dict:
    weeks = metrics.weekly_summary(runs, weeks=6)
    fit = metrics.fitness_series(runs)
    acwr = metrics.acwr_series(runs)
    ctx = {
        "laatste_loop": runs[-1].d.isoformat(),
        "weken": weeks,
        "fitness_ctl": round(fit[-1][1], 1) if fit else None,
        "vermoeidheid_atl": round(fit[-1][2], 1) if fit else None,
        "vorm_tsb": round(fit[-1][3], 1) if fit else None,
        "acwr": round(acwr[-1][1], 2) if acwr else None,
        "acwr_status": metrics.acwr_flag(acwr[-1][1]) if acwr else None,
    }
    return ctx


def weekly_note(runs, model=None) -> str:
    """Roept Claude aan voor een weeknotitie. Vereist ANTHROPIC_API_KEY."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return ("_(Claude coach-laag overgeslagen: zet ANTHROPIC_API_KEY om automatische "
                "weeknotities te genereren.)_")
    import anthropic
    ctx = build_context(runs)
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=model or config.COACH_MODEL,
        max_tokens=600,
        system=SYSTEM,
        messages=[{"role": "user", "content":
                   "Hier zijn mijn recente trainingscijfers (JSON). Schrijf de weeknotitie.\n\n"
                   + json.dumps(ctx, ensure_ascii=False, indent=2)}],
    )
    return msg.content[0].text.strip()

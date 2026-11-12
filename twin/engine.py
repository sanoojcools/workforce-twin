"""Simulate a policy on the synthetic workforce, then score it against the published outcome.

    run(case_id, clients) -> dict with voices, forecast, subgroups, briefing, score
"""
import os, random
from concurrent.futures import ThreadPoolExecutor
from .cases import CASES
from .llm import OfflineClient, parse_json
from .population import cells, headcount, voices

PERSONA_SYSTEM = """You are role-playing one specific employee, reacting privately to a policy announcement at work.
Answer as this person would in real life, not as an HR analyst or a survey respondent trying to please.
Your own situation (commute, family, career stage, options elsewhere) matters more than general opinions.
People rarely quit over one policy; many shrug. Be realistic about how big the effect is for you.

Reply with only JSON:
{"leave_pct_if_no_change": <0-100, chance you leave this employer in the next 12 months if nothing changes>,
 "leave_pct_with_policy": <0-100, the same chance if this policy goes ahead>,
 "feeling": <-2 very negative .. 2 very positive>,
 "quote": "<what you would honestly tell a close colleague about it, 1-2 sentences, in your own voice>",
 "top_factor": "<the one thing that drives your reaction, 2-5 words>"}"""

# v2 adds a say-do check. v1 personas reacted to takeaways the way people talk in an exit survey,
# not the way they act: the first live backtest overstated the RTO effect about 15x (see docs/).
SAY_DO = """
Before you give numbers, separate what you would SAY from what you would DO. Feeling angry is not the same as
leaving. Actually leaving means months of searching, interviews, finding an offer that is clearly better,
and giving up tenure, unvested pay, your network and a known manager. Plenty of people complain loudly and stay;
some quietly comply; a few were already leaving anyway. Your numbers must describe what you would actually do."""

# v3 adds the outside view: think about 100 people in your exact situation, not just yourself.
OUTSIDE_VIEW = """
Then take the outside view. Picture 100 people in exactly your situation at this company. Under today's
arrangement, how many of them have actually left a year from now? Under the new policy, how many? Your two
percentages are those counts. Remember that most of those 100 grumble and stay."""

PROMPTS = {"v1": PERSONA_SYSTEM,
           "v2": PERSONA_SYSTEM.replace("\n\nReply with only JSON:", SAY_DO + "\n\nReply with only JSON:"),
           "v3": PERSONA_SYSTEM.replace("\n\nReply with only JSON:", SAY_DO + "\n" + OUTSIDE_VIEW + "\n\nReply with only JSON:")}
PROMPT_VERSION = os.environ.get("WT_PROMPT", "v2")

ANALYST_SYSTEM = """You are a senior people-analytics lead advising a CHRO before a policy is announced.
You get the output of a synthetic workforce simulation: modelled employee reactions, weighted to the real
headcount mix. Simulations like this are directional, not precise; say how much weight the numbers bear.
Write for a busy executive: specific, plain, no jargon. Do not invent data you were not given.

Return only JSON:
{"headline": "<one sentence: the predicted effect on leaving, with the number>",
 "most_at_risk": "<who reacts worst or best, and why, one sentence>",
 "risks": ["<risk>", "<risk>", "<risk>"],
 "design_changes": ["<a change to the policy or rollout that would improve the outcome>", "<...>", "<...>"],
 "confidence": "<low | medium | high>, <one sentence on why>"}"""


def persona_prompt(case, p):
    return (f"Your company: {case['context']}\n\n"
            f"You: {p['name']}, a {p['age']}-year-old {p['gender']}, {p['role']} ({p['level']} level), "
            f"{p['tenure_years']} years at the company, {p['performance']}. "
            f"Commute: about {p['commute_min_each_way']} minutes each way. At home: {p['home']}.\n\n"
            f"How things work today: {case['status_quo']}\n\n"
            f"Today's announcement: {case['policy']}\n\n"
            "How do you react? Reply with only the JSON.")


def _clamp(x, lo, hi):
    try:
        return max(lo, min(hi, float(x)))
    except (TypeError, ValueError):
        return (lo + hi) / 2


def _offline_reaction(case, v):
    """Deterministic stand-in so the pipeline runs with no key. Not a forecast."""
    c = v["cell"]
    rng = random.Random(f"{case['title']}{c}{v['i']}")
    base = {"junior": 18, "mid": 12, "manager": 9}[c.split("-")[1]] + rng.uniform(-3, 3)
    weight = 1 + 0.5 * ("long" in c) + 0.3 * ("-care" in c)
    pol = base * (1 - 0.2 * case["flex_change"] * weight)
    return {"leave_pct_if_no_change": round(base, 1), "leave_pct_with_policy": round(max(pol, 0), 1),
            "feeling": case["flex_change"], "quote": "(offline mode: no model)", "top_factor": "offline"}


def react(case, v, client, session):
    if isinstance(client, OfflineClient):
        r = _offline_reaction(case, v)
    else:
        r = None
        for attempt in range(2):  # a reply cut off mid-JSON is retried once, then the voice is dropped
            text = client(PROMPTS[PROMPT_VERSION], [{"role": "user", "content": persona_prompt(case, v["persona"])}],
                          max_tokens=3000, session=session)
            try:
                r = parse_json(text)
                break
            except ValueError:
                continue
        if r is None:
            return None
    return {"base": _clamp(r.get("leave_pct_if_no_change"), 0, 100),
            "policy": _clamp(r.get("leave_pct_with_policy"), 0, 100),
            "feeling": _clamp(r.get("feeling"), -2, 2),
            "quote": str(r.get("quote", ""))[:400], "top_factor": str(r.get("top_factor", ""))[:60]}


GROUPS = {
    "gender": lambda c: c["gender"],
    "managerial": lambda c: "manager" if c["level"] == "manager" else "non-manager",
    "level": lambda c: c["level"],
    "commute": lambda c: "long" if c["long_commute"] else "short",
    "caregiver": lambda c: "caregiver" if c["caregiver"] else "no caring duties",
}


def aggregate(case, vs, n=5000, seed=11):
    """Weight cell answers by headcount; Monte Carlo the 5,000 people for 12-month leaver counts."""
    hc = headcount(case["population"], n)
    by_cell = {}
    for v in vs:
        by_cell.setdefault(v["cell"], []).append(v["reaction"])
    meta = {c["key"]: c for c in cells(case["population"])}
    cell_rows = []
    for k, rs in by_cell.items():
        cell_rows.append({"cell": k, "headcount": hc[k],
                          "base": sum(r["base"] for r in rs) / len(rs) / 100,
                          "policy": sum(r["policy"] for r in rs) / len(rs) / 100,
                          "feeling": sum(r["feeling"] for r in rs) / len(rs)})

    def rel(rows):
        b = sum(r["headcount"] * r["base"] for r in rows)
        p = sum(r["headcount"] * r["policy"] for r in rows)
        return (p / b - 1) if b else 0.0

    rng = random.Random(seed)
    leave_base = leave_pol = 0
    for r in cell_rows:
        for _ in range(r["headcount"]):
            u = rng.random()  # same draw in both worlds, so the difference is the policy
            leave_base += u < r["base"]
            leave_pol += u < r["policy"]
    subgroups = {}
    for name, f in GROUPS.items():
        groups = {}
        for r in cell_rows:
            groups.setdefault(f(meta[r["cell"]]), []).append(r)
        subgroups[name] = {g: {"relative_change": round(rel(rs), 3),
                               "headcount": sum(x["headcount"] for x in rs)} for g, rs in groups.items()}
    return {"employees": n, "relative_change": round(rel(cell_rows), 3),
            "leavers_status_quo": leave_base, "leavers_with_policy": leave_pol,
            "feeling": round(sum(r["headcount"] * r["feeling"] for r in cell_rows) / n, 2),
            "subgroups": subgroups, "cells": cell_rows}


def brief(case, forecast, vs, client, session):
    if isinstance(client, OfflineClient):
        pct = forecast["relative_change"] * 100
        return {"headline": f"Leaving changes by {pct:+.0f}% over 12 months (offline stand-in).",
                "most_at_risk": "-", "risks": [], "design_changes": [], "confidence": "low, offline mode"}
    quotes = sorted(vs, key=lambda v: v["reaction"]["policy"] - v["reaction"]["base"])
    sample = quotes[:4] + quotes[len(quotes) // 2 - 2: len(quotes) // 2 + 2] + quotes[-4:]
    lines = [f"- {v['persona']['role']}, {v['persona']['gender']}, commute {v['persona']['commute_min_each_way']} min, "
             f"{v['persona']['home']}: \"{v['reaction']['quote']}\"" for v in sample]
    sub = "\n".join(f"- {k}: " + ", ".join(f"{g} {d['relative_change'] * 100:+.0f}% (n={d['headcount']})"
                                             for g, d in groups.items())
                    for k, groups in forecast["subgroups"].items())
    user = (f"Company: {case['context']}\nToday: {case['status_quo']}\nProposed policy: {case['policy']}\n\n"
            f"Simulation of {forecast['employees']} employees ({len(vs)} modelled voices across 24 groups):\n"
            f"- Leavers in the next 12 months: {forecast['leavers_status_quo']} if nothing changes, "
            f"{forecast['leavers_with_policy']} with the policy ({forecast['relative_change'] * 100:+.0f}%)\n"
            f"- Average feeling: {forecast['feeling']:+.2f} on a -2..+2 scale\n"
            f"Relative change in leaving by group:\n{sub}\n\nSample voices:\n" + "\n".join(lines))
    return parse_json(client(ANALYST_SYSTEM, [{"role": "user", "content": user}], max_tokens=6000, session=session))


def score(case, forecast):
    pub = case.get("published")
    if not pub:
        return None
    pred, true = forecast["relative_change"], pub["relative_change"]
    checks = []
    for s in pub["subgroups"]:
        g = forecast["subgroups"][s["attr"]]
        key = "bigger_drop" if "bigger_drop" in s else "bigger_rise"
        a, b = g[s[key]]["relative_change"], g[s["vs"]]["relative_change"]
        ok = a < b if key == "bigger_drop" else a > b
        checks.append({"claim": s["say"], "twin": f"{s[key]} {a * 100:+.0f}% vs {s['vs']} {b * 100:+.0f}%", "hit": ok})
    return {"predicted": pred, "published": true, "direction_hit": (pred > 0) == (true > 0),
            "abs_error_pp": round(abs(pred - true) * 100, 1),
            "subgroup_hits": sum(c["hit"] for c in checks), "subgroup_checks": checks}


def run(case_id, clients, per_cell=2, seed=7, session="-", workers=8):
    case = CASES[case_id]
    vs = voices(case, per_cell=per_cell, seed=seed)
    with ThreadPoolExecutor(workers) as ex:
        reactions = list(ex.map(lambda v: react(case, v, clients["persona"], session), vs))
    for v, r in zip(vs, reactions):
        v["reaction"] = r
    vs = [v for v in vs if v["reaction"] is not None]
    forecast = aggregate(case, vs)
    return {"case": case_id, "title": case["title"], "kind": case["kind"], "seed": seed,
            "prompt": PROMPT_VERSION, "persona_model": getattr(clients["persona"], "model", "offline"),
            "voices": vs, "forecast": forecast,
            "briefing": brief(case, forecast, vs, clients["analyst"], session),
            "score": score(case, forecast)}

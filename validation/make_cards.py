"""Pick 12 simulated employees for the blind speed round.

    python -m validation.make_cards

Six from the Bengaluru five-day mandate (no known outcome) and six from the US RTO mandate,
spread across the twin's own predictions so the round covers low and high risk. The rater
sees the person and the policy, never the twin's answer.
Writes validation/cards.json (shown to the rater) and validation/twin_answers_HIDDEN.json.
"""
import json
from pathlib import Path
from twin.cases import CASES

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BANDS = (10, 20, 35, 50)  # % chance of leaving in 12 months: <10, 10-19, 20-34, 35-49, 50+
LABELS = ["Under 10%", "10-19%", "20-34%", "35-49%", "50% or more"]


def band(pct):
    return sum(pct >= b for b in BANDS)


def pick(case_id, seed=7, n=6):
    f = sorted((ROOT / "runs").glob(f"2*-{case_id}-s{seed}-v2-sonnet-*.json"))[-1]
    vs = sorted(json.loads(f.read_text())["voices"], key=lambda v: (v["reaction"]["policy"], v["cell"]))
    step = (len(vs) - 1) / (n - 1)
    return [vs[round(i * step)] for i in range(n)]


def main():
    cards, hidden = [], {}
    chosen = [("rto5_blr", v) for v in pick("rto5_blr")] + [("rto_sp500", v) for v in pick("rto_sp500")]
    # interleave so the two cases alternate and risk order is not obvious
    order = [0, 7, 3, 10, 5, 6, 1, 9, 4, 11, 2, 8]
    for k, idx in enumerate(order, 1):
        cid, v = chosen[idx]
        c = CASES[cid]
        cid_card = f"C{k:02d}"
        cards.append({"id": cid_card, "case": cid, "company": c["context"], "today": c["status_quo"],
                      "policy": c["policy"], "person": v["persona"]})
        hidden[cid_card] = {"case": cid, "cell": v["cell"], "twin_policy_pct": v["reaction"]["policy"],
                            "twin_base_pct": v["reaction"]["base"], "twin_band": band(v["reaction"]["policy"]),
                            "quote": v["reaction"]["quote"]}
    (HERE / "cards.json").write_text(json.dumps({"bands": LABELS, "cards": cards}, indent=2))
    (HERE / "twin_answers_HIDDEN.json").write_text(json.dumps(hidden, indent=2))
    print(f"{len(cards)} cards written")


if __name__ == "__main__":
    main()

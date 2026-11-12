"""Run the twin on every case and publish its error rate.

    python -m twin.backtest                    # all cases, seed 7
    python -m twin.backtest --seeds 7 8 9      # repeat with fresh voices to see run-to-run spread
    python -m twin.backtest --case rto5_blr    # one case
    python -m twin.backtest --offline          # no key, no cost (rule-based stand-in)
"""
import argparse, json, time, uuid
from pathlib import Path
from .cases import CASES
from .engine import PROMPT_VERSION, run
from .llm import make_clients
from .usage import Ledger

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "runs"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", action="append")
    ap.add_argument("--seeds", nargs="+", type=int, default=[7])
    ap.add_argument("--per-cell", type=int, default=2)
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args(argv)
    ledger = Ledger()
    clients = make_clients(ledger, offline=a.offline)
    mode = clients["persona"].name
    RUNS.mkdir(exist_ok=True)
    rows = []
    for cid in a.case or list(CASES):
        for seed in a.seeds:
            sid = uuid.uuid4().hex[:10]
            t0 = time.time()
            r = run(cid, clients, per_cell=a.per_cell, seed=seed, session=sid)
            r["mode"], r["spend"], r["seconds"] = mode, ledger.summary(sid), round(time.time() - t0, 1)
            if mode != "offline":
                (RUNS / f"{time.strftime('%Y%m%d-%H%M%S')}-{cid}-s{seed}-{PROMPT_VERSION}-{clients['persona'].model.split('-')[1] if mode != 'offline' else 'off'}-{sid}.json").write_text(json.dumps(r, indent=2))
            s, f = r["score"], r["forecast"]
            line = (f"{cid:12s} seed {seed}  twin {f['relative_change'] * 100:+5.0f}%  "
                    f"leavers {f['leavers_status_quo']}->{f['leavers_with_policy']} of {f['employees']}")
            if s:
                line += (f"  | published {s['published'] * 100:+.0f}%  error {s['abs_error_pp']:.0f}pp  "
                         f"direction {'hit' if s['direction_hit'] else 'MISS'}  "
                         f"subgroups {s['subgroup_hits']}/{len(s['subgroup_checks'])}")
            print(line + f"  ${r['spend']['usd']:.3f}  {r['seconds']}s", flush=True)
            rows.append({"case": cid, "seed": seed, "mode": mode, "forecast": f["relative_change"],
                         "score": s, "usd": r["spend"]["usd"]})
    scored = [x["score"] for x in rows if x["score"]]
    if scored:
        mae = sum(s["abs_error_pp"] for s in scored) / len(scored)
        dirs = sum(s["direction_hit"] for s in scored)
        subs = sum(s["subgroup_hits"] for s in scored), sum(len(s["subgroup_checks"]) for s in scored)
        print(f"\nBacktest runs: {len(scored)}  direction {dirs}/{len(scored)}  "
              f"mean abs error {mae:.1f} pp  subgroup pattern {subs[0]}/{subs[1]}")
    if mode != "offline":
        (RUNS / "last_batch.json").write_text(json.dumps(rows, indent=2))
    print(f"Spend so far: ${ledger.total():.4f} of ${ledger.budget:.2f}")


if __name__ == "__main__":
    main()

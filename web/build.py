"""Assemble web/explainer.html from the saved live runs.

    python -m web.build
"""
import glob, json
from pathlib import Path
from twin.cases import CASES

ROOT = Path(__file__).resolve().parent.parent


FIRST, FINAL = "v1|claude-haiku-5-5", "v2|claude-sonnet-5-5"


def latest(case, seed=7, prompt="v2", model="sonnet"):
    fs = sorted(glob.glob(str(ROOT / "runs" / f"2*-{case}-s{seed}-{prompt}-{model}-*.json")))
    return json.loads(Path(fs[-1]).read_text()) if fs else None


def forward(case):
    r = latest(case)
    f = r["forecast"]
    vs = sorted(r["voices"], key=lambda v: v["reaction"]["policy"] - v["reaction"]["base"])
    pick = [vs[0], vs[len(vs) // 3], vs[2 * len(vs) // 3], vs[-1]]
    return {"policy": CASES[case]["policy"], "status_quo": CASES[case]["status_quo"],
            "rel": f["relative_change"], "sq": f["leavers_status_quo"], "pol": f["leavers_with_policy"],
            "feeling": f["feeling"], "subgroups": f["subgroups"],
            "cells": [{k: c[k] for k in ("cell", "headcount", "base", "policy")} for c in f["cells"]],
            "quotes": [{"who": f"{v['persona']['name']}, {v['persona']['age']}, {v['persona']['role']}",
                        "detail": f"{v['persona']['commute_min_each_way']} min commute · {v['persona']['home']}",
                        "quote": v["reaction"]["quote"], "base": v["reaction"]["base"],
                        "policy": v["reaction"]["policy"]} for v in pick],
            "briefing": r["briefing"], "usd": r["spend"]["usd"], "calls": r["spend"]["calls"]}


def main():
    board = json.loads((ROOT / "docs" / "scoreboard.json").read_text())
    human = ROOT / "validation" / "human_result.json"
    data = {"rto5": forward("rto5_blr"), "rto3": forward("rto3_blr"),
            "board": [dict(b, stage="first" if b["config"] == FIRST else "final") for b in board
                      if b["kind"] == "backtest" and b["config"] in (FIRST, FINAL)],
            "mid": [b for b in board if b["kind"] == "backtest" and b["config"] == "v2|claude-haiku-5-5"],
            "human": json.loads(human.read_text()) if human.exists() else None}
    tpl = (ROOT / "web" / "explainer_template.html").read_text()
    (ROOT / "web" / "explainer.html").write_text(tpl.replace("__DATA__", json.dumps(data)))
    print("web/explainer.html written")


if __name__ == "__main__":
    main()

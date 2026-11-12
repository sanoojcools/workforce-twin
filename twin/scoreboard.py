"""Build the published scoreboard from every saved live run.

    python -m twin.scoreboard     # prints the table and writes runs/scoreboard.md + docs/scoreboard.json
"""
import json
from pathlib import Path
from .cases import CASES

ROOT = Path(__file__).resolve().parent.parent


CONFIGS = {  # (prompt, persona model) -> label; the last one is what the app ships with
    ("v1", "claude-haiku-5-5"): "A. First version: Haiku 5.5 voices",
    ("v2", "claude-haiku-5-5"): "B. Haiku 5.5 voices + say-do check",
    ("v3", "claude-haiku-5-5"): "B2. Haiku 5.5 voices + say-do + outside view (spot check)",
    ("v2", "claude-sonnet-5-5"): "C. Sonnet 5.5 voices + say-do check (current)",
}


def config_of(r):
    return f"{r.get('prompt', 'v1')}|{r.get('persona_model', '')}"


def load_runs():
    latest = {}
    for f in sorted((ROOT / "runs").glob("2*.json")):
        r = json.loads(f.read_text())
        r["config"] = config_of(r)
        latest[(r["case"], r["seed"], r["config"])] = r  # later file wins
    return list(latest.values())


def build(config):
    runs = [r for r in load_runs() if r["config"] == config]
    by_case = {}
    for r in runs:
        by_case.setdefault(r["case"], []).append(r)
    out = []
    for cid, rs in by_case.items():
        case = CASES[cid]
        preds = [r["forecast"]["relative_change"] for r in rs]
        row = {"config": config, "label": CONFIGS[tuple(config.split("|"))], "case": cid, "title": case["title"], "kind": case["kind"], "runs": len(rs),
               "twin_each": preds, "twin_mean": sum(preds) / len(preds),
               "usd_per_run": sum(r["spend"]["usd"] for r in rs) / len(rs)}
        if case["published"]:
            pub = case["published"]
            row.update(published=pub["relative_change"], study=pub["study"], caveat=pub["caveat"],
                       sources=pub["sources"],
                       abs_error_pp=abs(row["twin_mean"] - pub["relative_change"]) * 100,
                       direction_hits=sum(r["score"]["direction_hit"] for r in rs),
                       subgroup_hits=sum(r["score"]["subgroup_hits"] for r in rs),
                       subgroup_total=sum(len(r["score"]["subgroup_checks"]) for r in rs))
        out.append(row)
    order = list(CASES)
    return sorted(out, key=lambda x: order.index(x["case"]))


def table(rows):
    bt = [r for r in rows if r["kind"] == "backtest"]
    lines = ["| Case | Runs | Twin forecast | Published | Error | Direction | Subgroup pattern |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    for r in bt:
        lines.append(f"| {r['title']} | {r['runs']} | {r['twin_mean'] * 100:+.0f}% "
                     f"({', '.join(f'{p * 100:+.0f}' for p in r['twin_each'])}) | {r['published'] * 100:+.0f}% | "
                     f"{r['abs_error_pp']:.0f} pp | {r['direction_hits']}/{r['runs']} | "
                     f"{r['subgroup_hits']}/{r['subgroup_total']} |")
    if bt:
        mae = sum(r["abs_error_pp"] for r in bt) / len(bt)
        lines.append(f"\nMean absolute error across the {len(bt)} studies: **{mae:.0f} percentage points** "
                     f"of relative change in leaving. Direction right in "
                     f"{sum(r['direction_hits'] for r in bt)}/{sum(r['runs'] for r in bt)} runs; subgroup pattern "
                     f"{sum(r['subgroup_hits'] for r in bt)}/{sum(r['subgroup_total'] for r in bt)}.")
    for r in rows:
        if r["kind"] == "forward":
            lines.append(f"\nForward: {r['title']}: twin {r['twin_mean'] * 100:+.0f}% "
                         f"({', '.join(f'{p * 100:+.0f}' for p in r['twin_each'])}), no known outcome.")
    return "\n".join(lines)


def main():
    allrows, parts = [], []
    for key, label in CONFIGS.items():
        rows = build("|".join(key))
        if rows:
            parts.append(f"### {label}\n\n" + table(rows))
            allrows += rows
    text = "\n\n".join(parts)
    print(text)
    (ROOT / "runs" / "scoreboard.md").write_text(text + "\n")
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "scoreboard.json").write_text(json.dumps(allrows, indent=2))


if __name__ == "__main__":
    main()

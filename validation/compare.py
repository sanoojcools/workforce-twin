"""Compare a human's blind risk calls with the twin's.

    python -m validation.compare validation/human_ratings.json

human_ratings.json: {"C01": 0-4, ...} (band index, 0 = under 10% ... 4 = 50% or more).
Reports quadratic-weighted kappa on the 5 bands, exact and within-one-band agreement,
Spearman rank correlation, and whether the twin runs hotter or colder than the human.
"""
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def qwk(a, b, k=5):
    n = len(a)
    obs = [[0] * k for _ in range(k)]
    for x, y in zip(a, b):
        obs[x][y] += 1
    ha = [sum(r) for r in obs]
    hb = [sum(obs[i][j] for i in range(k)) for j in range(k)]
    num = den = 0.0
    for i in range(k):
        for j in range(k):
            w = (i - j) ** 2 / (k - 1) ** 2
            num += w * obs[i][j]
            den += w * ha[i] * hb[j] / n
    return 1 - num / den if den else 1.0


def ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for t in range(i, j + 1):
            r[order[t]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(a, b):
    ra, rb = ranks(a), ranks(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    va = sum((x - ma) ** 2 for x in ra) ** 0.5
    vb = sum((y - mb) ** 2 for y in rb) ** 0.5
    return cov / (va * vb) if va and vb else 0.0


def main(path):
    human = json.loads(Path(path).read_text())
    twin = json.loads((HERE / "twin_answers_HIDDEN.json").read_text())
    ids = sorted(set(human) & set(twin))
    h = [int(human[i]) for i in ids]
    t = [twin[i]["twin_band"] for i in ids]
    print(f"Cards compared: {len(ids)}")
    print(f"Quadratic-weighted kappa (5 bands): {qwk(h, t):.2f}")
    print(f"Exact band match: {sum(x == y for x, y in zip(h, t))}/{len(ids)}   "
          f"within one band: {sum(abs(x - y) <= 1 for x, y in zip(h, t))}/{len(ids)}")
    print(f"Spearman rank correlation: {spearman(h, t):.2f}")
    print(f"Mean band: human {sum(h) / len(h):.2f}, twin {sum(t) / len(t):.2f}")
    for i, x, y in zip(ids, h, t):
        print(f"  {i} {twin[i]['case']:10s} {twin[i]['cell']:28s} human {x}  twin {y} ({twin[i]['twin_policy_pct']:.0f}%)")


if __name__ == "__main__":
    main(sys.argv[1])

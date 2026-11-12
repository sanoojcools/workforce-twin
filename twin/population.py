"""The synthetic workforce.

5,000 employees are drawn from a case's population profile. They fall into 24 cells
(gender x level x commute x caregiver). The twin interviews a few "voices" per cell with the
model and gives every employee in that cell the cell's answers, so the cost scales with
the number of cells, not with headcount.
"""
import itertools, random

LEVELS = ("junior", "mid", "manager")
NAMES = {
    "zh": {"F": ["Li Na", "Wang Fang", "Zhang Min", "Chen Jing", "Liu Yan", "Zhao Lei"],
           "M": ["Wang Wei", "Li Qiang", "Zhang Jun", "Liu Yang", "Chen Hao", "Huang Tao"]},
    "us": {"F": ["Jessica", "Maria", "Ashley", "Priya", "Emily", "Keisha"],
           "M": ["Michael", "David", "Carlos", "Kevin", "James", "Andre"]},
    "uk": {"F": ["Sophie", "Amira", "Hannah", "Chloe", "Priya", "Grace"],
           "M": ["James", "Oliver", "Tom", "Daniel", "Ravi", "Callum"]},
    "in": {"F": ["Ananya", "Divya", "Lakshmi", "Sneha", "Fatima", "Kavya"],
           "M": ["Rahul", "Arjun", "Karthik", "Vikram", "Imran", "Siddharth"]},
}
ROLES = {"junior": ["software engineer", "marketing associate", "finance analyst", "accountant", "QA engineer"],
         "mid": ["senior engineer", "product marketing lead", "senior finance analyst", "data analyst", "team lead"],
         "manager": ["engineering manager", "marketing manager", "finance manager", "director of operations"]}
AGE = {"junior": (23, 29), "mid": (28, 38), "manager": (34, 50)}
TENURE = {"junior": (0, 3), "mid": (2, 8), "manager": (4, 15)}


def cells(pop):
    """All 24 cells with their population share."""
    out = []
    for g, lvl, lc, cg in itertools.product(("F", "M"), LEVELS, (True, False), (True, False)):
        share = (pop["F"] if g == "F" else 1 - pop["F"]) * pop["level"][lvl]
        share *= pop["long_commute"] if lc else 1 - pop["long_commute"]
        pc = pop["caregiver"][lvl]
        share *= pc if cg else 1 - pc
        out.append({"key": f"{g}-{lvl}-{'long' if lc else 'short'}-{'care' if cg else 'nocare'}",
                    "gender": g, "level": lvl, "long_commute": lc, "caregiver": cg, "share": share})
    return out


def headcount(pop, n=5000):
    """Integer headcount per cell that sums to n (largest remainder)."""
    cs = cells(pop)
    raw = [c["share"] * n for c in cs]
    hc = [int(r) for r in raw]
    for i in sorted(range(len(cs)), key=lambda i: raw[i] - hc[i], reverse=True)[: n - sum(hc)]:
        hc[i] += 1
    return {c["key"]: h for c, h in zip(cs, hc)}


def voice(cell, names, rng):
    """One concrete employee from a cell, described the way an HRBP would know them."""
    lvl = cell["level"]
    name = rng.choice(NAMES[names][cell["gender"]])
    age = rng.randint(*AGE[lvl])
    tenure = rng.randint(*TENURE[lvl])
    commute = rng.randint(55, 100) if cell["long_commute"] else rng.randint(10, 35)
    if cell["caregiver"]:
        care = rng.choice(["two young children", "a toddler and a partner who also works full time",
                           "an elderly parent who lives with them", "a child in primary school"])
    else:
        care = rng.choice(["no caring duties", "lives alone", "lives with a partner, no children"])
    perf = rng.choice(["solid performer", "strong performer", "top performer", "steady, meets expectations"])
    return {"name": name, "gender": "woman" if cell["gender"] == "F" else "man", "age": age,
            "role": rng.choice(ROLES[lvl]), "level": lvl, "tenure_years": tenure,
            "commute_min_each_way": commute, "home": care, "performance": perf}


def voices(case, per_cell=2, seed=7):
    rng = random.Random(f"{seed}-{case['title']}")
    out = []
    for c in cells(case["population"]):
        for i in range(per_cell):
            out.append({"cell": c["key"], "i": i, "persona": voice(c, case["population"]["names"], rng)})
    return out

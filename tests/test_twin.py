import json, tempfile, unittest
from types import SimpleNamespace
from twin.cases import CASES, BACKTESTS
from twin.engine import persona_prompt, run, PERSONA_SYSTEM, ANALYST_SYSTEM
from twin.llm import make_clients
from twin.population import cells, headcount, voices
from twin.usage import BudgetExceeded, Ledger


class Population(unittest.TestCase):
    def test_cells_sum_to_one(self):
        for c in CASES.values():
            self.assertEqual(len(cells(c["population"])), 24)
            self.assertAlmostEqual(sum(x["share"] for x in cells(c["population"])), 1.0)

    def test_headcount_is_exactly_5000(self):
        for c in CASES.values():
            self.assertEqual(sum(headcount(c["population"]).values()), 5000)

    def test_voices_are_deterministic(self):
        c = CASES["rto_sp500"]
        self.assertEqual(voices(c, seed=3), voices(c, seed=3))
        self.assertNotEqual(voices(c, seed=3), voices(c, seed=4))


class Blindness(unittest.TestCase):
    def test_published_outcome_never_reaches_a_prompt(self):
        for cid in BACKTESTS:
            case = CASES[cid]
            pub = case["published"]
            for v in voices(case):
                text = PERSONA_SYSTEM + persona_prompt(case, v["persona"])
                self.assertNotIn(pub["study"].split(" ")[0], text)
                self.assertNotIn(pub["statement"][:30], text)
                self.assertNotIn(f"{abs(pub['relative_change']) * 100:.0f}%", text)
            self.assertNotIn("published", ANALYST_SYSTEM.lower())


class Offline(unittest.TestCase):
    def test_runs_and_scores(self):
        clients = make_clients(offline=True)
        r = run("hybrid_trip", clients)
        self.assertLess(r["forecast"]["relative_change"], 0)
        self.assertTrue(r["score"]["direction_hit"])
        self.assertEqual(r["forecast"]["employees"], 5000)
        self.assertIsNone(run("rto5_blr", clients)["score"])
        json.dumps(r)


class Spend(unittest.TestCase):
    def test_cap_stops_calls(self):
        with tempfile.TemporaryDirectory() as d:
            led = Ledger(path=f"{d}/u.jsonl", budget_usd=0.001)
            led.record(session="s", role="persona", model="claude-haiku-5-5", effort="low",
                       usage=SimpleNamespace(input_tokens=20000, output_tokens=0), latency_s=0.1)
            with self.assertRaises(BudgetExceeded):
                led.check()


if __name__ == "__main__":
    unittest.main()

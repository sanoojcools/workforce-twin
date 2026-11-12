# Workforce Twin

**Test a people policy on a synthetic copy of your workforce before you announce it, and see how wrong the
twin has been on real policies.**

A CHRO pastes a draft announcement (say, five days in the office from next quarter). The twin builds a
5,000-person workforce in the company's headcount mix, asks it how it would react, and returns: how many more
people leave over 12 months, which groups are hit hardest, what employees would say to each other, and a
briefing with changes that would soften the impact. Then it does the same for a redesigned draft, so the two
can be compared before anyone real reads either.

Explainer with the customer's view: `web/explainer.html` (built from the real runs by `python -m web.build`).

## How it works

1. **Workforce.** 5,000 employees are drawn from a population profile and fall into 24 groups:
   gender x level (junior, mid, manager) x commute (short, long) x caring duties.
2. **Voices.** Two concrete people from each group (name, age, role, tenure, commute, home situation) read the
   company context, today's arrangement and the announcement. Each gives a 12-month chance of leaving with and
   without the policy, a feeling score, and what they would tell a close colleague. Every voice first separates
   what they would *say* from what they would *do* (see "Error rate" for why).
3. **Scale-up.** Group answers are weighted to headcount. A Monte Carlo pass over the 5,000 people (same random
   draw in both worlds) turns the probabilities into leaver counts, so the difference is the policy alone.
4. **Briefing.** One analyst call reads the weighted numbers and a sample of voices and writes a CHRO briefing:
   headline, most-at-risk groups, risks, design changes, confidence.

| Job | Model | Calls per run |
| --- | --- | --- |
| Employee voices | Claude Sonnet 5.5, effort low | 48 |
| Analyst briefing | Claude Opus 5.5, effort high | 1 |

Cost scales with the number of groups, not headcount. Every call is logged with its dollar cost in
`runs/usage.jsonl`; `WT_BUDGET_USD` (default $5) is a hard cap. See [COSTS.md](COSTS.md).

## Error rate

The twin is only useful if it is right about real policies, so it was run blind on three policy changes with
published outcomes, three times each with fresh voices. Measure: relative change in people leaving.

### A. First version: Haiku 5.5 voices

| Case | Runs | Twin forecast | Published | Error | Direction | Subgroup pattern |
| --- | --- | --- | --- | --- | --- | --- |
| Hybrid WFH at a travel-tech company | 3 | -38% (-38, -38, -39) | -33% | 5 pp | 3/3 | 9/9 |
| Return-to-office mandate at a big US tech or finance firm | 3 | +216% (+211, +222, +215) | +14% | 202 pp | 3/3 | 6/6 |
| Four-day week at UK small and mid-size firms | 2 | -49% (-48, -49) | -57% | 8 pp | 2/2 | 0/0 |

Mean absolute error across the 3 studies: **72 percentage points** of relative change in leaving. Direction right in 8/8 runs; subgroup pattern 15/15.

### B. Haiku 5.5 voices + say-do check

| Case | Runs | Twin forecast | Published | Error | Direction | Subgroup pattern |
| --- | --- | --- | --- | --- | --- | --- |
| Hybrid WFH at a travel-tech company | 3 | -32% (-32, -34, -31) | -33% | 1 pp | 3/3 | 7/9 |
| Return-to-office mandate at a big US tech or finance firm | 3 | +181% (+187, +180, +175) | +14% | 167 pp | 3/3 | 3/6 |
| Four-day week at UK small and mid-size firms | 1 | -43% (-43) | -57% | 14 pp | 1/1 | 0/0 |

Mean absolute error across the 3 studies: **61 percentage points** of relative change in leaving. Direction right in 7/7 runs; subgroup pattern 10/15.

### B2. Haiku 5.5 voices + say-do + outside view (spot check)

| Case | Runs | Twin forecast | Published | Error | Direction | Subgroup pattern |
| --- | --- | --- | --- | --- | --- | --- |
| Hybrid WFH at a travel-tech company | 1 | -34% (-34) | -33% | 1 pp | 1/1 | 2/3 |
| Return-to-office mandate at a big US tech or finance firm | 1 | +182% (+182) | +14% | 168 pp | 1/1 | 1/2 |

Mean absolute error across the 2 studies: **84 percentage points** of relative change in leaving. Direction right in 2/2 runs; subgroup pattern 3/5.

### C. Sonnet 5.5 voices + say-do check (current)

| Case | Runs | Twin forecast | Published | Error | Direction | Subgroup pattern |
| --- | --- | --- | --- | --- | --- | --- |
| Hybrid WFH at a travel-tech company | 3 | -34% (-35, -34, -34) | -33% | 1 pp | 3/3 | 5/9 |
| Return-to-office mandate at a big US tech or finance firm | 3 | +91% (+94, +91, +89) | +14% | 77 pp | 3/3 | 6/6 |
| Four-day week at UK small and mid-size firms | 3 | -49% (-48, -49, -50) | -57% | 8 pp | 3/3 | 0/0 |

Mean absolute error across the 3 studies: **29 percentage points** of relative change in leaving. Direction right in 9/9 runs; subgroup pattern 11/15.

Forward: Five-day office return at a Bengaluru IT services firm: twin +120% (+115, +126), no known outcome.

Forward: Redesigned: three office days at the same Bengaluru firm: twin +39% (+39, +40), no known outcome.


**What happened.** The first version (Haiku 5.5 voices) got the direction right every time and was within
5-8 points on the two policies that give people more flexibility. It overstated the return-to-office mandate
about 15 times: its simulated employees answered the way people talk when a perk is taken away, not the way
they act. Asking each voice to separate what they would say from what they would do (prompt v2) barely moved
Haiku (+216% to +181%); an outside-view prompt (v3) did not help either. Switching the voices to Sonnet 5.5
with the say-do check cut the RTO miss from 202 to 77 points and the average miss from 72 to 29 points.
It still overstates exits from a takeaway about 7 times, and it got the hybrid study's subgroup pattern less
often than Haiku did (5/9 vs 9/9).

**How to read a forecast.** Trust the direction, the ranking of groups, and the comparison between two
drafts. Treat the leaver count for a takeaway as a ceiling. On the forward case (five office days at a
Bengaluru IT services firm) the twin says +120%; a redesigned three-day version says +39%.

Every run is saved in `runs/` with all 48 voices and the briefing.

## Human check

An experienced HR leader (the author: certified Amazon Bar Raiser, HR roles at Trianz, Swvl and Carrefour)
makes blind one-tap calls on 12 simulated employees: how likely is this person to leave within 12 months if the
policy goes ahead? The twin's answers stay hidden (`validation/twin_answers_HIDDEN.json`).
`python -m validation.compare` reports quadratic-weighted kappa on five risk bands and rank correlation.

**Result (2026-11-12, 12 cards): quadratic-weighted kappa 0.59, rank correlation 0.71, 11 of 12 within one
band.** The twin ran hotter than the human (average band 1.67 vs 1.17), the same lean the backtest found on
takeaways. One rater, 12 cards: a first read. Details: [validation/results.md](validation/results.md).

## Run it

Python 3.10+. Offline mode needs nothing; live mode needs `pip install -r requirements.txt` and a key in
`ANTHROPIC_API_KEY` (or `HR_APPS_ANTHROPIC_KEY` in a Claude Code cloud session).

```bash
python -m twin.backtest --offline                      # whole pipeline, no key, rule-based stand-in
WT_PERSONA_MODEL=claude-sonnet-5-5 python -m twin.backtest --seeds 7 8 9   # live backtests + forward cases
python -m twin.scoreboard                              # error-rate table from every saved run
python -m twin.usage                                   # spend report
python -m validation.make_cards                        # 12 blind cards for a human rater
python -m validation.compare validation/human_ratings.json
python -m unittest -v tests.test_twin
```

Cases live in `twin/cases.py`. A backtest case holds the published outcome on the far side of a wall: a test
checks that it never reaches a prompt.

## Limits

- Three backtests is a small sample, and the voice-model switch was chosen after seeing the RTO miss, so the
  final RTO number is in-sample.
- The studies measure different windows (a six-month trial, an event study of turnover, a six-month pilot);
  the twin forecasts a 12-month change, so the comparison is approximate. The four-day-week pilot had no control
  group and its firms volunteered.
- The models may have read these studies. The twin is never told the outcome, but contamination cannot be ruled
  out; that is why the forward case and the human check matter.
- The workforce is synthetic. A real deployment would build the groups from aggregate HRIS data, never from
  individual records, and report only at group level.

All people and companies in the forward cases are fictional.

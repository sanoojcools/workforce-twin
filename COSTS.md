# Keeping API spend smart and visible

## Route by the kind of thinking

| Job | How often | Model and effort | Why |
| --- | --- | --- | --- |
| Simulated employee voice | 48 per run (24 groups x 2 people) | Claude Sonnet 5.5, effort `low` | Haiku 5.5 was 4x cheaper but overstated exits from takeaways 15x; Sonnet halved the miss. |
| Analyst briefing for the CHRO | Once per run | Claude Opus 5.5, effort `high` | The judgment is the product, so it gets the strongest model. |

The 5,000 employees are not 5,000 calls. Each of the 24 groups (gender x level x commute x caring duties) is
interviewed through two people, and their answers are weighted by the group's headcount. Cost scales with the
number of groups, not with headcount, so a 50,000-person company costs the same to simulate.

Change routing without touching code:

```bash
export WT_PERSONA_MODEL=claude-haiku-5-5    # cheaper voices, much worse on takeaways (see README)
export WT_ANALYST_EFFORT=medium             # cheaper briefing
```

## Track every call

Every API call is written to `runs/usage.jsonl` with role, model, effort, tokens, latency and dollar cost.
`python -m twin.usage` prints totals by role and day.

## Cap it

`WT_BUDGET_USD` (default $5) is a hard stop: once the ledger reaches it, no further calls are made. Set a
monthly limit on the Anthropic Console workspace as the final backstop.

## Measured cost

First live runs, 2026-11-11 (33 runs, $2.99 in total including the Haiku experiments):

| Setup | Per run | Split |
| --- | --- | --- |
| Haiku 5.5 voices + Opus 5.5 briefing | $0.04-0.05 | briefing about 85% |
| Sonnet 5.5 voices + Opus 5.5 briefing (current) | $0.16-0.18 | voices about 80% |

Sonnet costs about 4x more per run and cut the average backtest miss from 72 to 29 points, so it is the
default. At $0.17 a run, the $5 cap covers about 30 runs.

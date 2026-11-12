# Blind human check, 2026-11-12

Sanuj, an HR leader with roles at Trianz, Swvl and Carrefour, made blind calls on 12 simulated employees (six at the Bengaluru firm, six at the US firm) on 12 November 2026: how likely each person is to leave within 12 months if the mandate goes ahead, in five bands. The twin's answers were hidden until all 12 were saved. Result: quadratic-weighted kappa 0.59, rank correlation 0.71, 11 of 12 calls within one band (3 exact). The twin ran hotter than the human on 7 of 12 people (average band 1.67 vs 1.17). It is the same lean the backtest found: on a takeaway, the simulated employees overstate how many would actually walk.

| Card | Case | Group | Human band | Twin band (twin %) |
| --- | --- | --- | --- | --- |
| C01 | rto5_blr | F-manager-short-nocare | 1 | 1 (14%) |
| C02 | rto_sp500 | F-manager-short-nocare | 1 | 1 (15%) |
| C03 | rto5_blr | M-mid-short-care | 1 | 2 (25%) |
| C04 | rto_sp500 | M-junior-long-care | 1 | 2 (24%) |
| C05 | rto5_blr | M-junior-long-nocare | 2 | 3 (38%) |
| C06 | rto_sp500 | M-manager-short-nocare | 0 | 0 (9%) |
| C07 | rto5_blr | M-manager-short-nocare | 0 | 1 (17%) |
| C08 | rto_sp500 | F-junior-short-nocare | 1 | 2 (22%) |
| C09 | rto5_blr | M-mid-long-care | 3 | 2 (30%) |
| C10 | rto_sp500 | F-junior-long-care | 4 | 3 (35%) |
| C11 | rto5_blr | F-mid-short-care | 0 | 2 (22%) |
| C12 | rto_sp500 | M-mid-long-nocare | 0 | 1 (17%) |

Bands: 0 under 10%, 1 10-19%, 2 20-34%, 3 35-49%, 4 50% or more. Reproduce with
`python -m validation.compare validation/human_ratings.json` (needs `validation/twin_answers_HIDDEN.json`,
now published since the round is graded). One rater and 12 cards is a first read, not proof.

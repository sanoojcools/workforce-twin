"""Policy cases.

A backtest case is a real policy change with a published outcome. The twin is shown the
company context, the status quo and the announcement, never the outcome. `published` stays
on this side of the wall: tests check it never reaches a prompt.

A forward case has no known outcome: it is what a customer would run before announcing.
"""

CASES = {
    "hybrid_trip": {
        "title": "Hybrid WFH at a travel-tech company",
        "kind": "backtest",
        "flex_change": +1,  # used only by the offline stand-in
        "context": ("A large online travel company headquartered in Shanghai, China. You are a university-educated "
                    "employee in engineering, marketing, accounting or finance. Shanghai commutes are often long. "
                    "The local job market for your skills is competitive but not easy."),
        "status_quo": "Everyone works in the office five days a week, Monday to Friday.",
        "policy": ("From next month, you may work from home on Wednesdays and Fridays. Monday, Tuesday and Thursday "
                   "stay in the office. Your manager, pay, performance review and promotion process do not change."),
        "population": {"F": 0.35, "level": {"junior": 0.45, "mid": 0.40, "manager": 0.15},
                       "long_commute": 0.50, "caregiver": {"junior": 0.10, "mid": 0.35, "manager": 0.60},
                       "names": "zh"},
        "published": {
            "relative_change": -0.33,
            "statement": "Quit rates fell by one third in the hybrid group, with no change in performance or promotions.",
            "subgroups": [
                {"attr": "gender", "bigger_drop": "F", "vs": "M", "say": "Larger drop for women"},
                {"attr": "managerial", "bigger_drop": "non-manager", "vs": "manager", "say": "Larger drop for non-managers"},
                {"attr": "commute", "bigger_drop": "long", "vs": "short", "say": "Larger drop for long commuters"},
            ],
            "study": "Bloom, Han & Liang (2024), randomised trial of 1,612 Trip.com employees, Nature",
            "sources": ["https://www.scimex.org/newsfeed/working-from-home-flexibility-can-improve-staff-retention-without-impacting-their-performance",
                        "https://cep.lse.ac.uk/_NEW/PUBLICATIONS/abstract.asp?index=10993"],
            "caveat": "Randomised trial, the strongest evidence of the three.",
        },
    },
    "rto_sp500": {
        "title": "Return-to-office mandate at a big US tech or finance firm",
        "kind": "backtest",
        "flex_change": -1,
        "context": ("A large US technology or financial-services company (an S&P 500 firm). You are a salaried "
                    "professional. Since 2020 most of your team has worked hybrid or remotely, and other employers "
                    "in your field still offer some flexibility."),
        "status_quo": "You choose where you work most days; you go into the office when your team needs to.",
        "policy": ("Starting in 90 days, all employees must work from the office at least three set days a week. "
                   "Badge swipes will be tracked and reviewed with managers. Exceptions need VP approval."),
        "population": {"F": 0.35, "level": {"junior": 0.40, "mid": 0.40, "manager": 0.20},
                       "long_commute": 0.45, "caregiver": {"junior": 0.15, "mid": 0.40, "manager": 0.55},
                       "names": "us"},
        "published": {
            "relative_change": +0.14,
            "statement": "Employee turnover rose about 14% after the mandates; hiring took 23% longer.",
            "subgroups": [
                {"attr": "gender", "bigger_rise": "F", "vs": "M", "say": "Bigger rise for women (nearly 3x men)"},
                {"attr": "managerial", "bigger_rise": "manager", "vs": "non-manager", "say": "Bigger rise for mid and senior managers"},
            ],
            "study": "Ding, Jin, Ma, Xing & Yang (2024), LinkedIn data on 3M+ employees at 54 S&P 500 tech and finance firms, SSRN 5031481",
            "sources": ["https://hankamer.baylor.edu/news/story/2025/return-office-mandates-and-hidden-cost-brain-drain",
                        "https://fortune.com/2024/12/13/return-to-office-mandate-risk-losing-top-performers-study/"],
            "caveat": "Observational (event study), not randomised.",
        },
    },
    "fourday_uk": {
        "title": "Four-day week at UK small and mid-size firms",
        "kind": "backtest",
        "flex_change": +1,
        "context": ("A small or mid-size UK organisation (marketing, professional services, a charity or a tech "
                    "firm, 10 to 500 staff). You work full time, about 37.5 hours over five days."),
        "status_quo": "Five days a week, about 37.5 hours, standard pay.",
        "policy": ("For a six-month trial starting next month, everyone moves to a four-day week (about 32 hours) "
                   "with no cut in pay. In return, teams commit to keeping output at today's level."),
        "population": {"F": 0.50, "level": {"junior": 0.40, "mid": 0.40, "manager": 0.20},
                       "long_commute": 0.30, "caregiver": {"junior": 0.15, "mid": 0.40, "manager": 0.55},
                       "names": "uk"},
        "published": {
            "relative_change": -0.57,
            "statement": "The number of staff leaving fell 57% over the trial; 56 of 61 firms kept the four-day week.",
            "subgroups": [],
            "study": "Autonomy and 4 Day Week Global (2023), UK pilot, 61 companies, about 2,900 workers",
            "sources": ["https://autonomy.work/portfolio/uk4dwpilotresults/"],
            "caveat": "Firms volunteered and there was no control group, so the drop is likely overstated.",
        },
    },
    "rto5_blr": {
        "title": "Five-day office return at a Bengaluru IT services firm",
        "kind": "forward",
        "flex_change": -1,
        "context": ("A 5,000-person IT services company in Bengaluru, India. Clients are in the US and Europe, so "
                    "some calls run late. Bengaluru traffic is heavy. Competitors hire your skills actively and "
                    "several of them still offer hybrid work."),
        "status_quo": "Hybrid: two set office days a week, the rest from home.",
        "policy": ("From the first of next quarter, everyone works from the office five days a week. Attendance "
                   "counts toward your performance rating. A shuttle service will be added on main routes."),
        "population": {"F": 0.38, "level": {"junior": 0.50, "mid": 0.35, "manager": 0.15},
                       "long_commute": 0.60, "caregiver": {"junior": 0.15, "mid": 0.45, "manager": 0.65},
                       "names": "in"},
        "published": None,
    },
    "rto3_blr": {
        "title": "Redesigned: three office days at the same Bengaluru firm",
        "kind": "forward",
        "flex_change": -1,
        "context": None,  # filled from rto5_blr below
        "status_quo": "Hybrid: two set office days a week, the rest from home.",
        "policy": ("From the first of next quarter, teams work from the office three set days a week, chosen by "
                   "each team to match client hours. Attendance is not part of performance ratings. A shuttle "
                   "service will be added on main routes, and anyone with caring or health needs can apply for "
                   "an exception that HR answers within two weeks."),
        "population": None,
        "published": None,
    },
}

CASES["rto3_blr"]["context"] = CASES["rto5_blr"]["context"]
CASES["rto3_blr"]["population"] = CASES["rto5_blr"]["population"]

BACKTESTS = [k for k, c in CASES.items() if c["kind"] == "backtest"]

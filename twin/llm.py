"""Model clients and routing.

Two jobs, two models:
  persona  - 48 short in-character reactions per run -> Claude Sonnet 5.5, effort low
             (Haiku 5.5 was tried first; it overstated exits from takeaways 15x, see README)
  analyst  - one careful forecast briefing per run     -> Claude Opus 5.5, effort high
Override with WT_PERSONA_MODEL / WT_PERSONA_EFFORT / WT_ANALYST_MODEL / WT_ANALYST_EFFORT.

OfflineClient is a marker: the engine uses a rule-based stand-in so tests run with no key.
"""
import json, os, re, time
from .usage import Ledger

ROUTES = {
    "persona": {"model": os.environ.get("WT_PERSONA_MODEL", "claude-sonnet-5-5"),
                "effort": os.environ.get("WT_PERSONA_EFFORT", "low")},
    "analyst": {"model": os.environ.get("WT_ANALYST_MODEL", "claude-opus-5-5"),
                "effort": os.environ.get("WT_ANALYST_EFFORT", "high")},
}
FALLBACK_OK = ("claude-opus-", "claude-sonnet-", "claude-fable-")


class RefusalError(RuntimeError):
    pass


class ClaudeClient:
    name = "claude"

    def __init__(self, role, ledger, model=None, effort=None, sdk=None):
        import anthropic  # only needed in live mode
        self.role, self.ledger = role, ledger
        self.model = model or ROUTES[role]["model"]
        self.effort = effort or ROUTES[role]["effort"]
        self.sdk = sdk or anthropic.Anthropic(api_key=api_key(), max_retries=4)

    def __call__(self, system, messages, max_tokens=4000, session="-"):
        self.ledger.check()
        kw = dict(model=self.model, max_tokens=max_tokens, messages=messages,
                  system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
                  output_config={"effort": self.effort})
        t0 = time.time()
        if self.model.startswith(FALLBACK_OK):
            resp = self.sdk.beta.messages.create(**kw, betas=["server-side-fallback-2026-07-01"], fallbacks="default")
        else:
            resp = self.sdk.messages.create(**kw)
        self.ledger.record(session=session, role=self.role, model=self.model, effort=self.effort,
                           usage=resp.usage, latency_s=time.time() - t0)
        if resp.stop_reason == "refusal":
            raise RefusalError("The model declined this request.")
        return "".join(b.text for b in resp.content if b.type == "text")


class OfflineClient:
    name = "offline"


# Claude Code cloud sessions reserve ANTHROPIC_API_KEY, so a second name is accepted too.
KEY_VARS = ("ANTHROPIC_API_KEY", "HR_APPS_ANTHROPIC_KEY")


def api_key():
    return next((os.environ[v] for v in KEY_VARS if os.environ.get(v)), None)


def make_clients(ledger=None, offline=False):
    if offline or not api_key():
        return {"persona": OfflineClient(), "analyst": OfflineClient()}
    ledger = ledger or Ledger()
    return {role: ClaudeClient(role, ledger) for role in ROUTES}


def parse_json(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("no JSON in model reply: " + text[:200])
    return json.loads(m.group(0))

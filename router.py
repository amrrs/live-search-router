"""Routing layer: decide whether a query needs live search data.

Routes:
  direct            -> stable knowledge; answer without searching.
  search_and_answer -> one live lookup (Google) is enough.
  deep_research     -> fast-moving or comparative topic; pull Google Search + Google News.

Two interchangeable routers:
  LLMRouter       -> classifies with any OpenAI-compatible chat endpoint (incl. small
                     typed "system one" models - the slot TypeSafe Jev was built for).
  HeuristicRouter -> zero-dependency keyword/recency rules; always works, and is what
                     the demo uses when no LLM endpoint is configured.
"""
import json
import os
import re
import urllib.request

ROUTES = ("direct", "search_and_answer", "deep_research")

FRESHNESS_TERMS = [
    "today", "tonight", "yesterday", "this week", "this month", "this year", "latest", "current",
    "currently", "now", "recent", "recently", "news", "update", "updated", "release",
    "released", "launch", "launched", "announce", "announced", "price", "pricing",
    "cost", "deadline", "schedule", "weather", "score", "stock", "version", "2025", "2026",
]
RESEARCH_TERMS = [
    "compare", "comparison", "vs", "versus", "difference between", "pros and cons",
    "best", "top ", "overview", "market", "landscape", "alternatives", "which should",
    "trend", "trends", "analysis", "deep dive", "research",
]


class RouteDecision:
    def __init__(self, route, reason, router):
        if route not in ROUTES:
            route = "search_and_answer"
        self.route = route
        self.reason = reason
        self.router = router

    def __repr__(self):
        return f"RouteDecision(route={self.route!r}, router={self.router!r}, reason={self.reason!r})"


class HeuristicRouter:
    """Deterministic keyword router. No network, no dependencies."""

    name = "heuristic"

    def route(self, query):
        q = query.lower().strip()
        def matches(term):
            return bool(re.search(r"(?<!\w)" + re.escape(term.strip()) + r"(?!\w)", q))
        fresh = [t for t in FRESHNESS_TERMS if matches(t)]
        volatile = re.search(r"\b(ceo|president|prime minister|mayor|governor|raining|rain|temperature|exchange rate|gold rate|opening hours|open now|available|availability|election|winner|won|standings|flight|hotel|restaurant|pizza|cafe|near me|job|vacancy)\b", q)
        local = re.search(r"\b(places|restaurants?|pizza|cafes?|hotels?|near me)\b", q)
        research = [t for t in RESEARCH_TERMS if matches(t)]
        if local and not re.search(r"\b(compare|vs|versus|analysis|research)\b",q):
            return RouteDecision("search_and_answer", "local discovery needs a live lookup", self.name)
        if research:
            return RouteDecision("deep_research", "multi-source research signals: " + ", ".join(research), self.name)
        if fresh or volatile:
            return RouteDecision("search_and_answer", "freshness or changing-world facts require live evidence", self.name)
        stable = re.search(r"capital of|who wrote|who painted|chemical symbol|continents|speed of light|largest planet|reverse a string|http stand for|binary tree|formula|plot of|photosynthesis|pythagorean|\b(define|definition|arithmetic|algebra|multiplication)\b|^explain (what |how )?",q)
        if stable:
            return RouteDecision("direct", "recognized stable-knowledge intent; no freshness signals", self.name)
        return RouteDecision("search_and_answer", "uncertain freshness: conservative live lookup instead of silent direct answer", self.name)


class LLMRouter:
    """Classify with any OpenAI-compatible chat-completions endpoint.

    Env: ROUTER_LLM_BASE_URL (e.g. https://api.openai.com/v1), ROUTER_LLM_API_KEY,
    ROUTER_LLM_MODEL. The prompt forces a typed JSON answer, so a small classifier
    model (e.g. TypeSafe Jev) can own this slot; any chat model works too.
    """

    name = "llm"

    PROMPT = (
        "You are a routing classifier. Given a user query, decide how it should be answered.\n"
        "Routes:\n"
        '- "direct": stable knowledge, no current data needed.\n'
        '- "search_and_answer": needs one current web lookup (news, prices, releases, dates).\n'
        '- "deep_research": comparative/fast-moving topic needing multiple sources.\n'
        'Respond with JSON only: {"route": one of the three, "reason": short string}.\n'
        "Query: %s"
    )

    def __init__(self, base_url=None, api_key=None, model=None, fallback=None):
        self.base_url = (base_url or os.environ.get("ROUTER_LLM_BASE_URL", "")).rstrip("/")
        self.api_key = api_key or os.environ.get("ROUTER_LLM_API_KEY", "")
        self.model = model or os.environ.get("ROUTER_LLM_MODEL", "")
        self.fallback = fallback or HeuristicRouter()

    @property
    def configured(self):
        return bool(self.base_url and self.api_key and self.model)

    def route(self, query):
        if not self.configured:
            d = self.fallback.route(query)
            d.reason += " (LLM router not configured, used heuristic)"
            return d
        body = json.dumps(
            {
                "model": self.model,
                "messages": [{"role": "user", "content": self.PROMPT % query}],
                "temperature": 0,
            }
        ).encode()
        req = urllib.request.Request(
            self.base_url + "/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + self.api_key,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode())
            text = payload["choices"][0]["message"]["content"]
            parsed = json.loads(text[text.find("{"): text.rfind("}") + 1])
            return RouteDecision(parsed.get("route", ""),
                                 parsed.get("reason", ""), self.name)
        except Exception as e:  # fall back, never crash the pipeline
            d = self.fallback.route(query)
            d.reason += f" (LLM router failed: {e}; used heuristic)"
            return d


def get_router():
    """LLM router when configured, otherwise heuristic."""
    llm = LLMRouter()
    return llm if llm.configured else llm.fallback

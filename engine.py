"""Pipeline: route the query, fetch live data via SerpApi, answer with citations."""
import json
import os
import urllib.request

from router import get_router
from serpapi_client import SerpApiClient

DIRECT_NOTE = (
    "Routed DIRECT: answered from stable knowledge, no search credits spent."
)


def _llm_available():
    return bool(os.environ.get("ANSWER_LLM_BASE_URL") and os.environ.get("ANSWER_LLM_API_KEY")
                and os.environ.get("ANSWER_LLM_MODEL"))


def _llm_synthesize(query, sources):
    """Optional: synthesize the final answer with any OpenAI-compatible endpoint."""
    base = os.environ["ANSWER_LLM_BASE_URL"].rstrip("/")
    key = os.environ["ANSWER_LLM_API_KEY"]
    model = os.environ["ANSWER_LLM_MODEL"]
    src = "\n".join(f"[{i}] {s['title']} ({s['link']}): {s['snippet']}" for i,s in enumerate(sources,1))
    prompt = (
        "Answer the query using ONLY the sources below. Cite sources inline as [1], [2], ... "
        "matching the order given. Be concise.\n\nQuery: %s\n\nSources:\n%s"
        % (query, src)
    )
    if not sources:
        prompt = "Answer this stable-knowledge question concisely. Do not claim to have searched or cite invented sources. Query: " + query
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 650,
    }).encode()
    req = urllib.request.Request(
        base + "/chat/completions", data=body,
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + key},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode())
    return payload["choices"][0]["message"]["content"].strip()


def _extractive_answer(query, sources):
    """Zero-LLM fallback: return the best snippets as the answer, cited."""
    lines = []
    for i, s in enumerate(sources, 1):
        date = f" ({s['date']})" if s.get("date") else ""
        snippet = s["snippet"] or s["title"]
        lines.append(f"[{i}] {snippet}{date} - {s['title']}")
    return "Top live results for your query:\n" + "\n".join(lines)


def answer(query, client=None, router=None, num=5):
    """Full pipeline. Returns a dict: route, reason, answer, sources, searches_used."""
    router = router or get_router()
    decision = router.route(query)
    sources, searches = [], 0

    if decision.route == "direct":
        text = "No answer model configured. This stable query needs no live search; configure ANSWER_LLM_* to answer it."
        if _llm_available():
            text = _llm_synthesize(query, [])
        return {
            "query": query,
            "route": decision.route,
            "router": decision.router,
            "reason": decision.reason,
            "answer": text,
            "sources": [],
            "searches_used": 0,
        }

    client = client or SerpApiClient()
    if decision.route == "search_and_answer":
        data = client.search(query, engine="google", num=num)
        searches += 1
        sources = SerpApiClient.organic_results(data, limit=num)
    else:  # deep_research: two engines, merged and deduped
        data = client.search(query, engine="google", num=num)
        searches += 1
        sources = SerpApiClient.organic_results(data, limit=num)
        news = client.search(query, engine="google_news", num=num)
        searches += 1
        seen = {s["link"] for s in sources}
        for s in SerpApiClient.news_results(news, limit=num):
            if s["link"] not in seen:
                sources.append(s)
                seen.add(s["link"])

    if _llm_available():
        try:
            text = _llm_synthesize(query, sources)
        except Exception as e:
            text = _extractive_answer(query, sources) + f"\n\n(LLM synthesis failed: {e})"
    else:
        text = _extractive_answer(query, sources)

    return {
        "query": query,
        "route": decision.route,
        "router": decision.router,
        "reason": decision.reason,
        "answer": text,
        "sources": sources,
        "searches_used": searches,
    }

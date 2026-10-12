# live-search-router

A query router that decides **when an AI answer needs live search data** - and gets it from SerpApi.

Built for the **SerpApi India Hackathon 2026**, track: **AI Agents**.

[Watch the 36-second narrated local browser demo](https://github.com/amrrs/live-search-router/releases/tag/demo-v3): stable answering, live retrieval, Search + News, and a repeat with two cache hits / zero new API calls.

## The idea

LLM apps either search for everything (slow, expensive, and stale-prone answers anyway) or never search (confidently wrong about anything recent). This project puts a routing layer in front:

1. **Route** - classify each query: `direct`, `search_and_answer`, or `deep_research`.
2. **Fetch** - only the routes that need current data call SerpApi (Google Search; deep research adds Google News and dedupes).
3. **Answer** - respond with citations to the live sources, or answer directly when no search is needed.

The router is a **slot**, not a hard-coded model: any OpenAI-compatible endpoint can own it, including small typed classifier models (the design is shaped so a "system one" model such as TypeSafe Jev can drop in). Without any LLM configured, a deterministic heuristic router keeps the whole pipeline working.

## How SerpApi is used

SerpApi is the project's only live-data source, on the critical path:

- `search_and_answer` - one `google` engine call per query.
- `deep_research` - `google` + `google_news` calls, results merged and deduped by URL.
- `direct` - zero searches. Saving credits *is* the feature: the router spends SerpApi calls only where freshness matters.

## Setup

Requires Python 3.9+. **No pip install needed** - the project uses only the standard library.

```bash
git clone https://github.com/amrrs/live-search-router.git
cd live-search-router
export SERPAPI_API_KEY=your_key        # free key: https://serpapi.com/users/sign_up (250 searches/month free)
python demo.py
```

Optional - use an LLM for routing and/or answer synthesis (any OpenAI-compatible endpoint):

```bash
export ROUTER_LLM_BASE_URL=https://api.openai.com/v1
export ROUTER_LLM_API_KEY=...
export ROUTER_LLM_MODEL=gpt-4o-mini
export ANSWER_LLM_BASE_URL=https://api.openai.com/v1
export ANSWER_LLM_API_KEY=...
export ANSWER_LLM_MODEL=gpt-4o-mini
```

## Demo

```bash
python demo.py            # 3 built-in queries, one per route
python demo.py "your question here"
python demo.py --direct-only   # routing decisions only, spends no SerpApi credits
```

Expected output: each query prints its route, why it was routed there, the answer, and the sources used.

## Benchmark

`python benchmark.py` runs a routing benchmark over 38 hand-labeled queries (plus a small live latency sample, ~6 SerpApi calls). Latest results in `BENCHMARK.md`:

- Development regression coverage (heuristic): 38/38 after policy fixes; this is not held-out routing accuracy. See BENCHMARK.md.
- SerpApi searches: 50% fewer than an always-deep-search baseline; 12/38 queries answered with 0 searches
- Latency: routing decision ~0.01 ms local; current benchmark is offline; earlier live latency is not a current performance guarantee

## Files

| file | role |
|---|---|
| `router.py` | routing layer: `HeuristicRouter` (zero-dep) + `LLMRouter` (OpenAI-compatible slot) |
| `serpapi_client.py` | thin SerpApi client (Google Search + Google News), stdlib only |
| `engine.py` | pipeline: route -> search -> answer with citations |
| `demo.py` | CLI demo |
| `test_router.py` | routing unit tests |
| `benchmark.py` | routing benchmark (accuracy, search savings, latency) -> `BENCHMARK.md` |

## Notes

- AI tools used: built with AI assistance (listed per hackathon disclosure rules).
- License: MIT.

## Local browser demo

Copy `.env.example` to `.env`, add your SerpApi key and optional ANSWER_LLM settings, then run `python3 app.py` and open http://127.0.0.1:8765. The browser offers examples for all three routes, source links and per-answer/session search counts. Secrets are only read by the local server. Direct routing works without a SerpApi key; answering arbitrary stable questions requires an answer LLM. Without one, the UI explicitly reports that no answer model is configured.

AI disclosure: the initial project was supplied by the participant as a Drive ZIP with prior AI assistance; Codex reviewed it, fixed the direct-answer path and numbered citations, and added/tested the local browser demo. Nebius Token Factory provides optional answer synthesis.

## Conservative freshness policy and observable retrieval

The heuristic now uses token boundaries, recognizes changing office holders, rain/weather and local discovery, and defaults unfamiliar intents to a live lookup. Only recognized stable intents take the direct route. This deliberately prefers spending a search over silently treating uncertainty as timeless knowledge. It is a transparent policy, not a calibrated probability classifier.

SQLite caches retrieval payloads for 300 seconds, keyed by engine/query/parameters with secrets excluded. Set SEARCH_CACHE_TTL=0 to disable, or change SEARCH_CACHE_PATH. Each answer distinguishes planned engine lookups, actual network searches and cache hits; the trace shows engine, hit/miss, age and latency. Google + News results deduplicate exact URLs. Empty retrieval abstains. Invalid citation numbers trigger extractive fallback. Source snippets are untrusted data in the synthesis system prompt. This mitigates prompt injection; it does not prove source reliability or entailment.

The revised 38-query regression set scores 38/38 after fixing the original rain/local cases and correcting the Prime Minister label to require live search. This set informed development, so 100% is regression coverage, not held-out accuracy. There are 38 planned searches vs 76 always-deep, but no savings vs the always-one-search baseline on this mix. Caching saves repeated network calls separately. Run `python3 -m unittest discover` for nine tests covering freshness, no-key direct routing, cache expiry, empty evidence and invalid citations.

The demo narration uses ElevenLabs TTS Turbo v2.5 through fal.ai. The real ScreenStudioly video is preserved, with synchronized narration and selectable English subtitles.

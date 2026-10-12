# live-search-router

A query router that decides **when an AI answer needs live search data** - and gets it from SerpApi.

Built for the **SerpApi India Hackathon 2026**, track: **AI Agents**.

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

- Routing accuracy (heuristic): 95% (36/38) - see the label-bias caveat in BENCHMARK.md before quoting this
- SerpApi searches: 51% fewer than an always-deep-search baseline; 14/38 queries answered with 0 searches
- Latency: routing decision ~0.01 ms local; SerpApi call ~68 ms avg (live sample)

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

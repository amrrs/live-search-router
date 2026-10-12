# Benchmark results - live-search-router

Run: 2026-10-12 18:36 IST (live latency sample)

## Routing accuracy (HeuristicRouter)

- 36/38 correct = **95%** (38 hand-labeled queries; see label-bias caveat below)

| query | expected | routed | ok |
|---|---|---|---|
| What is the capital of France? | direct | direct | yes |
| Who wrote Pride and Prejudice? | direct | direct | yes |
| What is the chemical symbol for gold? | direct | direct | yes |
| How many continents are there? | direct | direct | yes |
| What is the speed of light in a vacuum? | direct | direct | yes |
| Who painted the Mona Lisa? | direct | direct | yes |
| What is the largest planet in the solar system? | direct | direct | yes |
| How do you reverse a string in Python? | direct | direct | yes |
| What does HTTP stand for? | direct | direct | yes |
| Explain what a binary tree is | direct | direct | yes |
| What is the formula for the area of a circle? | direct | direct | yes |
| Summarize the plot of Hamlet | direct | direct | yes |
| What is the latest pricing for OpenAI API models? | search_and_answer | search_and_answer | yes |
| Who won the IPL final this year? | search_and_answer | search_and_answer | yes |
| What is the current price of Bitcoin? | search_and_answer | search_and_answer | yes |
| Latest iPhone release date | search_and_answer | search_and_answer | yes |
| Weather in Bengaluru today | search_and_answer | search_and_answer | yes |
| Recent updates to the Python language | search_and_answer | search_and_answer | yes |
| Latest news about ISRO launches | search_and_answer | search_and_answer | yes |
| Current exchange rate USD to INR | search_and_answer | search_and_answer | yes |
| Who is the current CEO of X? | search_and_answer | search_and_answer | yes |
| Recent layoffs announced by tech companies | search_and_answer | search_and_answer | yes |
| Today's gold rate in Chennai | search_and_answer | search_and_answer | yes |
| Best pizza places in Bengaluru | search_and_answer | deep_research | MISS |
| Compare Fireworks AI vs Baseten vs Together AI for LLM infer | deep_research | deep_research | yes |
| Best open-source LLMs for code generation in 2026 | deep_research | deep_research | yes |
| Pros and cons of RAG vs fine-tuning | deep_research | deep_research | yes |
| MacBook Air vs Dell XPS for developers: which should I buy? | deep_research | deep_research | yes |
| Overview of the vector database market | deep_research | deep_research | yes |
| Trends in AI inference costs | deep_research | deep_research | yes |
| AWS vs GCP vs Azure for a startup | deep_research | deep_research | yes |
| Top framework alternatives to LangChain | deep_research | deep_research | yes |
| Difference between Kubernetes and Docker Swarm | deep_research | deep_research | yes |
| Market landscape for AI coding assistants | deep_research | deep_research | yes |
| Latest benchmarks: GPT-5 vs Gemini | deep_research | deep_research | yes |
| Research the best vector databases for RAG applications | deep_research | deep_research | yes |
| Is it raining in Mumbai? | search_and_answer | direct | MISS |
| Who is the Prime Minister of India? | direct | direct | yes |

Misses: 2
- "Best pizza places in Bengaluru" - expected search_and_answer, got deep_research
- "Is it raining in Mumbai?" - expected search_and_answer, got direct

## SerpApi searches spent (computed from routing decisions, no live calls)

| policy | searches over the 38-query set |
|---|---|
| router (this project) | 37 |
| always 1 search | 38 |
| always deep (2 engines) | 76 |

Router saves **51%** of searches vs always-deep; vs always-1-search it spends -1 extra (deep routes use 2 engines by design). The direct route is the real win: 14 queries answered with 0 searches and no stale-data risk.

## Latency

- Routing decision (local, heuristic): avg 0.01 ms over 38 queries
- SerpApi call (live, 6 calls): avg 68 ms (min 49, max 89)
  - google: 66 ms
  - google: 72 ms
  - google: 89 ms
  - google: 67 ms
  - google_news: 68 ms
  - google_news: 49 ms

End-to-end estimate per route (route + searches x avg SerpApi latency):

| route | searches | est. latency |
|---|---|---|
| direct | 0 | ~0 ms |
| search_and_answer | 1 | ~69 ms |
| deep_research | 2 | ~137 ms |

## Caveats

- **Label bias:** queries were written by the same author as the heuristic rules, including a few intentionally tricky ones. Accuracy here is self-consistency on a small hand-made set, not a measured real-world rate.
- Latency depends on network and SerpApi load; the sample is 6 live calls.
- The LLM router slot is unbenchmarked (no endpoint configured during the run).

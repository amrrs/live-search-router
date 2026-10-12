#!/usr/bin/env python3
"""Benchmark for the routing layer.

Measures:
  1. Routing accuracy of HeuristicRouter over 36 labeled queries (12 per route).
  2. SerpApi searches the router policy spends vs naive baselines (computed, not live).
  3. Latency: local routing latency (measured) + live SerpApi call latency (measured
     on a small sample, 6 calls) + end-to-end estimate per route.

CAVEAT (read before quoting the accuracy number): the 36 queries were authored for
this benchmark by the same author as the heuristic rules. They include a handful of
deliberately tricky cases, but the label set is still biased toward what the router
handles well. Treat accuracy as self-consistency on a small hand-made set, not as a
measured real-world rate.

Usage: SERPAPI_API_KEY=... python benchmark.py          # full run (uses ~6 searches)
       python benchmark.py --offline                    # accuracy + savings only, 0 searches
"""
import json
import sys
import time
from collections import Counter

from router import HeuristicRouter
from serpapi_client import SerpApiClient

QUERIES = [
    # direct: stable knowledge (12)
    ("What is the capital of France?", "direct"),
    ("Who wrote Pride and Prejudice?", "direct"),
    ("What is the chemical symbol for gold?", "direct"),
    ("How many continents are there?", "direct"),
    ("What is the speed of light in a vacuum?", "direct"),
    ("Who painted the Mona Lisa?", "direct"),
    ("What is the largest planet in the solar system?", "direct"),
    ("How do you reverse a string in Python?", "direct"),
    ("What does HTTP stand for?", "direct"),
    ("Explain what a binary tree is", "direct"),
    ("What is the formula for the area of a circle?", "direct"),
    ("Summarize the plot of Hamlet", "direct"),
    # search_and_answer: one fresh lookup (12)
    ("What is the latest pricing for OpenAI API models?", "search_and_answer"),
    ("Who won the IPL final this year?", "search_and_answer"),
    ("What is the current price of Bitcoin?", "search_and_answer"),
    ("Latest iPhone release date", "search_and_answer"),
    ("Weather in Bengaluru today", "search_and_answer"),
    ("Recent updates to the Python language", "search_and_answer"),
    ("Latest news about ISRO launches", "search_and_answer"),
    ("Current exchange rate USD to INR", "search_and_answer"),
    ("Who is the current CEO of X?", "search_and_answer"),
    ("Recent layoffs announced by tech companies", "search_and_answer"),
    ("Today's gold rate in Chennai", "search_and_answer"),
    ("Best pizza places in Bengaluru", "search_and_answer"),  # tricky: 'best' pulls to deep
    # deep_research: comparative / multi-source (12)
    ("Compare Fireworks AI vs Baseten vs Together AI for LLM inference", "deep_research"),
    ("Best open-source LLMs for code generation in 2026", "deep_research"),
    ("Pros and cons of RAG vs fine-tuning", "deep_research"),
    ("MacBook Air vs Dell XPS for developers: which should I buy?", "deep_research"),
    ("Overview of the vector database market", "deep_research"),
    ("Trends in AI inference costs", "deep_research"),
    ("AWS vs GCP vs Azure for a startup", "deep_research"),
    ("Top framework alternatives to LangChain", "deep_research"),
    ("Difference between Kubernetes and Docker Swarm", "deep_research"),
    ("Market landscape for AI coding assistants", "deep_research"),
    ("Latest benchmarks: GPT-5 vs Gemini", "deep_research"),
    ("Research the best vector databases for RAG applications", "deep_research"),
    # deliberately tricky extras (unlabeled-bias control): counted in accuracy
    ("Is it raining in Mumbai?", "search_and_answer"),      # fresh but no keyword -> likely miss
    ("Who is the Prime Minister of India?", "search_and_answer"),       # stable-ish; debatable label
]

SEARCHES_PER_ROUTE = {"direct": 0, "search_and_answer": 1, "deep_research": 2}


def run_accuracy(router):
    rows, confusion = [], Counter()
    for q, expected in QUERIES:
        t0 = time.perf_counter()
        d = router.route(q)
        route_ms = (time.perf_counter() - t0) * 1000
        ok = d.route == expected
        confusion[(expected, d.route)] += 1
        rows.append({"query": q, "expected": expected, "got": d.route,
                     "ok": ok, "route_ms": route_ms})
    return rows, confusion


def run_latency(client):
    samples = []
    for engine, q in [("google", "OpenAI API pricing"),
                      ("google", "ISRO latest launch"),
                      ("google", "USD to INR"),
                      ("google", "Nebius Token Factory"),
                      ("google_news", "AI inference providers"),
                      ("google_news", "Fireworks AI funding")]:
        t0 = time.perf_counter()
        client.search(q, engine=engine, num=5)
        ms = (time.perf_counter() - t0) * 1000
        samples.append({"engine": engine, "ms": round(ms)})
    return samples


def main():
    offline = "--offline" in sys.argv
    router = HeuristicRouter()
    rows, confusion = run_accuracy(router)
    n = len(rows)
    correct = sum(1 for r in rows if r["ok"])
    accuracy = correct / n

    policy = sum(SEARCHES_PER_ROUTE[r["got"]] for r in rows)
    always_1 = n * 1
    always_deep = n * 2
    avg_route_ms = sum(r["route_ms"] for r in rows) / n

    lines = []
    lines.append("# Benchmark results - live-search-router")
    lines.append("")
    lines.append(f"Run: {time.strftime('%Y-%m-%d %H:%M %Z', time.localtime())} "
                 f"({'offline' if offline else 'live latency sample'})")
    lines.append("")
    lines.append("## Routing accuracy (HeuristicRouter)")
    lines.append("")
    lines.append(f"- {correct}/{n} correct = **{accuracy:.0%}** "
                 f"({len(QUERIES)} hand-labeled queries; see label-bias caveat below)")
    lines.append("")
    lines.append("| query | expected | routed | ok |")
    lines.append("|---|---|---|---|")
    for r in rows:
        lines.append(f"| {r['query'][:60]} | {r['expected']} | {r['got']} | "
                     f"{'yes' if r['ok'] else 'MISS'} |")
    misses = [r for r in rows if not r["ok"]]
    lines.append("")
    lines.append(f"Misses: {len(misses)}")
    for r in misses:
        lines.append(f"- \"{r['query']}\" - expected {r['expected']}, got {r['got']}")
    lines.append("")
    lines.append("## SerpApi searches spent (computed from routing decisions, no live calls)")
    lines.append("")
    lines.append("| policy | searches over the 38-query set |")
    lines.append("|---|---|")
    lines.append(f"| router (this project) | {policy} |")
    lines.append(f"| always 1 search | {always_1} |")
    lines.append(f"| always deep (2 engines) | {always_deep} |")
    lines.append("")
    saved_deep = (always_deep - policy) / always_deep
    lines.append(f"Router saves **{saved_deep:.0%}** of searches vs always-deep; "
                 f"vs always-1-search it spends {policy - always_1:+d} extra "
                 f"(deep routes use 2 engines by design). The direct route is the real win: "
                 f"{sum(1 for r in rows if r['got']=='direct')} queries answered with 0 searches "
                 f"with no search calls.")
    lines.append("")
    lines.append("## Latency")
    lines.append("")
    lines.append(f"- Routing decision (local, heuristic): avg {avg_route_ms:.2f} ms over {n} queries")
    if not offline:
        client = SerpApiClient(timeout=40)
        samples = run_latency(client)
        avg_search = sum(s["ms"] for s in samples) / len(samples)
        lines.append(f"- SerpApi call (live, {len(samples)} calls): avg {avg_search:.0f} ms "
                     f"(min {min(s['ms'] for s in samples)}, max {max(s['ms'] for s in samples)})")
        for s in samples:
            lines.append(f"  - {s['engine']}: {s['ms']} ms")
        lines.append("")
        lines.append("End-to-end estimate per route (route + searches x avg SerpApi latency):")
        lines.append("")
        lines.append("| route | searches | est. latency |")
        lines.append("|---|---|---|")
        for route, s in SEARCHES_PER_ROUTE.items():
            est = avg_route_ms + s * avg_search
            lines.append(f"| {route} | {s} | ~{est:.0f} ms |")
    lines.append("")
    lines.append("## Caveats")
    lines.append("")
    lines.append("- **Label bias:** queries were written by the same author as the heuristic rules, "
                 "including a few intentionally tricky ones. Accuracy here is self-consistency on a "
                 "small hand-made set, not a measured real-world rate.")
    lines.append("- Latency depends on network and SerpApi load; the sample is 6 live calls.")
    lines.append("- The LLM router slot is unbenchmarked (no endpoint configured during the run).")

    report = "\n".join(lines)
    from pathlib import Path
    with Path(__file__).with_name("BENCHMARK.md").open("w") as f:
        f.write(report + "\n")
    print(report)


if __name__ == "__main__":
    main()

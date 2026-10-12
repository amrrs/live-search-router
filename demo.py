#!/usr/bin/env python3
"""Demo CLI: run queries through the live-search router.

Usage:
    SERPAPI_API_KEY=... python demo.py                 # run the 3 built-in demo queries
    SERPAPI_API_KEY=... python demo.py "your question" # route one question
    SERPAPI_API_KEY=... python demo.py --direct-only   # show routing without spending credits
"""
import sys

from engine import answer
from router import get_router

DEMO_QUERIES = [
    "What is the capital of France?",                       # -> direct
    "What is the latest pricing for OpenAI API models?",    # -> search_and_answer
    "Compare Fireworks AI vs Baseten vs Together AI for LLM inference",  # -> deep_research
]


def show(result):
    print("=" * 72)
    print("QUERY :", result["query"])
    print(f"ROUTE : {result['route']}  (router={result['router']}, searches={result['searches_used']})")
    print("WHY   :", result["reason"])
    print("ANSWER:")
    print(result["answer"])
    if result["sources"]:
        print("SOURCES:")
        for s in result["sources"]:
            print(" -", s["title"], "|", s["link"])
    print()


def main():
    args = [a for a in sys.argv[1:]]
    if args and args[0] == "--direct-only":
        router = get_router()
        for q in DEMO_QUERIES:
            d = router.route(q)
            print(f"{q}\n  -> {d.route} ({d.reason})\n")
        return
    queries = args if args else DEMO_QUERIES
    for q in queries:
        show(answer(q))


if __name__ == "__main__":
    main()

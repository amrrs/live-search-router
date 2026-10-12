# Live verification

October 12, 2026. Two consecutive identical deep-research requests using live SerpApi and Nebius synthesis. First request filled local SQLite cache; second reused it.

```json
[
  {
    "run": 1,
    "route": "deep_research",
    "network_searches": 2,
    "cache_hits": 0,
    "trace": [
      {
        "stage": "route",
        "route": "deep_research"
      },
      {
        "engine": "google",
        "cache": "miss",
        "age_seconds": 0,
        "latency_ms": 101.38
      },
      {
        "engine": "google_news",
        "cache": "miss",
        "age_seconds": 0,
        "latency_ms": 82.58
      },
      {
        "stage": "answer",
        "elapsed_ms": 2362.37
      }
    ],
    "warnings": []
  },
  {
    "run": 2,
    "route": "deep_research",
    "network_searches": 0,
    "cache_hits": 2,
    "trace": [
      {
        "stage": "route",
        "route": "deep_research"
      },
      {
        "engine": "google",
        "cache": "hit",
        "age_seconds": 2.26,
        "latency_ms": 0.35
      },
      {
        "engine": "google_news",
        "cache": "hit",
        "age_seconds": 2.18,
        "latency_ms": 0.1
      },
      {
        "stage": "answer",
        "elapsed_ms": 3341.36
      }
    ],
    "warnings": []
  }
]
```

Nine automated tests also pass. Cache TTL is five minutes; results remain a snapshot. This sample measures retrieval reuse, not general model quality.

"""Thin SerpApi client (stdlib only).

Covers the two engines this project uses: Google Search and Google News.
Docs: https://serpapi.com/search-api
"""
import json
import sqlite3
import hashlib
import time
from pathlib import Path
import os
import urllib.parse
import urllib.request

API_BASE = "https://serpapi.com/search.json"


class SerpApiError(RuntimeError):
    pass


class SerpApiClient:
    def __init__(self, api_key=None, timeout=20):
        self.api_key = api_key or os.environ.get("SERPAPI_API_KEY")
        if not self.api_key:
            raise SerpApiError(
                "No SerpApi key. Set SERPAPI_API_KEY (free key: https://serpapi.com/users/sign_up)."
            )
        self.timeout = timeout
        self.network_calls = 0
        self.cache_hits = 0
        self.trace = []
        self.cache_path = os.environ.get("SEARCH_CACHE_PATH", str(Path(__file__).with_name("search-cache.sqlite3")))
        self.cache_ttl = int(os.environ.get("SEARCH_CACHE_TTL", "300"))

    def search(self, query, engine="google", num=5, **params):
        """Run one SerpApi search and return the parsed JSON dict."""
        q = {
            "engine": engine,
            "q": query,
            "api_key": self.api_key,
            "num": num,
            "hl": "en",
        }
        q.update(params)
        cache_key = hashlib.sha256(json.dumps({k:v for k,v in q.items() if k != "api_key"},sort_keys=True).encode()).hexdigest()
        started = time.perf_counter()
        with sqlite3.connect(self.cache_path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS results (key TEXT PRIMARY KEY, created REAL, payload TEXT)")
            row = db.execute("SELECT created,payload FROM results WHERE key=?",(cache_key,)).fetchone()
        if row and time.time()-row[0] < self.cache_ttl:
            self.cache_hits += 1
            self.trace.append({"engine":engine,"cache":"hit","age_seconds":round(time.time()-row[0],2),"latency_ms":round((time.perf_counter()-started)*1000,2)})
            return json.loads(row[1])
        url = API_BASE + "?" + urllib.parse.urlencode(q)
        req = urllib.request.Request(url, headers={"User-Agent": "live-search-router/0.1"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise SerpApiError(f"SerpApi HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}")
        self.network_calls += 1
        if "error" in data:
            raise SerpApiError(f"SerpApi error: {data['error']}")
        with sqlite3.connect(self.cache_path) as db:
            db.execute("INSERT OR REPLACE INTO results VALUES (?,?,?)",(cache_key,time.time(),json.dumps(data)))
        self.trace.append({"engine":engine,"cache":"miss","age_seconds":0,"latency_ms":round((time.perf_counter()-started)*1000,2)})
        return data

    @staticmethod
    def organic_results(data, limit=5):
        """Normalize organic results into {title, link, snippet, date}."""
        out = []
        for r in data.get("organic_results", [])[:limit]:
            out.append(
                {
                    "title": r.get("title", ""),
                    "link": r.get("link", ""),
                    "snippet": r.get("snippet", ""),
                    "date": r.get("date", ""),
                }
            )
        return out

    @staticmethod
    def news_results(data, limit=5):
        """Normalize Google News results into the same shape."""
        out = []
        for r in data.get("news_results", [])[:limit]:
            out.append(
                {
                    "title": r.get("title", ""),
                    "link": r.get("link", ""),
                    "snippet": r.get("snippet", ""),
                    "date": r.get("date", ""),
                    "source": (r.get("source") or {}).get("name", "")
                    if isinstance(r.get("source"), dict)
                    else r.get("source", ""),
                }
            )
        return out

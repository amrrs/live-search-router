"""Thin SerpApi client (stdlib only).

Covers the two engines this project uses: Google Search and Google News.
Docs: https://serpapi.com/search-api
"""
import json
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
        url = API_BASE + "?" + urllib.parse.urlencode(q)
        req = urllib.request.Request(url, headers={"User-Agent": "live-search-router/0.1"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise SerpApiError(f"SerpApi HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}")
        if "error" in data:
            raise SerpApiError(f"SerpApi error: {data['error']}")
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

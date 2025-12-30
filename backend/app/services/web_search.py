from __future__ import annotations

import httpx

from app.config import get_settings


class WebSearchError(RuntimeError):
    pass


def tavily_search(*, query: str, max_results: int = 5) -> list[dict]:
    settings = get_settings()
    if not settings.tavily_api_key:
        raise WebSearchError("TAVILY_API_KEY not set")

    payload = {"api_key": settings.tavily_api_key, "query": query, "max_results": max_results}
    with httpx.Client(timeout=20) as client:
        r = client.post("https://api.tavily.com/search", json=payload)
        r.raise_for_status()
        data = r.json()

    results = data.get("results") or []
    # Normalize to title/url/snippet
    out: list[dict] = []
    for item in results[:max_results]:
        out.append(
            {
                "title": item.get("title"),
                "url": item.get("url"),
                "snippet": item.get("content") or item.get("snippet"),
            }
        )
    return out



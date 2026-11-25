from urllib.request import urlopen
import json
import os
from typing import Dict, List, Optional

BASE_API = "https://siiberram.github.io/Sii-Football/api"
VALID_CATEGORIES = ("amputee-football", "blind-football", "cp-football")


def get_json(endpoint: str, local_dir: Optional[str] = None) -> dict:
    clean_name = endpoint.lstrip("/")
    if local_dir:
        local_path = os.path.join(local_dir, clean_name)
        if os.path.exists(local_path):
            with open(local_path, "r", encoding="utf-8") as f:
                return json.load(f)

    url = f"{BASE_API}/{clean_name}"
    with urlopen(url, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_para_football_bundle(local_dir: Optional[str] = None) -> dict:
    return {
        "index": get_json("index.json", local_dir=local_dir),
        "sources": get_json("sources.json", local_dir=local_dir),
        "leagues": get_json("leagues.json", local_dir=local_dir),
        "standings": get_json("standings.json", local_dir=local_dir),
        "news": get_json("news.json", local_dir=local_dir),
        "disclaimer": get_json("disclaimer.json", local_dir=local_dir),
    }


def _normalize_category(category: str) -> str:
    cat = (category or "").strip().lower()
    if cat not in VALID_CATEGORIES:
        raise ValueError(f"Unsupported category '{category}'. Expected one of: {VALID_CATEGORIES}")
    return cat


def filter_competitions_by_category(bundle: dict, category: str) -> List[dict]:
    cat = _normalize_category(category)
    competitions = bundle.get("leagues", {}).get("competitions", [])
    return [c for c in competitions if c.get("category", "").lower() == cat]


def filter_matches_by_category(bundle: dict, category: str) -> List[dict]:
    cat = _normalize_category(category)
    matches = bundle.get("leagues", {}).get("matches", [])
    return [m for m in matches if m.get("category", "").lower() == cat]


def filter_standings_by_category(bundle: dict, category: str) -> List[dict]:
    cat = _normalize_category(category)
    standings = bundle.get("standings", {}).get("standings", [])
    rows = [s for s in standings if s.get("category", "").lower() == cat]
    return sorted(rows, key=lambda r: (r.get("position", 999), -r.get("points", 0)))


def filter_news_by_category(bundle: dict, category: str, limit: int = 5) -> List[dict]:
    cat = _normalize_category(category)
    items = [
        item for item in bundle.get("news", {}).get("items", [])
        if item.get("status") == "ok" and item.get("category", "").lower() == cat
    ]
    return [
        {
            "id": item.get("id"),
            "source_name": item.get("source_name"),
            "source_url": item.get("source_url"),
            "source_type": item.get("source_type"),
            "excerpt": item.get("excerpt", ""),
            "fetched_at": item.get("fetched_at"),
        }
        for item in items[:limit]
    ]


def build_siimatchmind_summary(bundle: dict) -> Dict[str, dict]:
    leagues = bundle.get("leagues", {})
    categories_summary = {}

    for cat in VALID_CATEGORIES:
        comps = filter_competitions_by_category(bundle, cat)
        matches = filter_matches_by_category(bundle, cat)
        standings = filter_standings_by_category(bundle, cat)
        news = filter_news_by_category(bundle, cat, limit=3)

        categories_summary[cat] = {
            "competitions_count": len(comps),
            "matches_count": len(matches),
            "standings_count": len(standings),
            "news_count": len(news),
            "latest_matches": matches[:5],
            "top_standings": standings[:5],
            "latest_news": news,
        }

    return {
        "app": "SiiMatchMind",
        "source_project": "Sii-Football",
        "updated_at": leagues.get("updated_at"),
        "totals": {
            "competitions": leagues.get("competitions_count", 0),
            "matches": leagues.get("matches_count", 0),
            "standings": bundle.get("standings", {}).get("standings_count", 0),
            "news": bundle.get("news", {}).get("count", 0),
        },
        "categories": categories_summary,
        "attribution_license": bundle.get("disclaimer", {}).get("license"),
    }


if __name__ == "__main__":
    local_api = "api" if os.path.isdir("api") else None
    bundle = fetch_para_football_bundle(local_dir=local_api)
    summary = build_siimatchmind_summary(bundle)
    print(json.dumps(summary, ensure_ascii=False, indent=2))

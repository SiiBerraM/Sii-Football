import json
import os
import sys
from datetime import datetime

EXPECTED_CATEGORIES = [
    "amputee-football",
    "blind-football",
    "cp-football",
    "world-football",
    "basketball",
    "motorsport",
    "tennis",
    "multi-sport",
]

REQUIRED_SCHEMAS = {
    "api/index.json": ["service", "base_url", "endpoints", "categories"],
    "api/sources.json": ["sources"],
    "api/news.json": ["count", "items", "updated_at"],
    "api/leagues.json": ["competitions_count", "competitions", "matches_count", "matches", "by_category"],
    "api/standings.json": ["standings_count", "standings", "updated_at"],
    "api/disclaimer.json": ["project", "license", "terms"],
}

def _is_valid_iso_timestamp(val):
    if not isinstance(val, str) or not val.strip():
        return False
    try:
        datetime.fromisoformat(val.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False

def main():
    errors = []
    loaded = {}

    for path, keys in REQUIRED_SCHEMAS.items():
        if not os.path.exists(path):
            errors.append(f"Missing file: {path}")
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                errors.append(f"Invalid root JSON object in {path}")
                continue
            loaded[path] = data
            for k in keys:
                if k not in data:
                    errors.append(f"Missing key '{k}' in {path}")
        except Exception as exc:
            errors.append(f"JSON decode error in {path}: {exc}")

    leagues = loaded.get("api/leagues.json", {})
    for m in leagues.get("matches", []):
        for req_field in ["match_id", "category", "home_team", "away_team", "home_score", "away_score", "source_name", "source_url"]:
            if req_field not in m or m[req_field] in (None, ""):
                errors.append(f"Match missing '{req_field}': {m}")
        cat = m.get("category")
        if cat not in EXPECTED_CATEGORIES:
            errors.append(f"Invalid match category '{cat}'")

    for path in ["api/news.json", "api/standings.json"]:
        d = loaded.get(path, {})
        if "updated_at" in d and not _is_valid_iso_timestamp(d.get("updated_at")):
            errors.append(f"Invalid updated_at in {path}: {d.get('updated_at')}")

    summary_path = "api/siimatchmind_summary.json"
    if os.path.exists(summary_path):
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                summary = json.load(f)
            if not _is_valid_iso_timestamp(summary.get("updated_at")):
                errors.append(f"Invalid updated_at in {summary_path}: {summary.get('updated_at')}")
            cats_map = summary.get("categories")
            if not isinstance(cats_map, dict):
                errors.append(f"Missing or invalid 'categories' dict in {summary_path}")
            else:
                for c in EXPECTED_CATEGORIES:
                    if c not in cats_map:
                        errors.append(f"Missing category '{c}' in {summary_path}")
        except Exception as exc:
            errors.append(f"JSON decode error in {summary_path}: {exc}")
    else:
        errors.append(f"Missing file: {summary_path}")

    if errors:
        for e in errors:
            print("ERROR:", e)
        sys.exit(1)

    news = loaded.get("api/news.json", {})
    standings = loaded.get("api/standings.json", {})

    print(
        f"VALIDATED OK | News: {news.get('count', 0)} | "
        f"Competitions: {leagues.get('competitions_count', 0)} | "
        f"Matches: {leagues.get('matches_count', 0)} | "
        f"Standings: {standings.get('standings_count', 0)}"
    )

if __name__ == "__main__":
    main()

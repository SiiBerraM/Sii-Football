import json
import os
import sys

REQUIRED_SCHEMAS = {
    "api/index.json": ["service", "base_url", "endpoints", "categories"],
    "api/sources.json": ["sources"],
    "api/news.json": ["count", "items", "updated_at"],
    "api/leagues.json": ["competitions_count", "competitions", "matches_count", "matches", "by_category"],
    "api/standings.json": ["standings_count", "standings", "updated_at"],
    "api/disclaimer.json": ["project", "license", "terms"],
}


def main():
    errors = []
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
            for k in keys:
                if k not in data:
                    errors.append(f"Missing key '{k}' in {path}")
        except Exception as exc:
            errors.append(f"JSON decode error in {path}: {exc}")

    if errors:
        for e in errors:
            print("ERROR:", e)
        sys.exit(1)

    with open("api/leagues.json", "r", encoding="utf-8") as f:
        leagues = json.load(f)
    with open("api/news.json", "r", encoding="utf-8") as f:
        news = json.load(f)
    with open("api/standings.json", "r", encoding="utf-8") as f:
        standings = json.load(f)

    print(
        f"VALIDATED OK | News: {news.get('count', 0)} | "
        f"Competitions: {leagues.get('competitions_count', 0)} | "
        f"Matches: {leagues.get('matches_count', 0)} | "
        f"Standings: {standings.get('standings_count', 0)}"
    )


if __name__ == "__main__":
    main()

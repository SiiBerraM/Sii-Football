import json
import os
import sys

REQUIRED_FILES = [
    "api/index.json",
    "api/sources.json",
    "api/news.json",
    "api/leagues.json",
    "api/standings.json",
    "api/disclaimer.json",
]


def main():
    errors = []
    for path in REQUIRED_FILES:
        if not os.path.exists(path):
            errors.append(f"Missing file: {path}")
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                errors.append(f"Invalid root JSON object in {path}")
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

    print(
        f"VALIDATED OK | News items: {news.get('count', 0)} | "
        f"Competitions: {leagues.get('competitions_count', 0)} | "
        f"Matches: {leagues.get('matches_count', 0)}"
    )


if __name__ == "__main__":
    main()

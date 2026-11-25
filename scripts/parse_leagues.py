import json
import os
import re
from datetime import datetime, timezone


def extract_matches_from_text(text: str, source_name: str, source_url: str, category: str, fetched_at: str):
    matches = []
    pattern = re.compile(r"([A-Z][A-Za-z0-9\s\-]{1,30}?)\s+(\d{1,2})\s*[-–]\s*(\d{1,2})\s+([A-Z][A-Za-z0-9\s\-]{1,30}?)(?=\s|$|[.,;])")
    for idx, m in enumerate(pattern.finditer(text), start=1):
        home = re.sub(r"\s+", " ", m.group(1)).strip()
        away = re.sub(r"\s+", " ", m.group(4)).strip()
        if len(home) < 2 or len(away) < 2:
            continue
        matches.append({
            "match_id": f"{category[:3]}-{idx}",
            "category": category,
            "home_team": home,
            "away_team": away,
            "home_score": int(m.group(2)),
            "away_score": int(m.group(3)),
            "status": "finished",
            "source_name": source_name,
            "source_url": source_url,
            "fetched_at": fetched_at,
        })
    return matches


def main():
    os.makedirs("api", exist_ok=True)
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    news_data = {"items": []}
    if os.path.exists("api/news.json"):
        with open("api/news.json", "r", encoding="utf-8") as f:
            news_data = json.load(f)

    all_matches = []
    for item in news_data.get("items", []):
        if item.get("status") != "ok":
            continue
        excerpt = item.get("excerpt", "")
        all_matches.extend(
            extract_matches_from_text(
                excerpt,
                item.get("source_name", "Para-Football Source"),
                item.get("source_url", ""),
                item.get("category", "para-football"),
                item.get("fetched_at", now_iso),
            )
        )

    leagues_payload = {
        "project": "Sii-Football",
        "consumer_app": "SiiMatchMind",
        "license_note": "Structured para-football match records from public HTML and PDF sources with attribution.",
        "updated_at": now_iso,
        "matches_count": len(all_matches),
        "matches": all_matches,
    }

    with open("api/leagues.json", "w", encoding="utf-8") as f:
        json.dump(leagues_payload, f, ensure_ascii=False, indent=2)

    print(f"Done. Extracted {len(all_matches)} structured matches -> api/leagues.json")


if __name__ == "__main__":
    main()

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


def extract_competitions(items: list, fetched_at: str):
    competitions = []
    seen_urls = set()
    for idx, item in enumerate(items, start=1):
        if item.get("status") != "ok":
            continue
        src_url = item.get("source_url", "")
        if src_url in seen_urls:
            continue
        seen_urls.add(src_url)
        competitions.append({
            "id": idx,
            "name": item.get("source_name", "Para-Football Competition"),
            "category": item.get("category", "para-football"),
            "source_type": item.get("source_type", "html"),
            "source_url": src_url,
            "discovered_pdfs": item.get("discovered_pdfs", []),
            "char_length": item.get("char_length", 0),
            "fetched_at": fetched_at,
        })
    return competitions


def main():
    os.makedirs("api", exist_ok=True)
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    news_data = {"items": []}
    if os.path.exists("api/news.json"):
        with open("api/news.json", "r", encoding="utf-8") as f:
            news_data = json.load(f)

    items = news_data.get("items", [])
    all_matches = []
    for item in items:
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

    competitions = extract_competitions(items, now_iso)

    leagues_payload = {
        "project": "Sii-Football",
        "consumer_app": "SiiMatchMind",
        "license_note": "Structured para-football leagues and match records from public HTML and PDF sources with attribution.",
        "updated_at": now_iso,
        "competitions_count": len(competitions),
        "competitions": competitions,
        "matches_count": len(all_matches),
        "matches": all_matches,
    }

    with open("api/leagues.json", "w", encoding="utf-8") as f:
        json.dump(leagues_payload, f, ensure_ascii=False, indent=2)

    print(f"Done. Competitions: {len(competitions)} | Matches: {len(all_matches)} -> api/leagues.json")


if __name__ == "__main__":
    main()

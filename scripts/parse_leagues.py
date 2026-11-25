import json
import os
import re
from datetime import datetime, timezone


def extract_matches_from_text(text: str, source_name: str, source_url: str, category: str, fetched_at: str):
    matches = []
    seen = set()
    patterns = [
        re.compile(
            r"\b([A-Za-z][A-Za-z0-9\s\.\'-]{1,25}?)\s+(\d{1,2})\s*(?:[-–:]|vs\.?)\s*(\d{1,2})\s+([A-Za-z][A-Za-z0-9\s\.\'-]{1,25}?)(?=\s|$|[.,;()|\[\]])"
        ),
        re.compile(
            r"\b([A-Za-z][A-Za-z0-9\s\.\'-]{1,25}?)\s+(?:vs\.?|v)\s+([A-Za-z][A-Za-z0-9\s\.\'-]{1,25}?)\s+(\d{1,2})\s*[-–:]\s*(\d{1,2})(?=\s|$|[.,;()|\[\]])",
            re.IGNORECASE,
        ),
    ]
    blocked_words = {"cookie", "privacy", "copyright", "version", "page", "http", "menu", "home", "news", "about", "contact", "login", "search"}

    for pat_idx, pattern in enumerate(patterns):
        for m in pattern.finditer(text):
            if pat_idx == 0:
                home, h_s, a_s, away = m.group(1), m.group(2), m.group(3), m.group(4)
            else:
                home, away, h_s, a_s = m.group(1), m.group(2), m.group(3), m.group(4)

            home = re.sub(r"\s+", " ", home).strip(" -–.:")
            away = re.sub(r"\s+", " ", away).strip(" -–.:")
            h_score = int(h_s)
            a_score = int(a_s)

            if len(home) < 2 or len(away) < 2 or home.lower() == away.lower():
                continue
            if h_score > 25 or a_score > 25:
                continue
            combined_tokens = set((home + " " + away).lower().split())
            if combined_tokens & blocked_words:
                continue

            key = (category, home.lower(), away.lower(), h_score, a_score)
            if key in seen:
                continue
            seen.add(key)
            matches.append({
                "match_id": f"{category[:3]}-{len(matches) + 1}",
                "category": category,
                "home_team": home.title(),
                "away_team": away.title(),
                "home_score": h_score,
                "away_score": a_score,
                "status": "finished",
                "source_name": source_name,
                "source_url": source_url,
                "fetched_at": fetched_at,
            })
    return matches


def extract_competitions(items: list, fetched_at: str):
    competitions = []
    seen_urls = set()
    for item in items:
        if item.get("status") != "ok":
            continue
        src_url = item.get("source_url", "")
        if not src_url or src_url in seen_urls:
            continue
        seen_urls.add(src_url)
        competitions.append({
            "id": len(competitions) + 1,
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
        blob = " ".join(filter(None, [item.get("full_text", ""), item.get("excerpt", "")]))
        all_matches.extend(
            extract_matches_from_text(
                blob,
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

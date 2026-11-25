import json
import os
import re
from datetime import datetime, timezone


def extract_standings_rows(text: str, source_name: str, source_url: str, category: str, fetched_at: str):
    rows = []
    seen = set()
    patterns = [
        re.compile(
            r"\b([1-9]|1[0-9]|20)\s+([A-Z][A-Za-z\s\.\'-]{2,24}?)\s+(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})\s+(\d{1,3})\b"
        ),
        re.compile(
            r"\b([1-9]|1[0-9]|20)\.\s+([A-Z][A-Za-z\s\.\'-]{2,24}?)\s+[-–|:]?\s*(\d{1,2})\s*(?:pts?|points?)\b",
            re.IGNORECASE,
        ),
    ]
    for idx, pattern in enumerate(patterns):
        for m in pattern.finditer(text):
            pos = int(m.group(1))
            team = re.sub(r"\s+", " ", m.group(2)).strip(" -–.:")
            if len(team) < 2:
                continue
            if idx == 0:
                played = int(m.group(3))
                won = int(m.group(4))
                drawn = int(m.group(5))
                lost = int(m.group(6))
                pts = int(m.group(7))
                if played < won + drawn + lost or pts > played * 6:
                    continue
            else:
                played = won = drawn = lost = 0
                pts = int(m.group(3))
            key = (category, team.lower(), pos)
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                "position": pos,
                "team": team.title(),
                "category": category,
                "played": played,
                "won": won,
                "drawn": drawn,
                "lost": lost,
                "points": pts,
                "source_name": source_name,
                "source_url": source_url,
                "fetched_at": fetched_at,
            })
    return rows


def main():
    os.makedirs("api", exist_ok=True)
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    news_data = {"items": []}
    if os.path.exists("api/news.json"):
        with open("api/news.json", "r", encoding="utf-8") as f:
            news_data = json.load(f)

    standings = []
    for item in news_data.get("items", []):
        if item.get("status") != "ok":
            continue
        blob = " ".join(filter(None, [item.get("full_text", ""), item.get("excerpt", "")]))
        standings.extend(
            extract_standings_rows(
                blob,
                item.get("source_name", "Para-Football Source"),
                item.get("source_url", ""),
                item.get("category", "para-football"),
                item.get("fetched_at", now_iso),
            )
        )

    payload = {
        "project": "Sii-Football",
        "consumer_app": "SiiMatchMind",
        "license_note": "Structured para-football standings from public HTML and PDF sources with attribution.",
        "updated_at": now_iso,
        "standings_count": len(standings),
        "standings": standings,
    }

    with open("api/standings.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Done. Standings rows: {len(standings)} -> api/standings.json")


if __name__ == "__main__":
    main()

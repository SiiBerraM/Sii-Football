import json
import os
import re
from datetime import datetime, timezone


def clean_prefix(category: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "", (category or "").lower())
    return (slug[:3] or "mat")


def _clean_team(name: str) -> str:
    cleaned = re.sub(r"\s+", " ", (name or "")).strip(" -–—.:|/()[]")
    cleaned = re.sub(r"^(?:vs\.?|v)\s+", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(
        r"^(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+(?:20\d{2}\s+)?",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()
    return cleaned.title()


def _is_valid_team_name(name: str, blocked_words: set) -> bool:
    cleaned = _clean_team(name)
    if len(cleaned) < 2 or len(cleaned) > 26:
        return False
    if not re.search(r"[A-Za-zÀ-ÿ]", cleaned):
        return False
    # Reject bracket/group codes or schedule codes like "E3 4Th B..."
    if re.search(r"\b(?:19|20)\d{2}[-/]\d{1,2}[-/]\d{1,2}\b", cleaned):
        return False
    if re.search(r"\b(?:1st|2nd|3rd|4th|5th|6th|7th|8th)\b", cleaned, flags=re.IGNORECASE):
        return False
    if len(cleaned.split()) > 4:
        return False
    if re.fullmatch(r"(?:19|20)\d{2}(?:\s*[-–/]\s*(?:19|20)\d{2})?", cleaned):
        return False
    tokens = set(re.findall(r"[a-z0-9]+", cleaned.lower()))
    if not tokens or (tokens & blocked_words):
        return False
    return True


def extract_matches_from_text(
    text: str,
    source_name: str,
    source_url: str,
    category: str,
    fetched_at: str,
    id_counters: dict,
    seen_matches: set,
):
    matches = []
    prefix = clean_prefix(category)
    id_counters.setdefault(prefix, 0)

    patterns = [
        re.compile(
            r"\b([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9\s\.\'\-]{1,28}?)\s+(\d{1,2})\s*[-–—]\s*(\d{1,2})\s*(?:\((?:a\.?e\.?t\.?|et|pen\.?|p)\))?\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9\s\.\'\-]{1,28}?)(?=\s|$|[.,;()|\[\]])",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9\s\.\'\-]{1,28}?)\s+(?:vs\.?|v)\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9\s\.\'\-]{1,28}?)\s+(\d{1,2})\s*[-–—:]\s*(\d{1,2})(?!\s*(?:am|pm)\b)(?=\s|$|[.,;()|\[\]])",
            re.IGNORECASE,
        ),
    ]

    blocked_words = {
        "cookie", "cookies", "privacy", "copyright", "version", "page", "http", "https",
        "menu", "home", "news", "about", "contact", "login", "search", "defeat", "win",
        "draw", "loss", "in", "on", "at", "to", "for", "from", "with", "by", "the", "and",
        "or", "of", "cup", "world", "euro", "championship", "tournaments", "results",
        "fixtures", "schedule", "schedules", "report", "reports", "live", "history",
        "rules", "table", "standings", "group", "stage", "final", "semi", "quarter",
        "round", "season", "year", "month", "day", "days", "time", "gmt", "utc", "am",
        "pm", "sep", "sept", "oct", "nov", "dec", "jan", "feb", "mar", "apr", "jun",
        "jul", "aug", "rest", "no", "matches", "match", "november", "december",
        "january", "february", "march", "april", "may", "june", "july", "august",
        "september", "october", "monday", "tuesday", "wednesday", "thursday", "friday",
        "mon", "tue", "wed", "thu", "fri", "sat", "sun", "saturday", "sunday", "venue", "stadium", "city", "location", "date", "dates",
        "vs", "each", "state", "currently", "has", "coaches", "plan", "development",
        "grassroots", "player", "players", "team", "teams"
    }

    for pat_idx, pattern in enumerate(patterns):
        for m in pattern.finditer(text or ""):
            if pat_idx == 0:
                home_raw, h_s, a_s, away_raw = m.group(1), m.group(2), m.group(3), m.group(4)
            else:
                home_raw, away_raw, h_s, a_s = m.group(1), m.group(2), m.group(3), m.group(4)

            if not _is_valid_team_name(home_raw, blocked_words) or not _is_valid_team_name(away_raw, blocked_words):
                continue

            home = _clean_team(home_raw)
            away = _clean_team(away_raw)
            h_score = int(h_s)
            a_score = int(a_s)

            if len(home) < 2 or len(away) < 2 or home.lower() == away.lower():
                continue
            if h_score > 25 or a_score > 25:
                continue

            key = (category, home.lower(), away.lower(), h_score, a_score)
            if key in seen_matches:
                continue
            seen_matches.add(key)

            id_counters[prefix] += 1
            matches.append({
                "match_id": f"{prefix}-{id_counters[prefix]}",
                "category": category,
                "home_team": home,
                "away_team": away,
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


def build_category_summary(competitions: list, matches: list):
    summary = {}
    for comp in competitions:
        cat = comp.get("category", "para-football")
        summary.setdefault(cat, {"competitions": 0, "matches": 0})
        summary[cat]["competitions"] += 1
    for match in matches:
        cat = match.get("category", "para-football")
        summary.setdefault(cat, {"competitions": 0, "matches": 0})
        summary[cat]["matches"] += 1
    return summary


def main():
    os.makedirs("api", exist_ok=True)
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    news_data = {"items": []}
    if os.path.exists("api/news.json"):
        with open("api/news.json", "r", encoding="utf-8") as f:
            news_data = json.load(f)

    items = news_data.get("items", [])
    all_matches = []
    id_counters = {}
    seen_matches = set()

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
                id_counters=id_counters,
                seen_matches=seen_matches,
            )
        )

    competitions = extract_competitions(items, now_iso)
    by_category = build_category_summary(competitions, all_matches)

    leagues_payload = {
        "project": "Sii-Football",
        "consumer_app": "SiiMatchMind",
        "license_note": "Structured para-football leagues and match records from public HTML and PDF sources with attribution.",
        "updated_at": now_iso,
        "by_category": by_category,
        "competitions_count": len(competitions),
        "competitions": competitions,
        "matches_count": len(all_matches),
        "matches": all_matches,
    }

    with open("api/leagues.json", "w", encoding="utf-8") as f:
        json.dump(leagues_payload, f, ensure_ascii=False, indent=2)

    print(f"Done. Competitions: {len(competitions)} | Matches: {len(all_matches)} | Categories: {list(by_category.keys())}")


if __name__ == "__main__":
    main()

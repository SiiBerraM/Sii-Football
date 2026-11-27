import json
import os
import re
from datetime import datetime, timezone


def _clean_team(raw: str) -> str:
    team = re.sub(r"\s+", " ", (raw or "")).strip(" -–—.:|/()[]")
    if len(team) < 2 or len(team) > 30:
        return ""
    if not re.search(r"[A-Za-zÀ-ÿ]", team):
        return ""
    if re.fullmatch(r"(?:19|20)\d{2}(?:\s*[-–/]\s*(?:19|20)\d{2})?", team):
        return ""
    bad_tokens = {
        "pos", "position", "rank", "team", "club", "nation", "country", "played",
        "mp", "p", "w", "d", "l", "won", "drawn", "lost", "pts", "points", "gd",
        "gf", "ga", "menu", "home", "news", "results", "standings", "table", "group"
    }
    tokens = set(re.findall(r"[a-z0-9]+", team.lower()))
    if not tokens or (tokens & bad_tokens):
        return ""
    return team.title()


def extract_standings_rows(text: str, source_name: str, source_url: str, category: str, fetched_at: str):
    rows = []
    seen = set()

    # Match rows with P, W, D, L and optional trailing columns (GF, GA, GD, Pts)
    # Using greedy trailing integer capture or taking the final number after W D L
    full_table_re = re.compile(
        r"\b([1-9]|1[0-9]|20)[\.\)\s]+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9\s\.\'\-]{1,26}?)\s+(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})(?:\s+[+-]?\d{1,3}){0,3}\s+(\d{1,3})\b"
    )

    ranked_pts_re = re.compile(
        r"\b([1-9]|1[0-9]|20)[\.\)]\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9\s\.\'\-]{1,26}?)\s*[-–—|:]?\s*(\d{1,3})\s*(?:pts?|points?)\b",
        re.IGNORECASE,
    )

    for m in full_table_re.finditer(text or ""):
        pos = int(m.group(1))
        team = _clean_team(m.group(2))
        if not team:
            continue
        played = int(m.group(3))
        won = int(m.group(4))
        drawn = int(m.group(5))
        lost = int(m.group(6))
        pts = int(m.group(7))

        if played < (won + drawn + lost) or played > 60 or pts > played * 6:
            continue

        # Sanity check: in standard football tables, points cannot be lower than `drawn`
        if pts < drawn:
            continue

        key = (category, team.lower(), pos)
        if key in seen:
            continue
        seen.add(key)

        rows.append({
            "position": pos,
            "team": team,
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

    for m in ranked_pts_re.finditer(text or ""):
        pos = int(m.group(1))
        team = _clean_team(m.group(2))
        if not team:
            continue
        pts = int(m.group(3))
        if pts > 200:
            continue

        key = (category, team.lower(), pos)
        if key in seen:
            continue
        seen.add(key)

        rows.append({
            "position": pos,
            "team": team,
            "category": category,
            "played": 0,
            "won": 0,
            "drawn": 0,
            "lost": 0,
            "points": pts,
            "source_name": source_name,
            "source_url": source_url,
            "fetched_at": fetched_at,
        })

    rows.sort(key=lambda r: (r["position"], -r["points"], r["team"]))
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

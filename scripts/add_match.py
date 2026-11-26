import argparse
import json
import os
import sys
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from sync_all import sync_project


def add_match(
    proj_dir: str,
    category: str,
    home_team: str,
    away_team: str,
    home_score: int,
    away_score: int,
    match_id: str | None = None,
    status: str = "finished",
    source_name: str = "Sii-Football Manual Entry",
    source_url: str = "https://siiberram.github.io/Sii-Football/",
) -> dict:
    api_dir = os.path.join(proj_dir, "api")
    matches_path = os.path.join(api_dir, "matches.json")

    with open(matches_path, "r", encoding="utf-8") as f:
        mdata = json.load(f)

    matches = mdata.get("matches", [])
    existing_ids = {str(m.get("match_id", "")) for m in matches}

    if not match_id:
        prefix = (category or "match").strip().lower().replace(" ", "-")
        idx = len(matches) + 1
        while f"{prefix}-{idx}" in existing_ids:
            idx += 1
        match_id = f"{prefix}-{idx}"
    elif match_id in existing_ids:
        raise ValueError(f"Duplicate match_id: {match_id}")

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = {
        "match_id": match_id,
        "category": category.strip().lower(),
        "home_team": home_team.strip(),
        "away_team": away_team.strip(),
        "home_score": home_score,
        "away_score": away_score,
        "status": status,
        "source_name": source_name,
        "source_url": source_url,
    }

    matches.append(entry)
    mdata["matches"] = matches
    mdata["matches_count"] = len(matches)
    mdata["updated_at"] = now_iso

    with open(matches_path, "w", encoding="utf-8") as f:
        json.dump(mdata, f, ensure_ascii=False, indent=2)

    sync_project(proj_dir)
    return entry


def main() -> None:
    parser = argparse.ArgumentParser(description="Add a match and sync Sii-Football endpoints.")
    parser.add_argument("--category", required=True, help="Sport category (e.g. football, basketball)")
    parser.add_argument("--home", required=True, help="Home team name")
    parser.add_argument("--away", required=True, help="Away team name")
    parser.add_argument("--home-score", type=int, required=True, help="Home team score")
    parser.add_argument("--away-score", type=int, required=True, help="Away team score")
    parser.add_argument("--id", dest="match_id", default=None, help="Optional unique match_id")
    parser.add_argument("--status", default="finished", help="Match status")
    parser.add_argument("--source-name", default="Sii-Football Manual Entry", help="Source label")
    parser.add_argument("--source-url", default="https://siiberram.github.io/Sii-Football/", help="Source URL")

    args = parser.parse_args()
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    added = add_match(
        proj_dir=base_dir,
        category=args.category,
        home_team=args.home,
        away_team=args.away,
        home_score=args.home_score,
        away_score=args.away_score,
        match_id=args.match_id,
        status=args.status,
        source_name=args.source_name,
        source_url=args.source_url,
    )
    print("Added match:", added["match_id"], f"({added['home_team']} {added['home_score']} - {added['away_score']} {added['away_team']})")


if __name__ == "__main__":
    main()

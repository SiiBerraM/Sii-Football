import json
import os
from datetime import datetime, timezone


def build_teams(api_dir: str) -> dict:
    matches_path = os.path.join(api_dir, "matches.json")
    with open(matches_path, "r", encoding="utf-8") as f:
        mdata = json.load(f)

    teams = {}
    for m in mdata.get("matches", []):
        cat = m.get("category", "general")
        for side, sk, ok in [
            ("home_team", "home_score", "away_score"),
            ("away_team", "away_score", "home_score"),
        ]:
            name = (m.get(side) or "").strip()
            if not name:
                continue
            key = f"{cat}::{name.lower()}"
            if key not in teams:
                teams[key] = {
                    "id": f"tm-{len(teams) + 1}",
                    "name": name,
                    "category": cat,
                    "matches_played": 0,
                    "wins": 0,
                    "draws": 0,
                    "losses": 0,
                    "goals_for": 0,
                    "goals_against": 0,
                }
            t = teams[key]
            hs, as_ = m.get(sk), m.get(ok)
            if isinstance(hs, int) and isinstance(as_, int):
                t["matches_played"] += 1
                t["goals_for"] += hs
                t["goals_against"] += as_
                if hs > as_:
                    t["wins"] += 1
                elif hs == as_:
                    t["draws"] += 1
                else:
                    t["losses"] += 1

    tdata = {
        "project": "Sii-Football",
        "consumer_app": "SiiMatchMind",
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "teams_count": len(teams),
        "teams": list(teams.values()),
    }

    out_path = os.path.join(api_dir, "teams.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(tdata, f, ensure_ascii=False, indent=2)
    return tdata


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    res = build_teams(os.path.join(base_dir, "api"))
    print("Built teams.json -> count:", res["teams_count"])

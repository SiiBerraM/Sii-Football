import json
import os
import re
from datetime import datetime, timezone

from build_teams import build_teams


def sync_project(proj_dir: str) -> None:
    api_dir = os.path.join(proj_dir, "api")
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    tdata = build_teams(api_dir)

    matches_path = os.path.join(api_dir, "matches.json")
    with open(matches_path, "r", encoding="utf-8") as f:
        mdata = json.load(f)
    matches_count = len(mdata.get("matches", []))

    idx_path = os.path.join(api_dir, "index.json")
    with open(idx_path, "r", encoding="utf-8") as f:
        idata = json.load(f)

    idata["updated_at"] = now_iso
    idata["matches_count"] = matches_count
    idata["teams_count"] = tdata["teams_count"]
    idata["siimatchmind_access"] = {
        "app": "SiiMatchMind",
        "unrestricted": True,
        "conditions": "none",
        "scope": "all_data_and_endpoints",
    }

    with open(idx_path, "w", encoding="utf-8") as f:
        json.dump(idata, f, ensure_ascii=False, indent=2)

    sitemap_path = os.path.join(proj_dir, "sitemap.xml")
    if os.path.exists(sitemap_path):
        with open(sitemap_path, "r", encoding="utf-8") as f:
            sm = f.read()
        sm = re.sub(r"<lastmod>[^<]+</lastmod>", f"<lastmod>{today}</lastmod>", sm)
        with open(sitemap_path, "w", encoding="utf-8") as f:
            f.write(sm)

    print(f"Synced -> matches: {matches_count} | teams: {tdata['teams_count']} | date: {today}")


if __name__ == "__main__":
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sync_project(base)

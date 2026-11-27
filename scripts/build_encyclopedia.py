import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "encyclopedia.json"
API_DIR = ROOT / "docs" / "api"
SPORTS_DIR = API_DIR / "sports"


def main() -> None:
    if not SRC.exists():
        raise FileNotFoundError(f"Missing {SRC}")

    data = json.loads(SRC.read_text(encoding="utf-8"))
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    data["updated_at"] = now_iso

    SPORTS_DIR.mkdir(parents=True, exist_ok=True)
    SRC.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (API_DIR / "encyclopedia.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    sports_list = data.get("sports", [])
    sport_endpoints = {}

    for sport in sports_list:
        sid = sport.get("id")
        if not sid:
            continue
        payload = {
            "service": data.get("service", "Sii-Football Multi-Sport Encyclopedia API"),
            "owner": data.get("owner", "Berra"),
            "access": data.get("access", "free_open"),
            "updated_at": now_iso,
            "sport": sport,
            "glossary": data.get("glossary", []),
        }
        out_path = SPORTS_DIR / f"{sid}.json"
        out_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        sport_endpoints[sid] = f"/api/sports/{sid}.json"

    index_path = API_DIR / "index.json"
    index_data = {}
    if index_path.exists():
        try:
            index_data = json.loads(index_path.read_text(encoding="utf-8"))
        except Exception:
            index_data = {}

    index_data.update(
        {
            "service": data.get("service", "Sii-Football Multi-Sport Encyclopedia API"),
            "owner": data.get("owner", "Berra"),
            "access": "free_open",
            "version": data.get("version", "2.0.0"),
            "updated_at": now_iso,
            "sports_count": len(sport_endpoints),
            "sports_ids": list(sport_endpoints.keys()),
            "endpoints": {
                **(index_data.get("endpoints") if isinstance(index_data.get("endpoints"), dict) else {}),
                "encyclopedia": "/api/encyclopedia.json",
                "support": "/api/support.json",
                "sports": sport_endpoints,
            },
        }
    )

    index_path.write_text(
        json.dumps(index_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Built encyclopedia + {len(sport_endpoints)} sport endpoints at {now_iso}")


if __name__ == "__main__":
    main()

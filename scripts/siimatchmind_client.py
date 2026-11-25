from urllib.request import urlopen
import json

BASE_API = "https://siiberram.github.io/Sii-Football/api"


def get_json(endpoint: str) -> dict:
    url = f"{BASE_API}/{endpoint.lstrip('/')}"
    with urlopen(url, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_para_football_bundle() -> dict:
    return {
        "index": get_json("index.json"),
        "leagues": get_json("leagues.json"),
        "standings": get_json("standings.json"),
        "news": get_json("news.json"),
        "disclaimer": get_json("disclaimer.json"),
    }


if __name__ == "__main__":
    bundle = fetch_para_football_bundle()
    leagues = bundle["leagues"]
    print(
        f"SiiMatchMind Feed Ready | Competitions: {leagues.get('competitions_count', 0)} | "
        f"Matches: {leagues.get('matches_count', 0)} | Updated: {leagues.get('updated_at')}"
    )

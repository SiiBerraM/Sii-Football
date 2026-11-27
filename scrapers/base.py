import time
import requests

HEADERS = {"User-Agent": "Sii-FootballBot/1.0 (+noreply@users.noreply.github.com)"}


class SourceError(Exception):
    pass


def fetch(url, retries=3, timeout=30):
    last = None
    for i in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            r.raise_for_status()
            return r.content
        except Exception as e:
            last = e
            time.sleep(2 * (i + 1))
    raise SourceError(f"fetch failed: {last}")

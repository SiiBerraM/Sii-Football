import hashlib, re
from datetime import timezone
from zoneinfo import ZoneInfo
from dateutil import parser as dparser

STATUS_MAP = {"ft": "finished", "finished": "finished", "full time": "finished", "final": "finished",
              "live": "live", "in play": "live", "scheduled": "scheduled", "ns": "scheduled",
              "postponed": "postponed", "ppd": "postponed", "cancelled": "cancelled",
              "canceled": "cancelled", "abandoned": "cancelled"}
SCORE_RE = re.compile(r"(\d+)\s*[-:\u2013]\s*(\d+)")


def make_id(sport, competition, date_utc, home, away):
    key = "|".join([sport, competition, (date_utc or "")[:10], home.lower().strip(), away.lower().strip()])
    return hashlib.sha1(key.encode()).hexdigest()[:16]


def team_code(name):
    letters = re.sub(r"[^A-Za-z]", "", name)
    return letters[:3].upper()


def get(row, key, cols):
    if isinstance(row, dict):
        return (row.get(key) or "").strip()
    idx = cols.get(key)
    if idx is None or idx >= len(row):
        return ""
    return (row[idx] or "").strip()


def to_utc(date_s, time_s, tz, dayfirst):
    dt = dparser.parse(f"{date_s} {time_s}".strip(), dayfirst=dayfirst)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo(tz))
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def rows_to_matches(rows, src, fetched_at):
    cols = src.get("columns", {})
    out, skipped = [], 0
    for row in rows:
        try:
            home, away = get(row, "home", cols), get(row, "away", cols)
            if not home or not away:
                raise ValueError("missing team")
            date_utc = to_utc(get(row, "date", cols), get(row, "time", cols),
                              src.get("timezone", "UTC"), src.get("dayfirst", True))
            score_s = get(row, "score", cols)
            sm = SCORE_RE.search(score_s)
            hs, as_ = (int(sm.group(1)), int(sm.group(2))) if sm else (None, None)
            raw_status = get(row, "status", cols).lower()
            status = STATUS_MAP.get(raw_status) or ("finished" if sm else "scheduled")
            out.append({
                "match_id": make_id(src["sport"], src["competition"], date_utc, home, away),
                "sport": src["sport"], "competition": src["competition"],
                "date_utc": date_utc, "status": status,
                "home_team": {"name": home, "code": team_code(home), "score": hs},
                "away_team": {"name": away, "code": team_code(away), "score": as_},
                "venue": get(row, "venue", cols), "source_url": src["url"],
                "source_id": src["id"], "is_stale": False, "source_updated_at": fetched_at,
            })
        except Exception:
            skipped += 1
    return out, skipped

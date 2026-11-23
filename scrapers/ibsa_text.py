"""Parser for IBSA-style results text (day headers + 'Stage: Team N (scorers) Team N (scorers)')."""
import re

DAY_RE = re.compile(r"^(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)\s*$", re.I)
START_RE = re.compile(r"^(?:\d{1,2}[:.]\d{2}\s*[-\u2013]?\s*)?(?:Group\s+\w+|Quarter-?Final\s*\d*|Semi-?Final\s*\d*|Final|3rd place|\d+(?:st|nd|rd|th)\s+place|\w+\s+place)", re.I)
MATCH_RE = re.compile(
    r"^(?:(?P<time>\d{1,2}[:.]\d{2})\s*[-\u2013]?\s*)?(?P<stage>[^:]{2,60}?):\s*"
    r"(?P<home>[A-Za-z\u00C0-\u017F.' ]+?)\s+(?P<hs>\d{1,2})\s+"
    r"(?P<away>[A-Za-z\u00C0-\u017F.' ]+?)\s+(?P<as>\d{1,2})\s*$")


def _clean(s):
    s = re.sub(r"\([^)]*\)", " ", s)          # drop scorers / penalty notes
    return re.sub(r"\s+", " ", s).strip()


def parse_text(text, src):
    year = str(src.get("year", ""))
    # 1) join wrapped lines
    logical, cur = [], ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if DAY_RE.match(line) or START_RE.match(line) or line.lower().startswith(("group ", "final standings", "individual", "top ")):
            if cur:
                logical.append(cur)
            cur = line
        else:
            cur = (cur + " " + line) if cur else line
    if cur:
        logical.append(cur)
    # 2) walk lines
    rows, date_s = [], ""
    for line in logical:
        d = DAY_RE.match(line)
        if d:
            date_s = f"{d.group(1)} {d.group(2)} {year}".strip()
            continue
        if not date_s:
            continue
        m = MATCH_RE.match(_clean_keep_colon(line))
        if not m:
            continue
        rows.append({"date": date_s, "time": (m.group("time") or "00:00").replace(".", ":"),
                     "home": m.group("home").strip(), "away": m.group("away").strip(),
                     "score": f"{m.group('hs')}-{m.group('as')}", "status": "finished",
                     "venue": src.get("venue", "")})
    return rows


def _clean_keep_colon(line):
    return _clean(line)

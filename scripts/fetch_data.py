import io
import json
import os
import re
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser


USER_AGENT = "SiiFootballBot/1.0 (+https://siiberram.github.io/Sii-Football/)"
IGNORED_PDF_KEYWORDS = ("guideline", "policy", "anti-doping", "doping", "statute", "constitution", "form", "application")


class LinkAndTextExtractor(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self.chunks = []
        self.pdf_links = []
        self.skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "svg", "nav", "footer"):
            self.skip = True
        elif tag == "a":
            href = dict(attrs).get("href", "").strip()
            if href:
                full_url = urljoin(self.base_url, href)
                low = full_url.lower()
                if ".pdf" in low and full_url not in self.pdf_links:
                    if not any(k in low for k in IGNORED_PDF_KEYWORDS):
                        self.pdf_links.append(full_url)

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "svg", "nav", "footer"):
            self.skip = False

    def handle_data(self, data):
        if not self.skip:
            cleaned = re.sub(r"\s+", " ", data).strip()
            if cleaned:
                self.chunks.append(cleaned)


def is_allowed_by_robots(url: str) -> bool:
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(USER_AGENT, url)
    except Exception:
        return True


def fetch_bytes(url: str, timeout: int = 25) -> bytes:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def parse_html(url: str):
    raw = fetch_bytes(url).decode("utf-8", errors="ignore")
    parser = LinkAndTextExtractor(url)
    parser.feed(raw)
    return " ".join(parser.chunks), parser.pdf_links[:8]


def parse_pdf(path_or_url: str) -> str:
    if path_or_url.startswith(("http://", "https://")):
        raw_bytes = fetch_bytes(path_or_url)
    else:
        with open(path_or_url, "rb") as f:
            raw_bytes = f.read()

    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(raw_bytes))
        pages_text = [(page.extract_text() or "").strip() for page in reader.pages]
        joined = "\n".join(t for t in pages_text if t)
        cleaned = re.sub(r"\s+", " ", joined).strip()
        printable_ratio = sum(ch.isprintable() for ch in cleaned) / max(len(cleaned), 1)
        return cleaned if printable_ratio > 0.92 else ""
    except Exception:
        return ""


def main():
    os.makedirs("api", exist_ok=True)
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    sources = []
    if os.path.exists("api/sources.json"):
        with open("api/sources.json", "r", encoding="utf-8") as f:
            sources = json.load(f).get("sources", [])

    items = []
    idx_counter = 0

    for src in sources:
        name = src.get("name", "Para-Football Source")
        url = src.get("url", "").strip()
        src_type = src.get("type", "html").lower()
        category = src.get("category", "para-football")
        if not url:
            continue

        if url.startswith(("http://", "https://")) and not is_allowed_by_robots(url):
            idx_counter += 1
            items.append({
                "id": idx_counter,
                "source_name": name,
                "source_url": url,
                "source_type": src_type,
                "category": category,
                "status": "blocked_by_robots",
                "fetched_at": now_iso,
            })
            continue

        try:
            discovered_pdfs = []
            if src_type == "pdf":
                content = parse_pdf(url)
            else:
                content, discovered_pdfs = parse_html(url)

            idx_counter += 1
            items.append({
                "id": idx_counter,
                "source_name": name,
                "source_url": url,
                "source_type": src_type,
                "category": category,
                "status": "ok" if content else "empty_or_unreadable",
                "discovered_pdfs": discovered_pdfs,
                "excerpt": content[:1200],
                "full_text": content[:80000],
                "char_length": len(content),
                "fetched_at": now_iso,
            })

            for pdf_url in discovered_pdfs:
                if not is_allowed_by_robots(pdf_url):
                    continue
                try:
                    pdf_text = parse_pdf(pdf_url)
                    if pdf_text:
                        idx_counter += 1
                        items.append({
                            "id": idx_counter,
                            "source_name": f"{name} (PDF)",
                            "source_url": pdf_url,
                            "source_type": "pdf",
                            "category": category,
                            "status": "ok",
                            "excerpt": pdf_text[:1200],
                            "full_text": pdf_text[:80000],
                            "char_length": len(pdf_text),
                            "fetched_at": now_iso,
                        })
                except Exception:
                    pass
                time.sleep(0.5)
        except Exception as exc:
            idx_counter += 1
            items.append({
                "id": idx_counter,
                "source_name": name,
                "source_url": url,
                "source_type": src_type,
                "category": category,
                "status": "error",
                "error": str(exc),
                "fetched_at": now_iso,
            })

        time.sleep(1.0)

    news_payload = {
        "project": "Sii-Football",
        "consumer_app": "SiiMatchMind",
        "license_note": "Aggregated from public para-football HTML and PDF sources with attribution.",
        "updated_at": now_iso,
        "count": len(items),
        "items": items,
    }

    with open("api/news.json", "w", encoding="utf-8") as f:
        json.dump(news_payload, f, ensure_ascii=False, indent=2)

    print(f"Done. Processed {len(items)} items -> api/news.json")


if __name__ == "__main__":
    main()

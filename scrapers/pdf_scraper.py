import io, re
import pdfplumber
from . import ibsa_text


def _tables(content):
    rows = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                rows.extend([[(c or "").replace("\n", " ") for c in r] for r in table if r])
    return rows


def _text(content):
    try:
        import fitz  # PyMuPDF (optional)
        with fitz.open(stream=content, filetype="pdf") as doc:
            return "\n".join(p.get_text() for p in doc)
    except Exception:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            return "\n".join((p.extract_text() or "") for p in pdf.pages)


def parse(content: bytes, src: dict):
    mode = src.get("parser")
    if mode == "ibsa_text":
        return ibsa_text.parse_text(_text(content), src)
    rows = _tables(content)
    if rows:
        return rows
    rx = src.get("line_regex")
    if not rx:
        return []
    pat = re.compile(rx)
    out = []
    for line in _text(content).splitlines():
        m = pat.search(line.strip())
        if m:
            out.append(m.groupdict())
    return out

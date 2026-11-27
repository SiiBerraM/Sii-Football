import io, re
import pdfplumber


def _tables(content):
    rows = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                rows.extend([[(c or "").replace("\n", " ") for c in r] for r in table if r])
    return rows


def _text_lines(content):
    text = ""
    try:
        import fitz  # PyMuPDF
        with fitz.open(stream=content, filetype="pdf") as doc:
            text = "\n".join(p.get_text() for p in doc)
    except Exception:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            text = "\n".join((p.extract_text() or "") for p in pdf.pages)
    return text.splitlines()


def parse(content: bytes, src: dict):
    rows = _tables(content)
    if rows:
        return rows
    rx = src.get("line_regex")
    if not rx:
        return []
    pat = re.compile(rx)
    out = []
    for line in _text_lines(content):
        m = pat.search(line.strip())
        if m:
            out.append(m.groupdict())
    return out

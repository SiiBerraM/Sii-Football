from bs4 import BeautifulSoup


def parse(content: bytes, src: dict):
    soup = BeautifulSoup(content, "html.parser")
    cell_sel = src.get("cell_selector", "td")
    rows = []
    for tr in soup.select(src.get("row_selector", "table tr")):
        cells = [c.get_text(" ", strip=True) for c in tr.select(cell_sel)]
        if cells:
            rows.append(cells)
    return rows

from . import html_scraper, pdf_scraper

PARSERS = {"html": html_scraper.parse, "pdf": pdf_scraper.parse}
# Add new source types (API/JSON/RSS...) here without touching anything else.

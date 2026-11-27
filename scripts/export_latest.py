import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.db import init_db
from app.exporter import export_latest

init_db()
print(export_latest())

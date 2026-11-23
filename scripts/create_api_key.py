import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.db import init_db
from app.security import create_key

init_db()
owner = sys.argv[1] if len(sys.argv) > 1 else "developer"
print(create_key(owner))

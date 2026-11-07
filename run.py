"""
VidCode Server Launcher (Root).
Run from c:\\Vidcode with: python run.py
"""
import sys
from pathlib import Path

# Add backend directory to sys.path so 'app' is discoverable from root
backend_dir = Path(__file__).resolve().parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import uvicorn
from app.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    print("\n" + "=" * 60)
    print(f" 🚀 Starting {settings.app_name} on http://127.0.0.1:8000")
    print(f" 📖 Interactive Swagger Docs: http://127.0.0.1:8000/docs")
    print("=" * 60 + "\n")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

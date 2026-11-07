"""
VidCode Server Launcher (Root).
Automatically switches to the project's virtual environment if not already active.
"""
import sys
import os
from pathlib import Path

root_dir = Path(__file__).resolve().parent
backend_dir = root_dir / "backend"
venv_python = backend_dir / ".venv" / "Scripts" / "python.exe"

# If user is running global python, seamlessly switch to the venv python
if venv_python.exists() and sys.executable.lower() != str(venv_python.resolve()).lower():
    print(f"🔄 Activating VidCode virtual environment: {venv_python}")
    os.execv(str(venv_python), [str(venv_python), str(Path(__file__).resolve())] + sys.argv[1:])

if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import uvicorn
from app.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    print("\n" + "=" * 65)
    print(f" 🚀 VidCode Backend Live on http://127.0.0.1:8000")
    print(f" 📖 Interactive Swagger Docs: http://127.0.0.1:8000/docs")
    print("=" * 65 + "\n")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

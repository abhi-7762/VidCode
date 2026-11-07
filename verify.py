"""
VidCode Verification Suite (Root).
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
    os.execv(str(venv_python), [str(venv_python), str(Path(__file__).resolve())] + sys.argv[1:])

if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import asyncio
from backend.verify import main

if __name__ == "__main__":
    asyncio.run(main())

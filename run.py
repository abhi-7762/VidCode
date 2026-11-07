"""
VidCode Master Launcher (Root)
==============================
Single entrypoint for both the Video Generator and the API Server:
- python run.py          -> Interactive choice (CLI Video Generator or API Server)
- python run.py --cli    -> Directly launch 9:16 Commercial Generator CLI
- python run.py --server -> Directly launch FastAPI Backend Server
- python run.py --demo   -> Directly run Matched Food Commercial demo
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
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

def start_server():
    import uvicorn
    print("\n" + "=" * 65)
    print(" 🚀 VidCode Backend Live on http://127.0.0.1:8000")
    print(" 📖 Interactive Swagger Docs: http://127.0.0.1:8000/docs")
    print("=" * 65 + "\n")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

def start_cli():
    import vidcode_cli
    vidcode_cli.main()

def start_demo():
    import make_matched_commercial
    make_matched_commercial.compile_commercial()

if __name__ == "__main__":
    args = [a.lower() for a in sys.argv[1:]]

    if "--server" in args or "-s" in args:
        start_server()
    elif "--cli" in args or "-c" in args:
        start_cli()
    elif "--demo" in args or "-d" in args:
        start_demo()
    else:
        # User ran 'python run.py' without arguments:
        # Show clean menu or launch CLI
        print("\n" + "=" * 65)
        print("  🎬  VIDCODE AI STUDIO — MASTER LAUNCHER")
        print("=" * 65)
        print("  [1] 🎬 Launch 9:16 Viral Commercial Generator (CLI)")
        print("  [2] 🚀 Start FastAPI Backend Server (http://127.0.0.1:8000)")
        print("  [3] ⚡ Re-render Matched Demo Commercial (Ambika Rasoi)")
        print("  [4] ❌ Exit")
        print("=" * 65)
        try:
            choice = input("  Apna option choose karein [Default: 1]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            sys.exit(0)

        if choice in ["", "1"]:
            start_cli()
        elif choice == "2":
            start_server()
        elif choice == "3":
            start_demo()
        else:
            print("Exiting.")
            sys.exit(0)

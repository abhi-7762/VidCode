"""
VidCode Server Launcher.
Run with: python run.py
"""
import uvicorn
from app.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    print(f"🚀 Starting {settings.app_name} on http://127.0.0.1:8000")
    print(f"📖 Interactive Swagger Docs: http://127.0.0.1:8000/docs")
    print(f"📄 Redoc API Documentation: http://127.0.0.1:8000/redoc")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)


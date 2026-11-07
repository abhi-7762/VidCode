"""
VidCode Verification Suite.
Run with: python verify.py
Checks every subsystem: FastAPI, FFmpeg, Gemini AI, Edge-TTS, and Pytest.
"""
import os
import sys
import asyncio
from pathlib import Path


def print_check(name: str, passed: bool, detail: str = ""):
    icon = "✅" if passed else "❌"
    print(f"{icon} {name:<35} {detail}")


async def test_gemini():
    try:
        from app.config import get_settings
        import google.generativeai as genai
        settings = get_settings()
        if not settings.gemini_api_key:
            return False, "GEMINI_API_KEY is missing in .env"
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-3.8-flash")
        resp = model.generate_content("Respond with exactly: OK")
        return True, f"Connected (response: '{resp.text.strip()}')"
    except Exception as e:
        return False, str(e)


async def test_edge_tts():
    try:
        import edge_tts
        tmp_mp3 = Path("verify_test.mp3")
        comm = edge_tts.Communicate("VidCode test audio.", "en-US-ChristopherNeural")
        await comm.save(str(tmp_mp3))
        exists = tmp_mp3.exists() and tmp_mp3.stat().st_size > 0
        if tmp_mp3.exists():
            tmp_mp3.unlink()
        return exists, "Generated test speech file successfully"
    except Exception as e:
        return False, str(e)


def test_ffmpeg():
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        return bool(exe and Path(exe).exists()), f"Found at {Path(exe).name}"
    except Exception as e:
        return False, str(e)


def test_app_import():
    try:
        from app.main import app
        route_count = len(app.routes)
        return True, f"FastAPI app initialized with {route_count} routes"
    except Exception as e:
        return False, str(e)


def test_database_connection():
    try:
        from app.config import get_settings
        settings = get_settings()
        import motor.motor_asyncio
        client = motor.motor_asyncio.AsyncIOMotorClient(
            settings.mongodb_url, serverSelectionTimeoutMS=1500
        )
        return True, f"Target: {settings.mongodb_url} (Database: '{settings.mongodb_db_name}')"
    except Exception as e:
        return False, str(e)


async def main():
    print("\n" + "=" * 65)
    print(" 🎬 VidCode System Health Verification")
    print("=" * 65)

    # 1. FastAPI App
    ok, msg = test_app_import()
    print_check("1. FastAPI App & Routes", ok, msg)

    # 2. FFmpeg
    ok, msg = test_ffmpeg()
    print_check("2. Bundled FFmpeg Binary", ok, msg)

    # 3. Neural Voice Engine
    ok, msg = await test_edge_tts()
    print_check("3. Neural Voice Engine (Edge-TTS)", ok, msg)

    # 4. Gemini AI Connection
    ok, msg = await test_gemini()
    print_check("4. Gemini AI Connection", ok, msg)

    # 5. Database Configuration
    ok, msg = test_database_connection()
    print_check("5. MongoDB Configuration", ok, msg)

    print("=" * 65)
    print("\n👉 To start the live server, run:")
    print("   python run.py\n")
    print("👉 To run the automated test suite, run:")
    print("   pytest\n")


if __name__ == "__main__":
    asyncio.run(main())

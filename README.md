# VidCode 🎬

> AI-powered video generation platform — from a text prompt to a fully rendered, voiced, subtitled video.

## Tech Stack
- **Backend**: FastAPI + Uvicorn
- **Database**: MongoDB (Motor async driver)
- **Cache / Queue**: Redis + Celery
- **AI**: Google Gemini, RunwayML, ElevenLabs, Whisper
- **Rendering**: FFmpeg

## Project Structure
```
VidCode/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI entry point
│   │   ├── config.py        # Settings
│   │   ├── database.py      # MongoDB connection
│   │   ├── celery_app.py    # Celery setup
│   │   ├── models/          # Pydantic schemas
│   │   ├── routers/         # API routes
│   │   ├── services/        # Business logic
│   │   └── tasks/           # Celery tasks
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
└── README.md
```

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
copy .env.example .env      # then fill in your values
```

## Running the Application

### 1. Interactive 9:16 Video Generator (Recommended)
Generate high-converting 1080x1920 Instagram Reels & YouTube Shorts commercials with real matched HD footage, Edge-TTS studio voiceover, kinetic subtitles, and brand banners:

```bash
# Easy launcher (menu selection):
python run.py

# Or directly:
python run.py --cli
# or:
backend\.venv\Scripts\python.exe vidcode_cli.py
```

### 2. FastAPI Backend & Swagger API Docs
```bash
# Start API Server:
python run.py --server

# Or directly with Uvicorn:
uvicorn app.main:app --reload
```
Once started, open your browser to **`http://127.0.0.1:8000/docs`** for the interactive Swagger dashboard.

### 3. Matched Food Commercial Demo (Ambika Rasoi)
```bash
python run.py --demo
# or:
backend\.venv\Scripts\python.exe make_matched_commercial.py
```

## Running Tests

```bash
pytest
```

## Build Phases Status
| Phase | Status | Description |
|-------|--------|-------------|
| 1 — Backend Foundation | ✅ Complete | FastAPI, MongoDB, Redis, Celery, File storage |
| 2 — Gemini Intelligence | ✅ Complete | Script generation, NLU, story planning |
| 3 — Storyboard Generation | ✅ Complete | Scene planning, camera specs, character consistency, prompts |
| 4 — AI Video Generation | ✅ Complete | RunwayML, Luma, Mock provider clip generation, job tracking |
| 5 — Video Production | ✅ Complete | Voiceover (Edge-TTS / ElevenLabs), subtitles, FFmpeg rendering |
| 6 — Quality & Optimization | ✅ Complete | Validation, visual audit, scene splicing, cost & version control |

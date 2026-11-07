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

## Running

```bash
# API server
uvicorn app.main:app --reload

# Celery worker (requires Redis)
celery -A app.celery_app worker --loglevel=info

# Tests
pytest
```

## Build Phases
| Phase | Status | Description |
|-------|--------|-------------|
| 1 — Backend Foundation | ✅ Done | FastAPI, MongoDB, Redis, Celery, File storage |
| 2 — Gemini Intelligence | 🔜 Next | Script generation, NLU, story planning |
| 3 — Storyboard Generation | ⏳ | Scene planning, camera specs, prompt generation |
| 4 — AI Video Generation | ⏳ | RunwayML/Pika clip generation, job tracking |
| 5 — Video Production | ⏳ | Voice, audio, subtitles, FFmpeg rendering |
| 6 — Quality & Optimization | ⏳ | Validation, regeneration, cost tracking |

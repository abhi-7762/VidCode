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

```bash
cd backend
.venv\Scripts\activate      # Windows (.venv/bin/activate on Mac/Linux)

# Start API Server with live reload
python run.py

# Or directly with Uvicorn
uvicorn app.main:app --reload
```
Once started, open your browser to **`http://127.0.0.1:8000/docs`** for the interactive Swagger dashboard.

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

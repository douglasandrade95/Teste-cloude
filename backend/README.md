# AutoVideoEditor - Backend

Python FastAPI backend for AI-powered video editing.

## Features (MVP - Phase 1)

- Video upload and validation
- Emotional analysis with Claude API
- Automatic silence removal
- Basic color grading
- Platform-specific scaling (Reels/TikTok/Shorts)
- Background task processing
- RESTful API

## Setup

### Prerequisites
- Python 3.10+
- FFmpeg installed (`apt-get install ffmpeg`)
- API keys in `.env`

### Installation

```bash
pip install -r requirements.txt
```

### Running Locally

```bash
# Set environment
export FASTAPI_ENV=development

# Run server
uvicorn app.main:app --reload --port 8000
```

### Running with Docker

```bash
docker-compose up backend
```

## API Endpoints

### Upload Video
```
POST /api/v1/upload
Content-Type: multipart/form-data

- file: mp4/mov/avi (required)
- vibe: emotional style (required)
- description: optional
```

Response: `project_id`, metadata, emotional analysis

### Get Project
```
GET /api/v1/project/{project_id}
```

### Start Editing
```
POST /api/v1/edit/{project_id}
```

### Check Editing Status
```
GET /api/v1/edit/{project_id}/status
```

### Download Edited Video
```
GET /api/v1/download/{project_id}
```

## Project Structure

```
app/
├── api/
│   └── routes.py          # API endpoints
├── services/
│   ├── ai_analyzer.py     # Claude AI integration
│   └── video_processor.py # FFmpeg operations
├── models/
│   ├── database.py        # SQLAlchemy models
│   └── schemas.py         # Pydantic schemas
├── config.py              # Settings
└── main.py                # FastAPI app
```

## Key Technologies

- **FastAPI** - Modern async Python web framework
- **Claude API** - Creative direction and analysis
- **FFmpeg** - Video processing
- **librosa** - Audio analysis
- **MoviePy** - Video editing
- **SQLAlchemy** - Database ORM

## Configuration

All config via `.env` file (see `.env.example`)

Key variables:
- `ANTHROPIC_API_KEY` - Claude API key
- `DATABASE_URL` - PostgreSQL connection
- `FASTAPI_ENV` - development/production
- `MAX_FILE_SIZE` - Upload limit

## Phase 2 Additions (Upcoming)

- Celery task queue for async processing
- Motion graphics generation
- Intelligent transition effects
- Sound design and music integration
- Retention analysis and hook detection

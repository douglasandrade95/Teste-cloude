# 🚀 AutoVideoEditor - Complete Setup Guide

## Quick Start (Docker - Recommended)

### 1. Prerequisites
- Docker & Docker Compose installed
- API Keys ready (see below)

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

**Required API Keys:**
- `ANTHROPIC_API_KEY` - Get from [Claude API](https://console.anthropic.com)
- `OPENAI_API_KEY` - For Whisper (subtitles) from [OpenAI](https://platform.openai.com)
- `AWS_ACCESS_KEY_ID` & `AWS_SECRET_ACCESS_KEY` - For S3 storage (optional)

### 3. Start Services

```bash
# Start everything
docker-compose up

# Or specific service
docker-compose up backend
docker-compose up frontend
```

**Services:**
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- Database: `localhost:5432`

### 4. Verify Installation

```bash
# Check backend is running
curl http://localhost:8000/health

# Frontend should auto-open or visit
open http://localhost:5173
```

---

## Manual Setup (Local Development)

### Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install FFmpeg
# macOS: brew install ffmpeg
# Ubuntu: sudo apt-get install ffmpeg
# Windows: choco install ffmpeg

# Run server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

---

## Project Structure

```
auto-video-editor/
├── backend/              # Python FastAPI
│   ├── app/
│   │   ├── api/         # API routes
│   │   ├── services/    # AI & processing logic
│   │   ├── models/      # Database models
│   │   └── config.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/            # React + TypeScript
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   └── main.tsx
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml
├── .env.example
├── CLAUDE.md            # Architecture & plans
├── SETUP.md             # This file
└── README.md
```

---

## Database Setup

### Using Docker (Automatic)

Database initializes automatically with docker-compose.

### Manual Setup

```bash
# Connect to PostgreSQL
psql postgresql://user:password@localhost:5432/auto_video_editor

# Run migrations (when alembic is configured)
alembic upgrade head
```

---

## API Usage Examples

### Upload & Analyze Video

```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@video.mp4" \
  -F "vibe=luxury" \
  -F "description=My video"
```

Response:
```json
{
  "project_id": "uuid",
  "message": "Video uploaded successfully",
  "emotional_analysis": {
    "primary_emotion": "luxury",
    "intensity": 0.85,
    "recommended_pacing": "slow",
    ...
  }
}
```

### Start Editing

```bash
curl -X POST http://localhost:8000/api/v1/edit/{project_id}
```

### Check Progress

```bash
curl http://localhost:8000/api/v1/edit/{project_id}/status
```

### Download

```bash
curl -O http://localhost:8000/api/v1/download/{project_id}
```

---

## Development Workflow

### Code Quality

```bash
# Backend linting
cd backend
black .           # Format code
flake8 .          # Lint
mypy .            # Type check

# Frontend linting
cd ../frontend
npm run lint      # ESLint
npm run type-check # TypeScript check
```

### Testing

```bash
# Backend
cd backend
pytest

# Frontend
cd ../frontend
npm test
```

---

## Troubleshooting

### Backend Won't Start

**Error: "No module named 'app'"**
```bash
cd backend
python -m pip install -e .
```

**FFmpeg not found**
```bash
# Check FFmpeg
ffmpeg -version

# Install:
# macOS: brew install ffmpeg
# Ubuntu: sudo apt-get install ffmpeg
# Windows: https://ffmpeg.org/download.html
```

### Frontend Won't Load

**Port 5173 already in use**
```bash
# Kill process or use different port
npm run dev -- --port 5174
```

**API connection error**
Check `.env` has correct `VITE_API_URL`

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose ps

# Check connection string in .env
# Format: postgresql://user:password@host:port/database
```

### API Key Errors

Ensure `.env` has all required keys:
- `ANTHROPIC_API_KEY` ✅
- `OPENAI_API_KEY` ✅
- AWS keys if using S3

---

## Performance Tips

1. **Use Docker** - Eliminates dependency conflicts
2. **Enable GPU** - For video processing (optional)
3. **Increase timeouts** - For large videos
4. **Set worker concurrency** - `WORKER_CONCURRENCY=2`

---

## Next Steps

1. ✅ Complete MVP Phase 1 (current)
2. 📋 Phase 2: Motion graphics & effects
3. 📊 Phase 3: Analytics & strategy

See `CLAUDE.md` for full roadmap.

---

## Support

For issues:
1. Check `docker-compose logs {service}`
2. Review `.env` configuration
3. Check API documentation at `http://localhost:8000/docs`

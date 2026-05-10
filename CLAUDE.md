# AutoVideoEditor - AI-Powered Video Editing for Social Media

## 🎬 Project Vision
An intelligent creative director that transforms raw videos into cinematic, emotionally engaging content optimized for Instagram Reels, TikTok, and YouTube Shorts.

## 🏗️ Architecture Overview

### Tech Stack
- **Frontend:** React 18 + TypeScript + TailwindCSS
- **Backend:** FastAPI (Python) + Node.js microservices
- **Video Processing:** FFmpeg, MoviePy, librosa
- **AI/ML:** Claude API, Google Vertex AI, Replicate
- **Storage:** AWS S3 (configurable)
- **Database:** PostgreSQL
- **Deployment:** Docker + Docker Compose

### Project Structure
```
auto-video-editor/
├── frontend/                 # React app
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── styles/
│   └── package.json
├── backend/                  # Python FastAPI
│   ├── app/
│   │   ├── api/
│   │   ├── services/
│   │   ├── models/
│   │   └── config.py
│   ├── requirements.txt
│   └── main.py
├── workers/                  # Processing services
│   ├── video_processor/
│   ├── ai_analyzer/
│   └── music_suggester/
├── docker-compose.yml
├── .env.example
└── CLAUDE.md
```

## 📋 MVP Roadmap (Phase 1)

### Features
1. **Upload System** - Videos, audio, reference images, creative brief
2. **Emotional Analysis** - AI analyzes vibe and intent using Claude
3. **Auto Editing**
   - Remove silences and pauses
   - Auto subtitles (Whisper API)
   - Basic color grading suggestions
4. **Export** - Optimized for Reels/TikTok/Shorts dimensions

### Not Included Yet (Phase 2+)
- Motion graphics and animated overlays
- Complex transition effects
- Full social media strategy analysis
- Automatic hook detection

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- FFmpeg installed
- API Keys: OpenAI, Google Cloud (optional for MVP)

### Setup
```bash
# 1. Copy env template
cp .env.example .env

# 2. Install backend dependencies
cd backend && pip install -r requirements.txt

# 3. Install frontend dependencies
cd ../frontend && npm install

# 4. Start services
docker-compose up
```

## 🔑 Key Technologies & Why

| Component | Tech | Reason |
|-----------|------|--------|
| Video processing | FFmpeg + MoviePy | Industry standard, powerful |
| Speech-to-text | OpenAI Whisper | Accurate, multilingual |
| Emotional analysis | Claude API | Best for nuanced creative intent |
| Audio processing | librosa | Professional audio analysis |
| Frontend | React + TypeScript | Safe, scalable, fast |
| Backend | FastAPI | Async, modern, fast |
| Video AI models | Replicate | Easy inference, many models |

## 🎯 Development Guidelines

### Branching
- All work on `claude/auto-video-editor-afHDl`
- Commit message format: `[PHASE1] Feature description`

### Code Quality
- Type hints everywhere (Python & TypeScript)
- Async/await for I/O operations
- Environment variables for all configs
- Comprehensive error handling

### Testing Strategy
- Unit tests for AI analysis logic
- Integration tests for video processing
- E2E tests for upload → export workflow

## 📊 Phase 2-3 Roadmap

**Phase 2:** Advanced Creativity
- Motion graphics generation
- Intelligent transitions
- Animated text overlays
- Dynamic visual effects

**Phase 3:** Social Media Strategy
- Retention analysis
- Hook suggestions
- Auto-thumbnail generation
- Platform-specific optimization

## 🔐 Security Notes

- All file uploads validated (size, format)
- Async processing with job queues
- API keys in environment only
- CORS properly configured
- Rate limiting on API endpoints

## 📞 Support
For questions about architecture or implementation, check the specific service READMEs.

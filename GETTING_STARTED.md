# 🎬 Getting Started with AutoVideoEditor

## What is This?

**AutoVideoEditor** is an AI-powered video editing platform that transforms raw videos into cinematic, emotionally engaging content for Instagram Reels, TikTok, and YouTube Shorts.

Think of it as having a professional creative director, editor, and motion designer working on your video automatically.

---

## 🚀 Start in 3 Minutes

### Option A: Docker (Easiest)

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Edit with your API keys (see API Keys section below)
# nano .env

# 3. Start everything
docker-compose up

# 4. Open in browser
# Frontend: http://localhost:5173
# Backend Docs: http://localhost:8000/docs
```

### Option B: Manual Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## 🔑 API Keys Required

You need these to make the AI work:

### 1. Claude API Key (Required)
- Go to: https://console.anthropic.com
- Create account/login
- Create API key
- Add to `.env`: `ANTHROPIC_API_KEY=sk-...`

### 2. OpenAI API Key (For subtitles)
- Go to: https://platform.openai.com
- Create API key
- Add to `.env`: `OPENAI_API_KEY=sk-...`

### 3. AWS Keys (Optional, for cloud storage)
- Skip for now if you just want to test locally

---

## 📚 How It Works

### Flow:
```
1. Upload Video
   ↓
2. Choose Emotional Vibe (luxury, energy, drama, etc)
   ↓
3. AI Analyzes with Claude
   ↓
4. Automatic Editing Starts
   - Remove silences
   - Color grading
   - Platform optimization
   ↓
5. Download Edited Video
```

### What the AI Does:

**Emotional Analysis**
- Detects emotion and intensity
- Recommends pacing (fast/slow/dynamic)
- Suggests color palette
- Recommends music mood

**Video Editing**
- Removes silent moments automatically
- Adds professional color grading
- Optimizes for TikTok/Reels/Shorts dimensions
- Sync cuts to emotion

---

## 🎯 MVP Features (Phase 1)

✅ Video upload  
✅ Emotional vibe selection  
✅ AI emotional analysis (Claude)  
✅ Silence removal  
✅ Color grading  
✅ Platform scaling  
✅ Download edited video  

---

## 📋 Phase 2 & 3 (Coming Soon)

**Phase 2:**
- Motion graphics & animations
- Intelligent transitions
- Animated text overlays
- Dynamic effects

**Phase 3:**
- Retention analysis
- Hook detection
- Thumbnail generation
- Social media strategy

---

## 🧪 Quick Test

### Test File
Use any MP4 video under 5GB. Or create a quick test:

```bash
# Simple test video (30 seconds)
ffmpeg -f lavfi -i color=c=blue:s=1080x1920:d=30 \
        -f lavfi -i sine=f=1000:d=30 \
        -pix_fmt yuv420p test_video.mp4
```

### Test Steps:
1. Open http://localhost:5173
2. Upload test_video.mp4
3. Select vibe (try "luxury")
4. Click "Analisar Vídeo"
5. Click "Começar Edição"
6. Watch progress bar
7. Download when done

Expected: Video will be shorter (silence removed) with enhanced colors.

---

## 🏗️ Project Structure

```
auto-video-editor/
├── backend/           # Python FastAPI
│   └── app/
│       ├── api/       # API endpoints
│       ├── services/  # AI & processing
│       └── models/    # Database models
├── frontend/          # React + TypeScript
│   └── src/
│       └── pages/Editor.tsx
├── docker-compose.yml
├── CLAUDE.md          # Full architecture
└── SETUP.md           # Detailed setup
```

---

## 🛠️ Common Issues

### "No module named app"
```bash
cd backend && pip install -e .
```

### "FFmpeg not found"
```bash
# macOS
brew install ffmpeg

# Ubuntu
sudo apt-get install ffmpeg
```

### "Port already in use"
```bash
# Kill process or use different port
npm run dev -- --port 5174
```

### "API key error"
Make sure `.env` has `ANTHROPIC_API_KEY` set.

---

## 📖 Full Documentation

- **Architecture**: See `CLAUDE.md`
- **Detailed Setup**: See `SETUP.md`
- **Backend API**: See `backend/README.md`
- **Frontend Code**: See `frontend/README.md`

---

## 🎨 UI Philosophy

Inspired by:
- **Apple** - Simple, elegant design
- **Notion** - Spacious, refined
- **CapCut Premium** - Fast, responsive

The interface should feel premium but easy to use.

---

## 🤖 AI Models Used

- **Claude 3.5 Sonnet** - Creative direction & analysis
- **OpenAI Whisper** - Speech-to-text for subtitles
- **FFmpeg + MoviePy** - Video processing
- **librosa** - Audio analysis

---

## 💡 Next Steps

1. ✅ Setup and run locally
2. 🎬 Test with a video
3. 📖 Read CLAUDE.md for full roadmap
4. 🚀 Build Phase 2 features

---

## 📞 Support

Issues? Check:
1. Docker logs: `docker-compose logs backend`
2. Browser console for frontend errors
3. Backend API docs: `http://localhost:8000/docs`
4. SETUP.md troubleshooting section

---

**Ready to create some magic? 🎭** Let's go!

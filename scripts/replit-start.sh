#!/bin/bash
set -e

echo "🚀 AutoVideoEditor - Replit Setup"
echo "=================================="

# Install FFmpeg
echo "📦 Installing FFmpeg..."
apt-get update -qq
apt-get install -y ffmpeg libsm6 libxext6 > /dev/null 2>&1

# Backend setup
echo "⚙️ Setting up Backend..."
cd backend
pip install -q -r requirements.txt
cd ..

# Frontend setup
echo "📦 Setting up Frontend..."
cd frontend
npm install -q
cd ..

echo "✅ Setup complete!"
echo ""
echo "Starting services..."
echo "🔧 Backend: http://localhost:8000"
echo "🎨 Frontend: http://localhost:5173"
echo ""

# Start backend in background
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start frontend
cd ../frontend
npm run dev -- --host 0.0.0.0 --port 5173

# Cleanup
kill $BACKEND_PID 2>/dev/null || true

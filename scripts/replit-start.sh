#!/bin/bash
# Build the frontend and serve everything from one port.
#
# FastAPI serves frontend/dist at / and the API under /api, so Replit only has
# to expose port 8000 and the browser talks to a single origin.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "AutoVideoEditor"
echo "==============="

# --- Secrets check -------------------------------------------------------
# Both are optional for a local run but required for a hosted one: without
# AVE_MASTER_KEY the credential vault is re-keyed on every restart, and
# without AVE_ADMIN_TOKEN the settings screen refuses non-local requests.
missing=0

if [ -z "${AVE_MASTER_KEY:-}" ]; then
  echo ""
  echo "!! AVE_MASTER_KEY is not set."
  echo "   Without it the vault gets a new key on every restart and any saved"
  echo "   API key becomes unreadable. Add this to Replit Secrets:"
  echo ""
  python -c "from cryptography.fernet import Fernet; print('   AVE_MASTER_KEY =', Fernet.generate_key().decode())" 2>/dev/null \
    || echo "   (generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\")"
  missing=1
fi

if [ -z "${AVE_ADMIN_TOKEN:-}" ]; then
  echo ""
  echo "!! AVE_ADMIN_TOKEN is not set."
  echo "   The Integrações screen only accepts local requests without it, so"
  echo "   you will not be able to save an API key from a browser. Add to"
  echo "   Replit Secrets:"
  echo ""
  python -c "import secrets; print('   AVE_ADMIN_TOKEN =', secrets.token_urlsafe(24))" 2>/dev/null \
    || echo "   (any long random string works)"
  missing=1
fi

if [ "$missing" -eq 1 ]; then
  echo ""
  echo "   Add them under Secrets (the padlock icon), then press Run again."
  echo "   Starting anyway so you can look around."
  echo ""
fi

# --- Dependencies --------------------------------------------------------
echo "Installing backend dependencies..."
pip install -q -r backend/requirements.txt

echo "Installing frontend dependencies..."
npm --prefix frontend ci --silent 2>/dev/null || npm --prefix frontend install --silent

# --- Build ---------------------------------------------------------------
echo "Building the frontend..."
npm --prefix frontend run build

# --- Serve ---------------------------------------------------------------
PORT="${PORT:-8000}"
echo ""
echo "Serving on port $PORT — open the URL Replit shows above."
echo ""

cd backend
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT"

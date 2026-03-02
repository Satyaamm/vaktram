#!/usr/bin/env bash
# ==========================================================================
# Vaktram - One-Command Development Setup
# ==========================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo ""
echo "=========================================="
echo "  Vaktram Development Setup"
echo "=========================================="
echo ""

# --------------------------------------------------------------------------
# Check prerequisites
# --------------------------------------------------------------------------

check_command() {
    if command -v "$1" &> /dev/null; then
        log_ok "$1 found: $(command -v "$1")"
        return 0
    else
        log_error "$1 not found. Please install it first."
        return 1
    fi
}

log_info "Checking prerequisites..."

MISSING=0
check_command "python3" || MISSING=1
check_command "node"    || MISSING=1
check_command "npm"     || MISSING=1
check_command "docker"  || MISSING=1
check_command "git"     || MISSING=1

if [ "$MISSING" -eq 1 ]; then
    log_error "Missing prerequisites. Please install them and retry."
    exit 1
fi

echo ""

# --------------------------------------------------------------------------
# Setup .env file
# --------------------------------------------------------------------------

ENV_FILE="$ROOT_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    log_info "Creating .env file from template..."
    cat > "$ENV_FILE" << 'ENVEOF'
# ==========================================================================
# Vaktram Environment Variables
# ==========================================================================

# Environment
ENV=development
DEBUG=true
LOG_LEVEL=INFO

# Supabase
SUPABASE_URL=http://localhost:54321
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
SUPABASE_JWT_SECRET=your-jwt-secret-here

# LLM (for summarization)
OPENAI_API_KEY=your-openai-api-key-here
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.3

# Hugging Face (for pyannote diarization)
HF_TOKEN=your-huggingface-token-here

# Service URLs
API_BASE_URL=http://localhost:8000
WEB_BASE_URL=http://localhost:3000
BOT_SERVICE_URL=http://localhost:8100

# Bot Service
BOT_SERVICE_PORT=8100
MAX_CONCURRENT_BOTS=5
HEADLESS=true

# Workers
WHISPER_MODEL=large-v3
COMPUTE_DEVICE=auto
POLL_INTERVAL_SECONDS=5
AUDIO_STORAGE_BUCKET=meeting-recordings
ENVEOF
    log_ok ".env file created at $ENV_FILE"
    log_warn "Please update the .env file with your actual credentials."
else
    log_ok ".env file already exists"
fi

echo ""

# --------------------------------------------------------------------------
# Install Python dependencies for workers
# --------------------------------------------------------------------------

log_info "Setting up Python virtual environment..."

VENV_DIR="$ROOT_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    log_ok "Virtual environment created at $VENV_DIR"
else
    log_ok "Virtual environment already exists"
fi

source "$VENV_DIR/bin/activate"

log_info "Installing bot-service dependencies..."
pip install -q -r "$ROOT_DIR/apps/bot-service/requirements.txt" 2>/dev/null || log_warn "Some bot-service deps may need system packages"

log_info "Installing transcription worker dependencies..."
pip install -q -r "$ROOT_DIR/apps/workers/transcription/requirements.txt" 2>/dev/null || log_warn "Some transcription deps may need GPU support"

log_info "Installing summarizer worker dependencies..."
pip install -q -r "$ROOT_DIR/apps/workers/summarizer/requirements.txt" 2>/dev/null || log_warn "Some summarizer deps may need GPU support"

log_ok "Python dependencies installed"

echo ""

# --------------------------------------------------------------------------
# Install Playwright browsers
# --------------------------------------------------------------------------

log_info "Installing Playwright browsers (Chromium)..."
playwright install chromium 2>/dev/null || log_warn "Playwright install may need to be run manually"

echo ""

# --------------------------------------------------------------------------
# Install frontend dependencies (if web app exists)
# --------------------------------------------------------------------------

WEB_DIR="$ROOT_DIR/apps/web"
if [ -f "$WEB_DIR/package.json" ]; then
    log_info "Installing frontend dependencies..."
    cd "$WEB_DIR" && npm ci
    log_ok "Frontend dependencies installed"
else
    log_warn "No frontend app found at $WEB_DIR (create it later)"
fi

echo ""

# --------------------------------------------------------------------------
# Done
# --------------------------------------------------------------------------

echo "=========================================="
echo -e "  ${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Update .env with your credentials"
echo "  2. Start Supabase:  npx supabase start"
echo "  3. Run migrations:  bash infra/scripts/seed-db.sh"
echo "  4. Start services:  (see docs/DEPLOYMENT.md)"
echo ""

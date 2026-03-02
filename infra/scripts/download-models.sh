#!/usr/bin/env bash
# ==========================================================================
# Download ML models for transcription and diarization
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

# Load environment
if [ -f "$ROOT_DIR/.env" ]; then
    set -a
    source "$ROOT_DIR/.env"
    set +a
fi

MODELS_DIR="${MODELS_DIR:-$ROOT_DIR/models}"
WHISPER_MODEL="${WHISPER_MODEL:-large-v3}"
HF_TOKEN="${HF_TOKEN:-}"

echo ""
echo "=========================================="
echo "  Vaktram Model Downloader"
echo "=========================================="
echo ""

mkdir -p "$MODELS_DIR"

# --------------------------------------------------------------------------
# Check Python environment
# --------------------------------------------------------------------------

VENV_DIR="$ROOT_DIR/.venv"
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
fi

if ! command -v python3 &> /dev/null; then
    log_error "Python 3 not found"
    exit 1
fi

# --------------------------------------------------------------------------
# Download Faster-Whisper model
# --------------------------------------------------------------------------

log_info "Downloading Faster-Whisper model: $WHISPER_MODEL"
log_info "This may take several minutes depending on your connection..."

python3 -c "
from faster_whisper import WhisperModel
import os

model_size = os.environ.get('WHISPER_MODEL', 'large-v3')
print(f'Downloading {model_size}...')

# This triggers the download to the default cache directory
model = WhisperModel(model_size, device='cpu', compute_type='int8')
print('Whisper model downloaded and verified.')
" 2>&1 && log_ok "Faster-Whisper model downloaded" || {
    log_warn "Failed to download Whisper model. You can retry later or download manually."
    log_warn "The model will be auto-downloaded on first worker startup."
}

echo ""

# --------------------------------------------------------------------------
# Download pyannote diarization model
# --------------------------------------------------------------------------

if [ -z "$HF_TOKEN" ]; then
    log_warn "HF_TOKEN not set. Skipping pyannote model download."
    log_warn "pyannote/speaker-diarization-3.1 requires a Hugging Face token."
    log_warn "Set HF_TOKEN in your .env and re-run this script."
else
    log_info "Downloading pyannote speaker diarization model..."

    python3 -c "
import os
os.environ['HF_TOKEN'] = os.environ.get('HF_TOKEN', '')

from pyannote.audio import Pipeline

token = os.environ.get('HF_TOKEN')
print('Downloading pyannote/speaker-diarization-3.1...')
pipeline = Pipeline.from_pretrained(
    'pyannote/speaker-diarization-3.1',
    use_auth_token=token,
)
print('pyannote model downloaded and verified.')
" 2>&1 && log_ok "pyannote diarization model downloaded" || {
        log_warn "Failed to download pyannote model."
        log_warn "Ensure your HF_TOKEN has access to pyannote/speaker-diarization-3.1"
        log_warn "Accept the license at: https://huggingface.co/pyannote/speaker-diarization-3.1"
    }
fi

echo ""

# --------------------------------------------------------------------------
# Download sentence-transformers embedding model
# --------------------------------------------------------------------------

log_info "Downloading sentence-transformers embedding model..."

python3 -c "
from sentence_transformers import SentenceTransformer

print('Downloading all-MiniLM-L6-v2...')
model = SentenceTransformer('all-MiniLM-L6-v2')
dim = model.get_sentence_embedding_dimension()
print(f'Embedding model downloaded (dimension={dim}).')
" 2>&1 && log_ok "Embedding model downloaded" || {
    log_warn "Failed to download embedding model. It will be downloaded on first use."
}

echo ""

echo "=========================================="
echo -e "  ${GREEN}Model download complete!${NC}"
echo "=========================================="
echo ""
echo "Models are cached in your local HuggingFace/torch cache directory."
echo "For Docker deployments, models will be downloaded at container startup."
echo ""

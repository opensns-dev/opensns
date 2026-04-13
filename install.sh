#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/opensns-dev/opensns.git"
DIR="opensns"

command_exists() { command -v "$1" &>/dev/null; }

gen_secret() { openssl rand -hex 32; }

set_env() {
  local key="$1" val="$2"
  sed -i.bak "s|^${key}=.*|${key}=${val}|" .env
  rm -f .env.bak
}

ask() {
  local prompt="$1" var="$2" default="${3:-}"
  if [ -n "$default" ]; then
    printf "%s [%s]: " "$prompt" "$default"
  else
    printf "%s: " "$prompt"
  fi
  read -r input
  eval "$var=\"${input:-$default}\""
}

setup_ai_providers() {
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  AI Provider Setup"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  # ── LLM Engine ──────────────────────────────
  echo ""
  echo "LLM Engine (generates ad copy & strategy)"
  echo "  1) OpenAI    — GPT-4o"
  echo "  2) Anthropic — Claude"
  echo "  3) Google    — Gemini"
  echo "  4) Groq      — Fast open-source models (Llama 3.3)"
  echo "  5) Ollama    — Local models, free (requires Ollama running)"
  echo "  6) Skip      — Configure later"
  echo ""
  ask "Choose LLM engine" llm_choice "1"

  case "$llm_choice" in
    1)
      ask "OpenAI API key" openai_key ""
      if [ -n "$openai_key" ]; then
        set_env "OPENAI_API_KEY" "$openai_key"
        set_env "DEFAULT_LLM_ENGINE" "openai"
        echo "  ✓ OpenAI configured"
      else
        echo "  ⚠ No key entered, skipping."
      fi
      ;;
    2)
      ask "Anthropic API key" anthropic_key ""
      if [ -n "$anthropic_key" ]; then
        set_env "ANTHROPIC_API_KEY" "$anthropic_key"
        set_env "DEFAULT_LLM_ENGINE" "anthropic"
        echo "  ✓ Anthropic configured"
      else
        echo "  ⚠ No key entered, skipping."
      fi
      ;;
    3)
      ask "Google API key" google_key ""
      if [ -n "$google_key" ]; then
        set_env "GOOGLE_API_KEY" "$google_key"
        set_env "DEFAULT_LLM_ENGINE" "gemini"
        echo "  ✓ Gemini configured"
      else
        echo "  ⚠ No key entered, skipping."
      fi
      ;;
    4)
      ask "Groq API key" groq_key ""
      if [ -n "$groq_key" ]; then
        set_env "GROQ_API_KEY" "$groq_key"
        set_env "DEFAULT_LLM_ENGINE" "groq"
        echo "  ✓ Groq configured"
      else
        echo "  ⚠ No key entered, skipping."
      fi
      ;;
    5)
      ask "Ollama URL" ollama_url "http://localhost:11434"
      set_env "OLLAMA_URL" "$ollama_url"
      set_env "DEFAULT_LLM_ENGINE" "ollama"
      echo "  ✓ Ollama configured ($ollama_url)"
      ;;
    *)
      echo "  Skipped. Edit .env later to set your LLM provider."
      ;;
  esac

  # ── Image Engine ────────────────────────────
  echo ""
  echo "Image Engine (generates ad images)"
  echo "  1) Fal.ai    — Fast cloud inference (also powers video)"
  echo "  2) ComfyUI   — Local Stable Diffusion (requires ComfyUI running)"
  echo "  3) Skip      — Configure later"
  echo ""
  ask "Choose Image engine" img_choice "1"

  case "$img_choice" in
    1)
      ask "Fal.ai API key" fal_key ""
      if [ -n "$fal_key" ]; then
        set_env "FAL_KEY" "$fal_key"
        set_env "DEFAULT_IMAGE_ENGINE" "fal"
        set_env "DEFAULT_VIDEO_ENGINE" "fal-video"
        echo "  ✓ Fal.ai configured (image + video)"
      else
        echo "  ⚠ No key entered, skipping."
      fi
      ;;
    2)
      ask "ComfyUI URL" comfyui_url "http://localhost:8188"
      set_env "COMFYUI_URL" "$comfyui_url"
      set_env "DEFAULT_IMAGE_ENGINE" "comfyui"
      set_env "DEFAULT_VIDEO_ENGINE" "comfyui-video"
      echo "  ✓ ComfyUI configured ($comfyui_url)"
      ;;
    *)
      echo "  Skipped. Edit .env later to set your Image provider."
      ;;
  esac

  # ── Video Engine (if not already set by Fal.ai/ComfyUI) ──
  if [ "$img_choice" != "1" ] && [ "$img_choice" != "2" ]; then
    echo ""
    echo "Video Engine (image-to-video for Reels/TikTok)"
    echo "  1) Fal.ai    — Cloud (requires FAL_KEY, enter above or now)"
    echo "  2) ComfyUI   — Local (requires ComfyUI running)"
    echo "  3) Skip      — Configure later"
    echo ""
    ask "Choose Video engine" vid_choice "3"

    case "$vid_choice" in
      1)
        ask "Fal.ai API key (if not entered above)" fal_key_vid ""
        if [ -n "$fal_key_vid" ]; then
          set_env "FAL_KEY" "$fal_key_vid"
        fi
        set_env "DEFAULT_VIDEO_ENGINE" "fal-video"
        echo "  ✓ Fal.ai video configured"
        ;;
      2)
        ask "ComfyUI URL" comfyui_url_vid "http://localhost:8188"
        set_env "COMFYUI_URL" "$comfyui_url_vid"
        set_env "DEFAULT_VIDEO_ENGINE" "comfyui-video"
        echo "  ✓ ComfyUI video configured"
        ;;
      *)
        echo "  Skipped."
        ;;
    esac
  fi

  # ── UGC Video (optional) ────────────────────
  echo ""
  ask "Set up UGC video? (AI avatar talking-head videos) [y/N]" setup_ugc "n"

  if [[ "$setup_ugc" =~ ^[Yy] ]]; then
    echo ""
    echo "UGC Video Engine"
    echo "  1) HeyGen     — Cloud AI avatars"
    echo "  2) D-ID       — Cloud AI avatars"
    echo "  3) SadTalker  — Self-hosted, free"
    echo ""
    ask "Choose UGC engine" ugc_choice "1"

    case "$ugc_choice" in
      1)
        ask "HeyGen API key" heygen_key ""
        if [ -n "$heygen_key" ]; then
          set_env "HEYGEN_API_KEY" "$heygen_key"
          set_env "DEFAULT_UGC_ENGINE" "heygen"
          echo "  ✓ HeyGen configured"
        fi
        ;;
      2)
        ask "D-ID API key" did_key ""
        if [ -n "$did_key" ]; then
          set_env "DID_API_KEY" "$did_key"
          set_env "DEFAULT_UGC_ENGINE" "d-id"
          echo "  ✓ D-ID configured"
        fi
        ;;
      3)
        ask "SadTalker URL" sadtalker_url "http://localhost:7860"
        set_env "SADTALKER_URL" "$sadtalker_url"
        set_env "DEFAULT_UGC_ENGINE" "sadtalker"
        echo "  ✓ SadTalker configured ($sadtalker_url)"
        ;;
      *)
        echo "  Skipped."
        ;;
    esac
  fi

  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

main() {
  for cmd in git docker openssl; do
    if ! command_exists "$cmd"; then
      echo "Error: $cmd is required but not installed." >&2
      exit 1
    fi
  done

  if ! docker compose version &>/dev/null; then
    echo "Error: docker compose plugin is required." >&2
    exit 1
  fi

  if [ -d "$DIR" ]; then
    echo "Directory '$DIR' already exists. Pulling latest..."
    cd "$DIR" && git pull --ff-only
  else
    echo "Cloning $REPO..."
    git clone "$REPO"
    cd "$DIR"
  fi

  if [ ! -f .env ]; then
    cp .env.example .env
    sed -i.bak "s/^JWT_SECRET_KEY=$/JWT_SECRET_KEY=$(gen_secret)/" .env
    sed -i.bak "s/^API_KEY_ENCRYPTION_KEY=$/API_KEY_ENCRYPTION_KEY=$(gen_secret)/" .env
    rm -f .env.bak
    echo "Created .env with generated secrets."
    setup_ai_providers
  else
    echo ".env already exists, skipping."
  fi

  echo "Starting services..."
  docker compose up -d

  echo ""
  echo "OpenSNS is running!"
  echo "  Frontend: http://localhost:3000"
  echo "  Backend:  http://localhost:8000"
  echo "  API Docs: http://localhost:8000/docs"
}

main

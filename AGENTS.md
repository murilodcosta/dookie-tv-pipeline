# Dookie Tv — Automation Pipeline (MVP)

## Overview

A children's YouTube Shorts channel ("Dookie Tv") featuring 3 fixed animal mascots (Dookie, Mia, Carrot). The MVP goal is to publish **1 video per day** in a **fully automated** way, with a single human approval gate via Telegram (<10 min/day). We are not optimizing for virality — the MVP exists to validate whether the pipeline runs reliably and cheaply (~$25-50/month) over a 14-28 day pilot.

The full, detailed scope lives in Obsidian: `C:\Users\muril\Documents\ObsidianNotes\Projects\dookie-tv\MVP_Project_Scope.md`

**Whenever a pipeline step is completed, update the corresponding checklist in that Obsidian file instead of only marking it in code.**

## Stack and Architecture

- **Language:** Python 3.11+
- **Containerization:** Docker + docker-compose (single service, no microservices)
- **Video processing:** FFmpeg / MoviePy
- **Deployment:** Oracle Free Tier VPS (Ampere A1, ARM/aarch64, Ubuntu, 2 OCPU / 12GB RAM)
- **VPS access:** Connection details (host, SSH key path) are documented in `NOTES.local.md` (gitignored, per-developer).
- **Database:** Local SQLite (`src/db/`)
- **Storage:** Cloudflare R2 (S3-compatible bucket, `src/storage/`) with local fallback mode
- **Human approval / notifications:** Telegram Bot API (`src/upload/telegram_bot.py`)
- **Publishing:** YouTube Data API v3 OAuth2 (`src/upload/youtube_uploader.py`)
- **TTS & Video API Engine:** Segmind API (Segmind Seedance 2.0 for video, Segmind TTS for audio narration)

⚠️ **Architecture note:** The local dev machine is x86 (Windows), but production is ARM (aarch64). Don't assume binary compatibility between the two. Production builds must be done directly on the VPS (`docker compose build` run there via SSH), not cross-compiled locally.

## Folder Structure

```
src/
  script/     # 3.1 — Script & metadata generation via DeepSeek API
  media/      # 3.2 & 3.3 — Scene image & video animation via Segmind API (Seedance 2.0) + Mock mode
  editor/     # 3.4 & 3.5 — Audio narration via Segmind TTS, final assembly, subtitles (Fredoka), thumbnail template
  upload/     # 3.6 & 3.7 — Telegram review bot (with Redo sub-menu) + YouTube upload
  db/         # 3.8 — SQLite schema and topic history manager (7-day no-repeat rule)
  storage/    # Cloudflare R2 client
assets/       # Fixed mascot images, fonts (Fredoka), color palette
config/       # Non-sensitive configs (topics.json, base prompts, etc.)
scripts/      # Infrastructure scripts (setup_vps.sh)
```

Each subfolder under `src/` maps to a section of the pipeline (3.1 to 3.8) described in the MVP scope. When implementing a step, keep the code inside the matching folder.

## Visual Identity (Fixed — Do not change without explicit approval)

- **Palette:** 
  - Sunshine Yellow `#FFD166` (60% background)
  - Sky Blue `#4EA8DE` (30% secondary/floor)
  - Bubblegum Pink `#EF476F` (10% action/text pop)
  - Midnight Blue `#0F4C81` (text stroke/outline)
- **Font:** Fredoka (Bold/One), white fill, Midnight Blue outline 15-20%
- **Subtitles:** Never more than 2-4 words on screen at once
- **Video format:** 9:16 vertical Full HD (1080x1920), 30-60 seconds

## Useful Commands

```bash
docker compose build              # Build the image (local for testing, VPS for production)
docker compose up                 # Run the full pipeline
docker compose run --rm app ffmpeg -version   # Validate ffmpeg install inside container
python -m pytest                  # Run unit tests
```

## Code Conventions

- Python: Follow PEP 8, use type hints on public functions
- Variable/function names and all comments/log messages in English
- Every external API call (DeepSeek, Nano Banana, Seedance, ElevenLabs, Cloudflare R2, Telegram, YouTube) must have explicit error handling + logging, never fail silently
- Secrets and API keys **never** in code — always via `.env` (which is in `.gitignore`)

## Out of Scope for the MVP (Do not implement unless explicitly requested)

- Multiple channels or languages
- Uploading to other platforms (TikTok, Instagram Reels)
- Premium video tools (Kling Pro, Runway Gen-3, Veo 3.1)
- Complex web dashboards (use Telegram or a spreadsheet instead)
- Advanced monetization, title/thumbnail A/B testing, voice cloning

## Topic & Mascot No-Repeat Rule

The system tracks topics and mascots used in SQLite (`src/db/`). It must never repeat the same topic for the same character within **7 days**.

## Language

All interaction with the AI agent for this project — prompts, AGENTS.md, skills, commit messages, code comments, and generated documentation — should be in English.

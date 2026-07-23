# Dookie Tv — Project Status & Antigravity Setup Handoff

Compiled to switch the AI coding agent from Claude Code to **Antigravity CLI**
(running on Gemini 3.5/3.6 Flash — see note under section 3 about the model
name). This file recaps everything decided so far and lays out what to
configure before sending the first prompt to Antigravity.

---

## 1. What has been done so far

### Channel identity & content (done)
- Channel name: Dookie Tv
- 3 mascots: Dookie (boxer dog), Mia (white cat), Carrot (orange rabbit)
- Fixed color palette, font (Fredoka), thumbnail template, banner/profile picture
- Topic bank (11 rotating topics) with a 7-day no-repeat rule per character

### Infrastructure (Sprint 0, in progress)
- **VPS provider:** Oracle Cloud Free Tier — Ampere A1 (ARM/aarch64)
  - Shape: `VM.Standard.A1.Flex`, 2 OCPU / 12GB RAM (current Always Free limit
    as of June 2026, down from the old 4 OCPU/24GB)
  - Boot volume: 50-60GB custom size, default in-transit encryption, Oracle-managed key
  - Networking: default VCN + public subnet, auto-assigned public IPv4 (ephemeral),
    no IPv6
  - Account upgraded to Pay As You Go to solve "out of host capacity" errors
    (this is permanent — Oracle does not allow downgrading back to a free-only
    account, but Always Free resources remain free regardless)
  - Instance is **created and running**
- **Cost safety notes:** stick to Always-Free-eligible shape, don't enable
  volume backup policies, don't reserve a static public IP, don't create a
  second instance — all of these are the realistic ways to accidentally incur
  charges, not the free-tier resources themselves.

### Repository & local environment
- Private GitHub repo created and cloned locally to:
  `C:\Users\muril\Projects\Dev\dookie-tv-pipeline`
- **No folders/files created inside it yet** — this is the actual next step.
- Planned folder structure:
  ```
  src/script/   src/media/   src/editor/   src/upload/   src/db/
  assets/       config/
  ```

### Tooling decisions
- **Docker:** yes, single `Dockerfile` + `docker-compose.yml`, one service,
  no microservices. Reasoning: dev machine is x86, production VPS is ARM —
  Docker avoids "works on my machine" issues. Production images should be
  built directly on the VPS (`docker compose build` over SSH), not
  cross-compiled locally.
- **Tools/APIs selected:** DeepSeek API (script/metadata), Nano Banana
  (images), Seedance (video), Suno (background music only — not narration),
  a TTS tool still to be picked for narration (ElevenLabs Starter ~$5/mo or
  a cheaper Google/OpenAI TTS option), Telegram Bot API (human approval
  gate), YouTube Data API with OAuth2 (publishing).
- **Storage:** Cloudflare R2 or Backblaze B2 (or Oracle's own 20GB free
  Object Storage as an alternative worth evaluating).

### AI agent config — originally drafted for Claude Code (see section 2)
We wrote `CLAUDE.md` and `CLAUDE.local.md` for Claude Code, but **the plan
changed to use Antigravity instead**, so these files need to be adapted —
Antigravity does not read `CLAUDE.md`.

---

## 2. Important: Antigravity does not read CLAUDE.md

Antigravity uses a different, Gemini-native convention:

- **`AGENTS.md`** (project root) — project-level standing instructions,
  natively auto-detected by Antigravity since v1.20.3 (March 2026). This is
  the direct equivalent of `CLAUDE.md`.
- **`GEMINI.md`** — can also exist at the project level or globally at
  `~/.gemini/GEMINI.md`. Antigravity reads both `AGENTS.md` and `GEMINI.md`
  at session start and merges them, with `GEMINI.md` taking precedence if
  the two conflict.
- **`.agents/skills/`** — equivalent to Claude Code's `.claude/skills/`, for
  reusable custom capabilities/commands.
- **⚠️ Known conflict:** if you also have the old Gemini CLI installed on
  this machine, both tools currently read the *same* global file
  (`~/.gemini/GEMINI.md`), which can cause instructions to bleed between
  tools. The documented workaround is to keep global/shared rules in
  `~/.gemini/AGENTS.md` instead, and leave `~/.gemini/GEMINI.md` for
  Antigravity-only overrides. This mainly matters for global config — your
  project-level `AGENTS.md` is unaffected.
- Antigravity does **not** have a documented native equivalent to
  `CLAUDE.local.md` (a personal, gitignored file that auto-loads). The
  practical workaround is a plain gitignored file (e.g. `NOTES.local.md`)
  that you reference manually in `AGENTS.md`, since there's no confirmed
  `@import` mechanism for `AGENTS.md` the way Claude Code has for
  `CLAUDE.md`.

**Action needed:** rename/rewrite the content of `CLAUDE.md` into
`AGENTS.md`, and carry over `CLAUDE.local.md`'s content into a gitignored
`NOTES.local.md` (or similar), referenced by name inside `AGENTS.md`.

---

## 3. A note on the model name

You mentioned "Gemini 3.6 Flash (High)." At the time of this research,
publicly available information points to Antigravity 2.0 / Antigravity CLI
running on **Gemini 3.5 Flash** (GA since May 19, 2026), with "High" likely
referring to a reasoning-effort setting exposed in the Antigravity UI/CLI
rather than a separate model version. If your Antigravity install shows
"3.6," that's most likely a newer point release that came out after this
was researched — worth double-checking the exact model string inside the
app itself (or via `agy inspect`, see below) rather than relying on this
document for that detail.

---

## 4. Next steps to continue with Antigravity CLI

1. **Install Antigravity CLI** (the official replacement for Gemini CLI,
   which sunsets for individual users on June 18, 2026). If you already
   have Gemini CLI installed, Antigravity CLI ships a one-shot importer for
   your old extensions, model preferences, and auth state.
2. **Authenticate** with your Google account (note: Antigravity currently
   requires a personal Gmail-type account, not a Workspace/company account,
   per public reports as of mid-2026 — confirm this hasn't changed).
3. **Open a terminal in the project folder**
   (`C:\Users\muril\Projects\Dev\dookie-tv-pipeline`).
4. **Create `AGENTS.md`** in the project root, adapting the content we
   already wrote for `CLAUDE.md` (project overview, stack, folder structure,
   visual identity constants, Docker/ARM note, code conventions, out-of-scope
   list, current sprint status). Ask me to regenerate this content in
   `AGENTS.md` form if you'd like it pre-written again.
5. **Create `NOTES.local.md`** (gitignored) carrying over what was in
   `CLAUDE.local.md`: VPS IP, SSH key path, Obsidian vault path, and the
   reminder to confirm before running any command that touches the
   production VPS.
6. **Add both new files to `.gitignore` correctly** — `AGENTS.md` should be
   committed (shared), `NOTES.local.md` should not.
7. **Run `agy inspect`** (or the equivalent diagnostic command in your
   installed version) to confirm which config files, skills, and MCP servers
   Antigravity actually loaded for this project. This is the Antigravity
   equivalent of Claude Code's `/context`.
8. **Obsidian vault access:** Antigravity's documented mechanism is
   filesystem-native — mounting files like `AGENTS.md` and skills under
   `.agents/skills/` into its working context. Whether it supports an
   equivalent to Claude Code's `--add-dir` flag for an external folder (your
   Obsidian vault) isn't confirmed from available documentation at the time
   of writing. Simplest reliable workaround if a direct flag isn't
   available: keep referencing the vault's `MVP_Project_Scope.md` by full
   path in `AGENTS.md`/`NOTES.local.md`, and check Antigravity's own docs or
   `agy inspect` output for a supported way to add external directories.
9. **First real prompt to Antigravity**, once the above is in place: ask it
   to scaffold the folder structure, `Dockerfile`, `docker-compose.yml`, and
   `requirements.txt` we already planned.

---

## 5. Still open / unresolved before Sprint 1

- TTS tool for narration not yet chosen (ElevenLabs vs cheaper alternative).
- Storage bucket (R2 / B2 / Oracle Object Storage) not yet created.
- SQLite schema not yet drafted.
- Section 3.1 (DeepSeek prompt + JSON schema) not yet built.

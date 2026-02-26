# 🎓 Lecture Transcription & Note Generation Framework

A two-stage pipeline that takes a raw lecture video and produces structured, study-ready notes:

```
  lecture.mp4
      │
      ▼  [Stage 1 — transcribe.py + Whisper]
  lecture_transcript.txt
  lecture_timestamped.txt
      │
      ▼  [Stage 2 — structure_notes.py + Claude]
  lecture_notes_deep.md   ← structured study notes
```

---

## ⚡ Quick Start

### 1. Install system dependency (ffmpeg)

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg

# Windows: https://ffmpeg.org/download.html  (add to PATH)
```

### 2. Install Python packages

```bash
pip install -r requirements.txt
```

### 3. Set your Anthropic API key (for Stage 2)

```bash
export ANTHROPIC_API_KEY='sk-ant-...'
# Get yours at: https://console.anthropic.com/
```

### 4. Run the full pipeline in one command

```bash
python transcribe.py lecture.mp4 --notes
```

This produces:
- `lecture_transcript.txt` — verbatim transcript
- `lecture_timestamped.txt` — transcript with `[HH:MM:SS]` markers
- `lecture_transcript_notes_deep.md` — structured study notes

---

## 📖 Stage 1 — Transcription

```
python transcribe.py <video.mp4> [options]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--model` / `-m` | `base` | Whisper model: tiny, base, small, medium, large, large-v3 |
| `--language` / `-l` | `en` | Language code (`auto` for auto-detect) |
| `--task` / `-t` | `transcribe` | `transcribe` or `translate` (translate → always English) |
| `--output` / `-o` | `txt,timestamped` | Output formats: `txt`, `timestamped`, `srt`, `vtt`, `json`, `md`, `all` |
| `--outdir` | same as video | Save files to a custom directory |
| `--prompt` / `-p` | — | Domain hint (e.g. `"Machine Learning lecture"`) |
| `--keep-audio` | false | Keep the extracted `.wav` audio file |
| `--notes` | false | **Run Stage 2 automatically after transcription** |
| `--notes-style` | `deep` | Note style for Stage 2 |
| `--course` / `-c` | — | Course name passed to Stage 2 |

### Examples

```bash
# Transcribe only (fast)
python transcribe.py lecture.mp4

# Full pipeline: transcribe + generate deep notes
python transcribe.py lecture.mp4 --notes --course "Linear Algebra"

# High accuracy + Cornell-style notes
python transcribe.py lecture.mp4 --model large-v3 --notes --notes-style cornell --course "Quantum Physics"

# Italian lecture, translated to English, then notes
python transcribe.py lezione.mp4 --language it --task translate --notes

# Batch transcribe a folder
python batch_transcribe.py ./lectures/ --model small
```

---

## 📖 Stage 2 — Note Structuring

Can also be run **independently** on any existing `.txt` transcript:

```
python structure_notes.py <transcript.txt> [options]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--style` / `-s` | `deep` | Note-taking style (see table below) |
| `--course` / `-c` | — | Course name / subject hint |
| `--timestamped` / `-ts` | — | Path to `_timestamped.txt` (adds `[HH:MM:SS]` refs to notes) |
| `--outdir` | same as transcript | Output directory |
| `--output-name` | `<stem>_notes_<style>` | Custom output filename |

### Examples

```bash
# Basic
python structure_notes.py lecture_transcript.txt

# Cornell style with timestamp cross-references
python structure_notes.py lecture_transcript.txt \
  --style cornell \
  --course "Algorithms & Data Structures" \
  --timestamped lecture_timestamped.txt

# Flashcards for exam prep
python structure_notes.py lecture_transcript.txt --style flashcard

# Mind map for Obsidian/Notion
python structure_notes.py lecture_transcript.txt --style mindmap-md --course "Neuroscience"
```

---

## 🎨 Note Styles

| Style | Best for | Produces |
|-------|----------|---------|
| `deep` | Primary study reference | Overview · Key Concepts · Formulas · Examples · Pitfalls · Insights · Summary · Review Questions |
| `cornell` | Active recall while rewatching | Main Notes · Cue Questions · Summary (classic Cornell layout) |
| `outline` | Quick reference / overview | Clean H2/H3/H4 hierarchy · Key Takeaways |
| `mindmap-md` | Visual thinkers, Obsidian | Nested bullet mind map · Glossary |
| `flashcard` | Exam preparation | Q&A pairs grouped by topic · Summary |

> You can fully customize any style by editing `prompts.py` — each style is a plain string in the `STYLES` dict.

---

## 🤖 Whisper Model Comparison

| Model    | Size   | Speed      | Accuracy  | Recommended for |
|----------|--------|------------|-----------|-----------------|
| tiny     | 75 MB  | ⚡⚡⚡⚡⚡  | ⭐⭐      | Quick drafts    |
| base     | 145 MB | ⚡⚡⚡⚡    | ⭐⭐⭐    | Default         |
| small    | 465 MB | ⚡⚡⚡      | ⭐⭐⭐⭐  | CPU recommended |
| medium   | 1.5 GB | ⚡⚡        | ⭐⭐⭐⭐⭐| GPU recommended |
| large-v3 | 3.1 GB | ⚡          | ⭐⭐⭐⭐⭐| Best quality    |

---

## 📁 Output Files Reference

| File | Content |
|------|---------|
| `*_transcript.txt` | Clean word-for-word transcript |
| `*_timestamped.txt` | Transcript with `[HH:MM:SS]` per segment |
| `*.srt` | SubRip subtitles (VLC, video editors) |
| `*.vtt` | WebVTT subtitles (web players) |
| `*_transcript.md` | Markdown transcript grouped in 5-min blocks |
| `*_transcript.json` | Full Whisper output (word-level timestamps) |
| `*_notes_<style>.md` | **Structured study notes** (Stage 2 output) |

---

## 💡 Tips

- Pass `--prompt "Machine Learning, gradient descent"` to improve terminology recognition in Stage 1
- Use `--timestamped` in Stage 2 to get `[HH:MM:SS]` links in your notes — great for jumping back to the video while studying
- Long lectures (>1 hour) are automatically split into chunks and merged — no extra configuration needed
- Edit `prompts.py` to fully customize the LLM's behavior, output sections, and formatting style

---

## 🔧 Requirements

```
openai-whisper
ffmpeg-python
torch
anthropic
```

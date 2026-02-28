#!/usr/bin/env python3
"""
Lecture Transcription Framework
Powered by OpenAI Whisper

Usage:
    python transcribe.py <video.mp4> [options]
"""

import argparse
import json
import sys
import time
from pathlib import Path
from datetime import timedelta


# ──────────────────────────────────────────────
# DEPENDENCY CHECK
# ──────────────────────────────────────────────

def check_dependencies():
    missing = []
    try:
        import whisper
    except ImportError:
        missing.append("openai-whisper")
    try:
        import ffmpeg
    except ImportError:
        missing.append("ffmpeg-python")

    if missing:
        print("❌ Missing dependencies. Install with:\n")
        print(f"   pip install {' '.join(missing)}\n")
        sys.exit(1)

    return True


# ──────────────────────────────────────────────
# AUDIO EXTRACTION
# ──────────────────────────────────────────────

def extract_audio(video_path: Path, audio_path: Path):
    import ffmpeg

    print(f"🎬 Extracting audio from: {video_path.name}")

    (
        ffmpeg
        .input(str(video_path))
        .output(
            str(audio_path),
            format="wav",
            acodec="pcm_s16le",
            ac=1,
            ar="16000"
        )
        .overwrite_output()
        .run(quiet=True)
    )

    return audio_path


# ──────────────────────────────────────────────
# TRANSCRIPTION
# ──────────────────────────────────────────────

def transcribe(audio_path, model_name="base", language="en", task="transcribe", initial_prompt=None):
    import whisper

    print(f"🧠 Loading Whisper model: {model_name}")
    model = whisper.load_model(model_name)

    start = time.time()

    options = dict(
        language=language,
        task=task,
        verbose=False,
        word_timestamps=True,
    )

    if initial_prompt:
        options["initial_prompt"] = initial_prompt

    result = model.transcribe(str(audio_path), **options)

    print(f"✅ Done in {int(time.time() - start)} seconds")

    return result


# ──────────────────────────────────────────────
# SAVE FUNCTIONS
# ──────────────────────────────────────────────

def save_plain_text(result, path):
    path.write_text(result["text"].strip(), encoding="utf-8")
    print(f"📄 Saved → {path}")


def main():
    parser = argparse.ArgumentParser(description="Transcribe lecture videos using Whisper")

    parser.add_argument("video", type=Path)
    parser.add_argument("--model", "-m", default="base")
    parser.add_argument("--language", "-l", default="en")
    parser.add_argument("--task", "-t", default="transcribe", choices=["transcribe", "translate"])
    parser.add_argument("--outdir", type=Path, default=None)
    parser.add_argument("--prompt", "-p", default=None)
    parser.add_argument("--keep-audio", action="store_true")

    args = parser.parse_args()

    video_path = args.video.resolve()
    if not video_path.exists():
        print(f"❌ File not found: {video_path}")
        sys.exit(1)

    out_dir = args.outdir or video_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = video_path.stem
    audio_path = out_dir / f"{stem}_audio.wav"

    check_dependencies()
    extract_audio(video_path, audio_path)

    result = transcribe(
        audio_path,
        model_name=args.model,
        language=None if args.language == "auto" else args.language,
        task=args.task,
        initial_prompt=args.prompt,
    )

    save_plain_text(result, out_dir / f"{stem}_transcript.txt")

    if not args.keep_audio:
        audio_path.unlink(missing_ok=True)

    print(f"\n🎉 Transcription complete! Output folder: {out_dir}\n")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Lecture Transcription Framework
Powered by OpenAI Whisper

Usage:
    python transcribe.py <video.mp4> [options]
"""

import argparse
import json
import shutil
import sys
import time
import tempfile
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

def split_audio_in_two_chunks(audio_path: Path):
    import ffmpeg

    probe_info = ffmpeg.probe(str(audio_path))
    duration_str = probe_info.get("format", {}).get("duration")
    if duration_str is None:
        return [(audio_path, 0.0)], None

    duration = float(duration_str)
    if duration <= 1.0:
        return [(audio_path, 0.0)], None

    midpoint = duration / 2.0

    temp_dir = Path(tempfile.mkdtemp(prefix="transcribe_chunks_"))
    chunk_1 = temp_dir / "chunk_1.wav"
    chunk_2 = temp_dir / "chunk_2.wav"

    (
        ffmpeg
        .input(str(audio_path), ss=0, t=midpoint)
        .output(str(chunk_1), format="wav", acodec="pcm_s16le", ac=1, ar="16000")
        .overwrite_output()
        .run(quiet=True)
    )

    (
        ffmpeg
        .input(str(audio_path), ss=midpoint)
        .output(str(chunk_2), format="wav", acodec="pcm_s16le", ac=1, ar="16000")
        .overwrite_output()
        .run(quiet=True)
    )

    return [(chunk_1, 0.0), (chunk_2, midpoint)], temp_dir


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

    chunks, chunk_temp_dir = split_audio_in_two_chunks(Path(audio_path))
    if len(chunks) == 2:
        print("✂️ Splitting audio into 2 near-equal chunks for transcription")

    try:
        chunk_results = []
        for index, (chunk_path, offset) in enumerate(chunks, start=1):
            if len(chunks) > 1:
                print(f"📝 Transcribing chunk {index}/{len(chunks)}")
            chunk_result = model.transcribe(str(chunk_path), **options)
            chunk_results.append(chunk_result)
    finally:
        if chunk_temp_dir is not None:
            shutil.rmtree(chunk_temp_dir, ignore_errors=True)

    print(f"✅ Done in {int(time.time() - start)} seconds")

    return chunk_results


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

    chunk_results = transcribe(
        audio_path,
        model_name=args.model,
        language=None if args.language == "auto" else args.language,
        task=args.task,
        initial_prompt=args.prompt,
    )

    if chunk_results:
        save_plain_text(chunk_results[0], out_dir / "Transcription_Pt1.txt")
    else:
        (out_dir / "Transcription_Pt1.txt").write_text("", encoding="utf-8")
        print(f"📄 Saved → {out_dir / 'Transcription_Pt1.txt'}")

    if len(chunk_results) > 1:
        save_plain_text(chunk_results[1], out_dir / "Transcription_Pt2.txt")
    else:
        (out_dir / "Transcription_Pt2.txt").write_text("", encoding="utf-8")
        print(f"📄 Saved → {out_dir / 'Transcription_Pt2.txt'}")

    if not args.keep_audio:
        audio_path.unlink(missing_ok=True)

    print(f"\n🎉 Transcription complete! Output folder: {out_dir}\n")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║          LECTURE TRANSCRIPTION FRAMEWORK                     ║
║          Powered by OpenAI Whisper                           ║
╚══════════════════════════════════════════════════════════════╝

Usage:
    python transcribe.py <video.mp4> [options]

Examples:
    python transcribe.py lecture.mp4
    python transcribe.py lecture.mp4 --model large --output txt
    python transcribe.py lecture.mp4 --language en --timestamps --output all
"""

import argparse
import json
import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import timedelta


# ──────────────────────────────────────────────
# DEPENDENCY CHECK
# ──────────────────────────────────────────────

def check_dependencies():
    """Check that required packages are installed."""
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
        print("❌ Missing dependencies. Install them with:\n")
        print(f"   pip install {' '.join(missing)}\n")
        print("Also make sure ffmpeg is installed on your system:")
        print("   macOS:   brew install ffmpeg")
        print("   Ubuntu:  sudo apt install ffmpeg")
        print("   Windows: https://ffmpeg.org/download.html\n")
        sys.exit(1)

    return True


# ──────────────────────────────────────────────
# AUDIO EXTRACTION
# ──────────────────────────────────────────────

def extract_audio(video_path: Path, audio_path: Path) -> Path:
    """
    Extract audio from MP4 video using ffmpeg.
    Returns the path to the extracted audio file.
    """
    import ffmpeg

    print(f"🎬 Extracting audio from: {video_path.name}")

    try:
        (
            ffmpeg
            .input(str(video_path))
            .output(
                str(audio_path),
                format="wav",
                acodec="pcm_s16le",
                ac=1,           # mono
                ar="16000"      # 16kHz – optimal for Whisper
            )
            .overwrite_output()
            .run(quiet=True)
        )
        print(f"✅ Audio extracted → {audio_path.name}")
        return audio_path

    except ffmpeg.Error as e:
        print(f"❌ ffmpeg error: {e.stderr.decode()}")
        sys.exit(1)


# ──────────────────────────────────────────────
# TRANSCRIPTION
# ──────────────────────────────────────────────

def transcribe(
    audio_path: Path,
    model_name: str = "base",
    language: str = "en",
    task: str = "transcribe",
    initial_prompt: str = None,
) -> dict:
    """
    Run Whisper transcription on an audio file.

    Args:
        audio_path:     Path to the WAV audio file
        model_name:     Whisper model size (tiny|base|small|medium|large)
        language:       Source language code (e.g. 'en', 'it', 'fr')
        task:           'transcribe' or 'translate' (translate → always outputs English)
        initial_prompt: Optional hint to improve accuracy (e.g. course subject)

    Returns:
        Whisper result dict with keys: text, segments, language
    """
    import whisper

    print(f"\n🧠 Loading Whisper model: '{model_name}'  (first run downloads the model)")
    model = whisper.load_model(model_name)

    print(f"📝 Transcribing... (language: {language}, task: {task})")
    start = time.time()

    options = dict(
        language=language,
        task=task,
        verbose=False,
        word_timestamps=True,  # enables per-word timing
    )
    if initial_prompt:
        options["initial_prompt"] = initial_prompt

    result = model.transcribe(str(audio_path), **options)

    elapsed = timedelta(seconds=int(time.time() - start))
    print(f"✅ Transcription complete in {elapsed}")

    return result


# ──────────────────────────────────────────────
# FORMATTERS
# ──────────────────────────────────────────────

def format_timestamp(seconds: float) -> str:
    """Convert seconds to SRT/VTT-style timestamp HH:MM:SS,mmm"""
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    millis = int((seconds - int(seconds)) * 1000)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def format_vtt_timestamp(seconds: float) -> str:
    """WebVTT uses dots instead of commas"""
    return format_timestamp(seconds).replace(",", ".")


def save_plain_text(result: dict, output_path: Path):
    """Save plain continuous transcript (word-for-word, no timestamps)."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result["text"].strip())
        f.write("\n")
    print(f"📄 Plain text  → {output_path}")


def save_timestamped_text(result: dict, output_path: Path):
    """Save transcript with [HH:MM:SS] timestamps per segment."""
    with open(output_path, "w", encoding="utf-8") as f:
        for seg in result["segments"]:
            ts = format_timestamp(seg["start"]).split(",")[0]  # drop milliseconds
            f.write(f"[{ts}]  {seg['text'].strip()}\n")
    print(f"🕐 Timestamped → {output_path}")


def save_srt(result: dict, output_path: Path):
    """Save SubRip (.srt) subtitle file."""
    with open(output_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(result["segments"], start=1):
            f.write(f"{i}\n")
            f.write(f"{format_timestamp(seg['start'])} --> {format_timestamp(seg['end'])}\n")
            f.write(f"{seg['text'].strip()}\n\n")
    print(f"🎞  SRT subtitles → {output_path}")


def save_vtt(result: dict, output_path: Path):
    """Save WebVTT (.vtt) subtitle file."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for i, seg in enumerate(result["segments"], start=1):
            f.write(f"{i}\n")
            f.write(f"{format_vtt_timestamp(seg['start'])} --> {format_vtt_timestamp(seg['end'])}\n")
            f.write(f"{seg['text'].strip()}\n\n")
    print(f"🌐 VTT subtitles → {output_path}")


def save_json(result: dict, output_path: Path):
    """Save full Whisper result as JSON (includes word-level timestamps)."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"📦 JSON (full)  → {output_path}")


def save_markdown(result: dict, output_path: Path, video_name: str):
    """Save a nicely formatted Markdown transcript."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# Lecture Transcript\n")
        f.write(f"**Source:** `{video_name}`  \n")
        f.write(f"**Language:** {result.get('language', 'en').upper()}  \n\n")
        f.write("---\n\n")

        # Group segments into ~5-minute chunks for readability
        chunk_duration = 300  # seconds
        current_chunk_start = 0
        chunk_lines = []

        for seg in result["segments"]:
            if seg["start"] >= current_chunk_start + chunk_duration:
                # Write accumulated chunk
                ts = str(timedelta(seconds=int(current_chunk_start)))[:-3] if int(current_chunk_start) >= 3600 \
                    else str(timedelta(seconds=int(current_chunk_start)))[2:]
                f.write(f"## ⏱ {ts}\n\n")
                f.write(" ".join(chunk_lines).strip() + "\n\n")
                chunk_lines = []
                current_chunk_start = seg["start"]

            chunk_lines.append(seg["text"].strip())

        # Write last chunk
        if chunk_lines:
            ts_str = str(timedelta(seconds=int(current_chunk_start)))
            f.write(f"## ⏱ {ts_str}\n\n")
            f.write(" ".join(chunk_lines).strip() + "\n\n")

    print(f"📝 Markdown     → {output_path}")


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Transcribe university lecture videos using OpenAI Whisper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "video",
        type=Path,
        help="Path to input MP4 video file"
    )
    parser.add_argument(
        "--model", "-m",
        default="base",
        choices=["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"],
        help="Whisper model size (default: base). Larger = more accurate but slower."
    )
    parser.add_argument(
        "--language", "-l",
        default="en",
        help="Language of the lecture (default: en). Use 'auto' for auto-detect."
    )
    parser.add_argument(
        "--task", "-t",
        default="transcribe",
        choices=["transcribe", "translate"],
        help="'transcribe' keeps original language; 'translate' outputs English (default: transcribe)"
    )
    parser.add_argument(
        "--output", "-o",
        default="txt,timestamped",
        help=(
            "Comma-separated list of output formats. "
            "Options: txt, timestamped, srt, vtt, json, md, all "
            "(default: txt,timestamped)"
        )
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=None,
        help="Output directory (default: same folder as input video)"
    )
    parser.add_argument(
        "--prompt", "-p",
        default=None,
        help="Optional initial prompt to improve transcription (e.g. 'Machine Learning lecture')"
    )
    parser.add_argument(
        "--keep-audio",
        action="store_true",
        help="Keep the extracted WAV audio file after transcription"
    )

    # ── Note generation stage (optional)
    parser.add_argument(
        "--notes",
        action="store_true",
        help=(
            "After transcription, automatically generate structured study notes "
            "using Claude (requires ANTHROPIC_API_KEY env variable)"
        )
    )
    parser.add_argument(
        "--notes-style",
        default="deep",
        choices=["deep", "cornell", "outline", "mindmap-md", "flashcard"],
        help=(
            "Note-taking style used when --notes is enabled (default: deep). "
            "Options: deep | cornell | outline | mindmap-md | flashcard"
        )
    )
    parser.add_argument(
        "--notes-model", 
        default="llama3.1:8b", 
        help="Ollama model to use for note structuring (default: llama3.1:8b)"
    )
    parser.add_argument(
        "--course", "-c",
        default="",
        help="Course name passed to the note structurer (e.g. 'Linear Algebra')"
    )

    args = parser.parse_args()

    # ── Validate input
    video_path = args.video.resolve()
    if not video_path.exists():
        print(f"❌ File not found: {video_path}")
        sys.exit(1)
    if video_path.suffix.lower() not in (".mp4", ".mov", ".avi", ".mkv", ".webm"):
        print(f"⚠️  Unexpected file extension: {video_path.suffix}. Proceeding anyway...")

    # ── Output directory
    out_dir = args.outdir or video_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = video_path.stem

    # ── Determine requested formats
    requested = set(f.strip().lower() for f in args.output.split(","))
    if "all" in requested:
        requested = {"txt", "timestamped", "srt", "vtt", "json", "md"}

    # ── Check dependencies
    check_dependencies()

    print("\n" + "═" * 60)
    print(f"  🎓 Lecture Transcription Framework")
    print(f"  Video   : {video_path.name}")
    print(f"  Model   : {args.model}")
    print(f"  Language: {args.language}")
    print(f"  Formats : {', '.join(sorted(requested))}")
    print("═" * 60 + "\n")

    # ── Extract audio
    audio_path = out_dir / f"{stem}_audio.wav"
    extract_audio(video_path, audio_path)

    # ── Transcribe
    lang = None if args.language == "auto" else args.language
    result = transcribe(
        audio_path=audio_path,
        model_name=args.model,
        language=lang,
        task=args.task,
        initial_prompt=args.prompt,
    )

    # ── Save outputs
    print(f"\n💾 Saving outputs to: {out_dir}\n")

    if "txt" in requested:
        save_plain_text(result, out_dir / f"{stem}_transcript.txt")

    if "timestamped" in requested:
        save_timestamped_text(result, out_dir / f"{stem}_timestamped.txt")

    if "srt" in requested:
        save_srt(result, out_dir / f"{stem}.srt")

    if "vtt" in requested:
        save_vtt(result, out_dir / f"{stem}.vtt")

    if "json" in requested:
        save_json(result, out_dir / f"{stem}_transcript.json")

    if "md" in requested:
        save_markdown(result, out_dir / f"{stem}_transcript.md", video_path.name)

    # ── Cleanup
    if not args.keep_audio:
        audio_path.unlink(missing_ok=True)

    print(f"\n✨ Transcription done! All files saved in: {out_dir}")

    # ── Optional: generate structured notes via Claude
    if args.notes:
        print(f"\n{'═' * 60}")
        print(f"  📓 Starting Note Structuring Stage")
        print(f"{'═' * 60}\n")

        # Ensure the plain-text transcript exists (required by structure_notes_ollama.py)
        txt_path = out_dir / f"{stem}_transcript.txt"
        if not txt_path.exists():
            # Save it now if not already saved
            save_plain_text(result, txt_path)

        ts_path = out_dir / f"{stem}_timestamped.txt"

        import subprocess
        cmd = [
            sys.executable,
            str(Path(__file__).parent / "structure_notes_ollama.py"),
            str(txt_path),
            "--style", args.notes_style,
            "--model", args.notes_model,
            "--outdir", str(out_dir),
        ]
        if ts_path.exists():
            cmd += ["--timestamped", str(ts_path)]
        if args.course:
            cmd += ["--course", args.course]
        if args.notes_model:
            cmd += ["--model", args.notes_model]

        subprocess.run(cmd, check=True)

    print(f"\n🎉 All done! Output folder: {out_dir}\n")


if __name__ == "__main__":
    main()

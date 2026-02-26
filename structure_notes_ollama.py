#!/usr/bin/env python3
"""
Lecture Note Structurer (LOCAL)
Powered by Ollama (no API keys, free, offline)

Usage:
  python structure_notes_ollama.py <transcript.txt> [options]

Examples:
  python structure_notes_ollama.py lecture_transcript.txt
  python structure_notes_ollama.py lecture_transcript.txt --style cornell --model qwen2.5:7b
  python structure_notes_ollama.py lecture_transcript.txt --timestamped lecture_timestamped.txt
"""

import argparse
import sys
import subprocess
from pathlib import Path

# Keep your chunking logic similar to the original
CHUNK_SIZE = 12_000  # chars
DEFAULT_MODEL = "llama3.1:8b"


def load_text(path: Path) -> str:
    if not path.exists():
        print(f"❌ File not found: {path}")
        sys.exit(1)
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        print(f"❌ Empty file: {path}")
        sys.exit(1)
    return text


def split_into_chunks(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    while text:
        if len(text) <= chunk_size:
            chunks.append(text)
            break

        split_at = text.rfind(". ", 0, chunk_size)
        if split_at == -1:
            split_at = chunk_size

        chunks.append(text[: split_at + 1].strip())
        text = text[split_at + 1 :].strip()

    return chunks


def check_ollama_installed():
    try:
        subprocess.run(["ollama", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        print("❌ Ollama not found. Install it first:\n")
        print("   curl -fsSL https://ollama.com/install.sh | sh\n")
        sys.exit(1)


def call_ollama(model: str, prompt: str) -> str:
    """
    Calls: ollama run <model>
    Feeds prompt via stdin to avoid shell quoting issues.
    """
    proc = subprocess.run(
        ["ollama", "run", model],
        input=prompt.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    if proc.returncode != 0:
        print("❌ Ollama error:\n")
        print(proc.stderr.decode("utf-8", errors="ignore"))
        sys.exit(1)

    return proc.stdout.decode("utf-8", errors="ignore").strip()


def structure_single_chunk(
    chunk: str,
    style_description: str,
    course_hint: str,
    system_prompt: str,
    user_template: str,
    chunk_index: int,
    total_chunks: int,
) -> str:
    course_str = f"\nCourse / subject: {course_hint}" if course_hint else ""

    chunk_context = ""
    if total_chunks > 1:
        if chunk_index < total_chunks:
            chunk_context = (
                f"\n\nNote: This is part {chunk_index} of {total_chunks} of the lecture. "
                "Generate notes only for this part, using the same section structure. "
                "Do NOT add a Summary or Review Questions section — those will be added at the end."
            )
        else:
            chunk_context = (
                f"\n\nNote: This is the FINAL part ({chunk_index} of {total_chunks}) of the lecture. "
                "Generate notes for this part AND add the Summary and Review Questions section "
                "covering the entire lecture (use your best judgment from the context)."
            )

    user_message = user_template.format(
        course_hint=course_str + chunk_context,
        style=style_description,
        transcript=chunk,
    )

    # Many local LLMs work best with a single combined prompt:
    prompt = f"{system_prompt}\n\n{user_message}"
    return prompt


def merge_chunked_notes(
    model: str,
    parts: list[str],
    style_description: str,
    course_hint: str,
    system_prompt: str,
) -> str:
    combined = "\n\n---\n\n".join(f"### PART {i+1}\n\n{p}" for i, p in enumerate(parts))
    course_str = f"Course / subject: {course_hint}\n" if course_hint else ""

    merge_prompt = f"""{system_prompt}

You produced the following structured notes for a multi-part lecture transcript.
{course_str}
Merge them into a single, coherent Markdown document following the style: **{style_description}**

Rules:
- Remove duplicate section headers
- Preserve all content (do not summarize or cut)
- Ensure section numbering and structure is consistent
- Keep only ONE Summary and ONE Review Questions section at the end

--- PARTS START ---
{combined}
--- PARTS END ---

Output the final merged document now.
"""
    return call_ollama(model, merge_prompt)


def main():
    parser = argparse.ArgumentParser(description="Structure a lecture transcript into study notes using local Ollama")
    parser.add_argument("transcript", type=Path, help="Path to transcript .txt")
    parser.add_argument("--style", "-s", default="deep", choices=["deep", "cornell", "outline", "mindmap-md", "flashcard"])
    parser.add_argument("--course", "-c", default="", help="Course name / hint")
    parser.add_argument("--timestamped", "-ts", type=Path, default=None, help="Optional timestamped transcript")
    parser.add_argument("--outdir", type=Path, default=None, help="Output directory")
    parser.add_argument("--output-name", type=str, default=None, help="Custom output filename (without extension)")
    parser.add_argument("--model", "-m", default=DEFAULT_MODEL, help=f"Ollama model (default: {DEFAULT_MODEL})")

    args = parser.parse_args()

    check_ollama_installed()

    # import your prompts from prompts.py
    from prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, STYLES

    transcript_path = args.transcript.resolve()
    out_dir = (args.outdir or transcript_path.parent).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = args.output_name or f"{transcript_path.stem}_notes_{args.style}"
    output_path = out_dir / f"{stem}.md"

    transcript = load_text(transcript_path)

    # Optional: enrich with timestamped context (your existing approach)
    if args.timestamped and args.timestamped.exists():
        ts_text = load_text(args.timestamped)
        transcript = (
            "=== TIMESTAMPED VERSION (use [HH:MM:SS] markers to reference moments) ===\n\n"
            + ts_text
            + "\n\n=== PLAIN VERSION ===\n\n"
            + transcript
        )

    style_description = STYLES.get(args.style, STYLES["deep"])
    chunks = split_into_chunks(transcript)
    total = len(chunks)

    print("\n" + "═" * 60)
    print("  📓 Lecture Note Structurer (LOCAL)")
    print(f"  Transcript : {transcript_path.name}")
    print(f"  Style      : {args.style}")
    print(f"  Model      : {args.model}")
    print(f"  Chunks     : {total}")
    print("═" * 60 + "\n")

    if total == 1:
        prompt = structure_single_chunk(
            chunk=chunks[0],
            style_description=style_description,
            course_hint=args.course,
            system_prompt=SYSTEM_PROMPT,
            user_template=USER_PROMPT_TEMPLATE,
            chunk_index=1,
            total_chunks=1,
        )
        notes = call_ollama(args.model, prompt)
    else:
        parts = []
        for i, chunk in enumerate(chunks, 1):
            print(f"⚙️  Processing chunk {i}/{total}...")
            prompt = structure_single_chunk(
                chunk=chunk,
                style_description=style_description,
                course_hint=args.course,
                system_prompt=SYSTEM_PROMPT,
                user_template=USER_PROMPT_TEMPLATE,
                chunk_index=i,
                total_chunks=total,
            )
            parts.append(call_ollama(args.model, prompt))

        print("\n🔗 Merging parts...")
        notes = merge_chunked_notes(
            model=args.model,
            parts=parts,
            style_description=style_description,
            course_hint=args.course,
            system_prompt=SYSTEM_PROMPT,
        )

    output_path.write_text(notes, encoding="utf-8")
    print(f"\n✅ Notes saved → {output_path}\n")


if __name__ == "__main__":
    main()
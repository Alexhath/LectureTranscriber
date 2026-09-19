# LectureTranscriber

LectureTranscriber uses OpenAI Whisper to transcribe recorded lessons. It is designed as the first step in a study workflow:

1. `transcribe.py` extracts the audio from a video and transcribes it with Whisper.
2. The transcription is split into two text files so it can be reviewed or supplied to an LLM in manageable parts.
3. An LLM is used manually to turn the two transcription files into a structured note file.

The LLM step is intentionally separate from this project. You can use the model and prompt that best fit your workflow.

## Workflow

```text
lecture.mp4
    |
    v
transcribe.py + Whisper
    |
    +--> Transcription_Pt1.txt
    |
    +--> Transcription_Pt2.txt
             |
             v
       Manual LLM processing
             |
             v
       structured_notes.md
```

## Requirements

- Python 3.10 or newer
- `ffmpeg`
- `openai-whisper`
- `ffmpeg-python`
- `PySide6` for the graphical interface
- PyTorch, installed as part of the Whisper setup

Install the Python dependencies with:

```bash
pip install openai-whisper ffmpeg-python PySide6
```

Install `ffmpeg` separately if it is not already available:

```bash
# Ubuntu / Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

For Windows, install `ffmpeg` and add it to `PATH`.

## Transcribe a Lecture

Run:

```bash
python transcribe.py path/to/lecture.mp4
```

The script creates two files in the same directory as the video:

- `Transcription_Pt1.txt`: the first half of the transcription
- `Transcription_Pt2.txt`: the second half of the transcription

The audio is split into two near-equal chunks before transcription. Temporary audio chunks are removed automatically. The extracted audio is also removed when transcription finishes unless `--keep-audio` is used.

## Options

```text
--model, -m       Whisper model: tiny, base, small, medium, large, or large-v3
--language, -l    Language code; defaults to en, or use auto for detection
--task, -t        transcribe or translate; defaults to transcribe
--outdir          Directory for the output files
--prompt, -p      Optional prompt containing domain-specific terminology
--keep-audio      Keep the extracted WAV audio file
```

Examples:

```bash
# Use a smaller model for a faster draft
python transcribe.py lecture.mp4 --model small

# Automatically detect the spoken language
python transcribe.py lecture.mp4 --language auto

# Save the results to a separate directory
python transcribe.py lecture.mp4 --outdir ./transcriptions

# Keep the extracted audio file for inspection
python transcribe.py lecture.mp4 --keep-audio
```

## Use the Graphical Interface

Launch the GUI from the project directory with:

```bash
python transcribe_gui.py
```

To create an application icon on the Linux desktop, create a launcher file:

```bash
mkdir -p ~/.local/share/applications
nano ~/.local/share/applications/lecture-transcriber.desktop
```

Paste the following content into the file. Replace `/path/to/TranscribeLectures` with the absolute path to this repository:

```ini
[Desktop Entry]
Type=Application
Name=LectureTranscriber
Comment=Transcribe lectures with Whisper
Exec=/usr/bin/python3 /path/to/TranscribeLectures/transcribe_gui.py
Path=/path/to/TranscribeLectures
Terminal=false
Categories=AudioVideo;Education;
```

Make the launcher executable:

```bash
chmod +x ~/.local/share/applications/lecture-transcriber.desktop
```

The application should then appear in the desktop application menu. You can right-click it and choose **Add to Desktop** or **Add to Favorites**, depending on your desktop environment.

If Python or the project dependencies are installed inside a virtual environment, use that environment's Python executable in `Exec`, for example:

```ini
Exec=/path/to/TranscribeLectures/.venv/bin/python /path/to/TranscribeLectures/transcribe_gui.py
```

## Create Structured Notes

After transcription, provide both text files to an LLM manually. A useful prompt should ask the LLM to:

- combine both parts into one coherent lecture
- preserve important definitions, explanations, examples, and formulas
- remove repetition and transcription noise
- organize the result with clear headings and subheadings
- identify questions or concepts that need further review
- save the result as a Markdown file

The resulting note file is created by your LLM workflow and is not generated automatically by `transcribe.py`.

## Whisper Models

| Model | Approximate size | Typical use |
| --- | ---: | --- |
| `tiny` | 75 MB | Fast drafts |
| `base` | 145 MB | Default starting point |
| `small` | 465 MB | Better accuracy on CPU |
| `medium` | 1.5 GB | Higher accuracy with a capable GPU |
| `large-v3` | 3.1 GB | Best accuracy, highest resource use |

The model is downloaded by Whisper on first use. Model files are kept in Whisper's cache and should not be committed to this repository.

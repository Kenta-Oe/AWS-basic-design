"""Text-to-Speech utility for Windows using the latest OpenAI TTS model.

This script reads Japanese (or any language) text from an external file and
converts it to speech audio using the OpenAI TTS API.  It defaults to the
`gpt-4o-mini-tts` model, which is the latest streaming-capable TTS model at the
moment of writing.  Run this script on Windows with Python 3.9+ after installing
```
pip install openai
```
and setting the environment variable `OPENAI_API_KEY`.

Example:
    python openai_tts_reader.py memo.txt --voice alloy --output speech.mp3
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from openai import OpenAI


DEFAULT_MODEL = "gpt-4o-mini-tts"
DEFAULT_VOICE = "alloy"
DEFAULT_FORMAT = "mp3"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Convert text from a file into speech audio using the latest OpenAI "
            "text-to-speech model."
        )
    )
    parser.add_argument(
        "text_file",
        type=Path,
        help="Path to the text memo file that will be converted into speech.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("speech.mp3"),
        help=(
            "Path for the generated audio file. The extension should match the "
            "requested audio format (default: speech.mp3)."
        ),
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"OpenAI TTS model to use (default: {DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--voice",
        default=DEFAULT_VOICE,
        help=f"Voice preset to use for synthesis (default: {DEFAULT_VOICE}).",
    )
    parser.add_argument(
        "--format",
        default=DEFAULT_FORMAT,
        choices=["mp3", "wav", "ogg"],
        help="Audio format to request from the API (default: mp3).",
    )
    return parser.parse_args(argv)


def read_text(text_path: Path) -> str:
    if not text_path.exists():
        raise FileNotFoundError(f"Text file not found: {text_path}")
    return text_path.read_text(encoding="utf-8").strip()


def synthesize_speech(text: str, output_path: Path, *, model: str, voice: str, audio_format: str) -> None:
    client = OpenAI()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with client.audio.speech.with_streaming_response.create(
        model=model,
        voice=voice,
        input=text,
        format=audio_format,
    ) as response:
        response.stream_to_file(output_path)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    try:
        text = read_text(args.text_file)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1

    if not text:
        print("The provided text file is empty.", file=sys.stderr)
        return 1

    try:
        synthesize_speech(
            text,
            args.output,
            model=args.model,
            voice=args.voice,
            audio_format=args.format,
        )
    except Exception as exc:  # noqa: BLE001 - surface API errors to the user
        print(f"Failed to synthesize speech: {exc}", file=sys.stderr)
        return 1

    print(f"Audio saved to {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

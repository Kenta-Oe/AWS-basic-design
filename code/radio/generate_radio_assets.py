import argparse
import datetime
import json
import re
import subprocess
from pathlib import Path

from api_config import get_openai_client

SCRIPT_MODEL = "gpt-4.1-mini"
TTS_MODEL = "gpt-4o-mini-tts"
TTS_VOICE = "alloy"

BASE_DIR = Path(__file__).resolve().parent
SCRIPT_DIR = BASE_DIR / "scripts"
AUDIO_DIR = BASE_DIR / "audio"
BGM_DIR = BASE_DIR.parent / "bgm"


def sanitize_filename(title: str) -> str:
    """タイトルを安全なファイル名に変換します。"""
    safe = re.sub(r"[\\/:*?\"<>|]", "_", title.strip())
    safe = re.sub(r"\s+", "_", safe)
    return safe[:80] or f"radio_script_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"


def build_prompt(topic: str, minutes: int) -> str:
    return f"""
あなたはラジオ番組の構成作家です。
以下の条件で、日本語のラジオ台本を作成してください。

# テーマ
{topic}

# 仕様
- 番組時間の目安: {minutes}分
- 対象: AIの最新情報を知りたい一般リスナー
- 形式: 一人語り
- トーン: 誠実でわかりやすい
- 内容: 最新トレンド、実務活用、注意点(セキュリティ/倫理)、今後の展望
- 話すテンポ: 聞き取りやすい中速。重要点の前後で短い間(1拍)が取れるよう、文を短めに区切る
- 読み上げやすさ: 1文を長くしすぎず、句読点を適切に入れる

必ずJSONで返し、次のキーのみを含めてください:
{{
  "title": "番組タイトル",
  "script": "本文(読み上げ用の台本)"
}}
""".strip()


def generate_script(topic: str, minutes: int) -> dict:
    client = get_openai_client()
    prompt = build_prompt(topic, minutes)

    response = client.chat.completions.create(
        model=SCRIPT_MODEL,
        messages=[
            {"role": "system", "content": "あなたは日本語のプロの放送作家です。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.6,
        response_format={"type": "json_object"},
    )

    payload = response.choices[0].message.content
    data = json.loads(payload)

    if "title" not in data or "script" not in data:
        raise ValueError("AIの応答に title/script がありません。")
    return data


def save_script_file(title: str, script: str) -> Path:
    SCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    file_name = f"{sanitize_filename(title)}.txt"
    path = SCRIPT_DIR / file_name

    with path.open("w", encoding="utf-8") as f:
        f.write(f"タイトル: {title}\n\n")
        f.write(script.strip())
        f.write("\n")

    return path


def synthesize_tts(script_text: str, output_audio_path: Path) -> None:
    client = get_openai_client()
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    with client.audio.speech.with_streaming_response.create(
        model=TTS_MODEL,
        voice=TTS_VOICE,
        input=script_text,
    ) as response:
        response.stream_to_file(str(output_audio_path))


def find_bgm_file() -> Path:
    """BGMフォルダからmp3ファイルを1つ取得します。"""
    if not BGM_DIR.exists():
        raise FileNotFoundError(f"BGMフォルダが見つかりません: {BGM_DIR}")

    bgm_candidates = sorted(BGM_DIR.glob("*.mp3"))
    if not bgm_candidates:
        raise FileNotFoundError(f"BGMフォルダにmp3がありません: {BGM_DIR}")
    return bgm_candidates[0]


def convert_audio_to_mp4(audio_path: Path, video_path: Path, bgm_path: Path) -> None:
    """ナレーション音声にBGMを重ね、黒背景付きのMP4動画へ変換します。"""
    command = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "color=c=black:s=1280x720:r=30",
        "-i",
        str(audio_path),
        "-stream_loop",
        "-1",
        "-i",
        str(bgm_path),
        "-filter_complex",
        "[1:a]volume=1.0[narr];[2:a]volume=0.12[bgm];[narr][bgm]amix=inputs=2:duration=first:dropout_transition=2[mix]",
        "-map",
        "0:v:0",
        "-map",
        "[mix]",
        "-shortest",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        str(video_path),
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError as e:
        raise RuntimeError(
            "ffmpeg が見つかりません。MP4出力には ffmpeg のインストールが必要です。"
        ) from e
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffmpeg でMP4変換に失敗しました: {e.stderr}") from e


def load_script_text(script_file: Path) -> str:
    """テキストファイルから読み上げ本文を読み込みます。"""
    if not script_file.exists():
        raise FileNotFoundError(f"台本ファイルが見つかりません: {script_file}")

    raw = script_file.read_text(encoding="utf-8").strip()
    lines = raw.splitlines()

    if lines and lines[0].startswith("タイトル:"):
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines.pop(0)

    script_text = "\n".join(lines).strip()
    if not script_text:
        raise ValueError(f"台本ファイルの本文が空です: {script_file}")
    return script_text


def create_video_from_script_file(script_file: Path, dry_run: bool = False) -> Path | None:
    script_text = load_script_text(script_file)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    audio_path = AUDIO_DIR / f"{script_file.stem}.mp3"
    video_path = AUDIO_DIR / f"{script_file.stem}.mp4"

    if dry_run:
        return None

    bgm_path = find_bgm_file()
    synthesize_tts(script_text=script_text, output_audio_path=audio_path)
    convert_audio_to_mp4(audio_path=audio_path, video_path=video_path, bgm_path=bgm_path)
    audio_path.unlink(missing_ok=True)
    return video_path


def run(topic: str, minutes: int, dry_run: bool = False, script_file: Path | None = None) -> tuple[Path | None, Path | None]:
    if script_file:
        video_path = create_video_from_script_file(script_file=script_file, dry_run=dry_run)
        return script_file, video_path

    if dry_run:
        title = "【サンプル】最新AIニュースラジオ"
        script = "本日は最新のAI事情を、5つのポイントでわかりやすくお届けします。"
    else:
        data = generate_script(topic=topic, minutes=minutes)
        title = data["title"]
        script = data["script"]

    script_path = save_script_file(title=title, script=script)

    if dry_run:
        return script_path, None

    audio_name = script_path.stem + ".mp3"
    video_name = script_path.stem + ".mp4"
    audio_path = AUDIO_DIR / audio_name
    video_path = AUDIO_DIR / video_name
    bgm_path = find_bgm_file()
    synthesize_tts(script_text=script, output_audio_path=audio_path)
    convert_audio_to_mp4(audio_path=audio_path, video_path=video_path, bgm_path=bgm_path)
    audio_path.unlink(missing_ok=True)
    return script_path, video_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ラジオ台本生成 + TTSでMP4動画化")
    parser.add_argument("--topic", default="最新のAI事情", help="番組のテーマ")
    parser.add_argument("--minutes", type=int, default=8, help="番組時間(分)")
    parser.add_argument(
        "--script-file",
        type=Path,
        help="MP4化したい台本テキストファイルのパス。指定時はこのファイルから動画を作成",
    )
    parser.add_argument("--dry-run", action="store_true", help="APIを呼ばずにファイル生成テスト")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    script_path, video_path = run(
        topic=args.topic,
        minutes=args.minutes,
        dry_run=args.dry_run,
        script_file=args.script_file,
    )

    if script_path:
        print(f"[OK] 台本ファイル: {script_path}")
    if video_path:
        print(f"[OK] 動画ファイル: {video_path}")
    else:
        print("[INFO] dry-run のため動画生成はスキップしました。")


if __name__ == "__main__":
    main()

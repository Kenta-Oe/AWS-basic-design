import argparse
import datetime
import json
import re
from pathlib import Path

from api_config import get_openai_client

SCRIPT_MODEL = "gpt-4.1-mini"
TTS_MODEL = "gpt-4o-mini-tts"
TTS_VOICE = "alloy"

BASE_DIR = Path(r"C:\Users\takky\OneDrive\デスクトップ\code_work\code\radio")
OUTPUT_ROOT = BASE_DIR / "output"
SCRIPT_DIR = OUTPUT_ROOT / "scripts"
AUDIO_DIR = OUTPUT_ROOT / "audio"


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


def run(topic: str, minutes: int, dry_run: bool = False) -> tuple[Path, Path | None]:
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
    audio_path = AUDIO_DIR / audio_name
    synthesize_tts(script_text=script, output_audio_path=audio_path)
    return script_path, audio_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ラジオ台本生成 + TTS音声化")
    parser.add_argument("--topic", default="最新のAI事情", help="番組のテーマ")
    parser.add_argument("--minutes", type=int, default=8, help="番組時間(分)")
    parser.add_argument("--dry-run", action="store_true", help="APIを呼ばずにファイル生成テスト")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    script_path, audio_path = run(topic=args.topic, minutes=args.minutes, dry_run=args.dry_run)

    print(f"[OK] 台本ファイル: {script_path}")
    if audio_path:
        print(f"[OK] 音声ファイル: {audio_path}")
    else:
        print("[INFO] dry-run のため音声生成はスキップしました。")


if __name__ == "__main__":
    main()

import os
from pathlib import Path


def load_env_file(env_path: Path) -> None:
    """.env ファイルを読み込み、未設定の環境変数に反映します。"""
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue

        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def get_openai_client():
    """環境変数からAPIキーを読み込み、OpenAIクライアントを返します。"""
    try:
        from openai import OpenAI
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "openai パッケージが見つかりません。`pip install openai` を実行してください。"
        ) from e

    env_file = Path(__file__).resolve().parent / ".env"
    load_env_file(env_file)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "環境変数 OPENAI_API_KEY が未設定です。"
            "APIキーはコードに直書きせず、.env やOSの環境変数で設定してください。"
        )
    return OpenAI(api_key=api_key)

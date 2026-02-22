import os


def get_openai_client():
    """環境変数からAPIキーを読み込み、OpenAIクライアントを返します。"""
    try:
        from openai import OpenAI
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "openai パッケージが見つかりません。`pip install openai` を実行してください。"
        ) from e

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "環境変数 OPENAI_API_KEY が未設定です。"
            "APIキーはコードに直書きせず、.env やOSの環境変数で設定してください。"
        )
    return OpenAI(api_key=api_key)

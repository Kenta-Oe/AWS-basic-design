# ラジオ台本生成 + TTS 変換

OpenAI APIを使って、
1) 最新AI事情のラジオ台本を生成し、
2) タイトルをファイル名にした台本テキストを保存し、
3) OpenAI Text-to-Speechで音声ファイル(mp3)を出力します。

## ファイル構造

```text
C:\Users\takky\OneDrive\デスクトップ\code_work\code\radio\
├── api_config.py                # APIキー読込専用(メイン処理と分離)
├── generate_radio_assets.py     # 台本生成 + 音声生成のメイン処理
└── output/
    ├── scripts/                 # タイトル名ベースの台本テキスト
    └── audio/                   # タイトル名ベースの音声(mp3)
```

## セキュリティ方針

- APIキーはコードに直書きしない。
- `OPENAI_API_KEY` を環境変数で読み込む。
- APIキー管理は `.env` やOSのシークレット機構を利用する。

## すぐ使うための初期設定（.env）

`code/radio/.env` を用意済みです。`OPENAI_API_KEY` の値だけ更新すれば実行できます。

```env
OPENAI_API_KEY=sk-your-api-key-here
```

## 実行手順（ステップバイステップ）

1. 依存ライブラリをインストール
   ```bash
   pip install openai
   ```

2. APIキーを `.env` に設定（推奨）
   - `code/radio/.env` の `OPENAI_API_KEY` を更新

   または直接環境変数に設定
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```

3. ドライラン（API未使用）で動作確認
   ```bash
   cd "C:\Users\takky\OneDrive\デスクトップ\code_work\code\radio"
   python generate_radio_assets.py --dry-run
   ```

4. 本番実行（台本 + 音声生成）
   ```bash
   cd "C:\Users\takky\OneDrive\デスクトップ\code_work\code\radio"
   python generate_radio_assets.py --topic "最新のAI事情" --minutes 8
   ```

5. 生成物を確認
   - 台本: `C:\Users\takky\OneDrive\デスクトップ\code_work\code\radio\output\scripts\*.txt`
   - 音声: `C:\Users\takky\OneDrive\デスクトップ\code_work\code\radio\output\audio\*.mp3`

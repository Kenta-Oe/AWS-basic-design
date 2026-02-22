# ラジオ台本生成 + TTS 変換

OpenAI APIを使って、
1) 最新AI事情のラジオ台本を生成し、
2) タイトルをファイル名にした台本テキストを保存し、
3) OpenAI Text-to-Speechで生成した音声をMP4動画に変換して出力します。

## ファイル構造

```text
C:\Users\takky\OneDrive\デスクトップ\code_work\code\radio\
├── api_config.py                # APIキー読込専用(メイン処理と分離)
├── generate_radio_assets.py     # 台本生成 + 音声生成のメイン処理
├── scripts/                     # タイトル名ベースの台本テキスト
└── audio/                       # タイトル名ベースの動画(mp4)

C:\Users\takky\OneDrive\デスクトップ\code_work\AWS-basic-design\code\bgm\
└── *.mp3                         # BGM(先頭1ファイルを使用)
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

   MP4変換に `ffmpeg` が必要です（PATHが通っている状態）。
   また、`code/bgm` にBGM用のmp3を置いてください（動画生成時に自動でミックス）。

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

4-2. 既存の台本テキストを引数で渡してMP4化
   ```bash
   cd "C:\Users\takky\OneDrive\デスクトップ\code_work\code\radio"
   python generate_radio_assets.py --script-file "scripts\任意の台本ファイル.txt"
   ```

5. 生成物を確認
   - 台本: `C:\Users\takky\OneDrive\デスクトップ\code_work\code\radio\scripts\*.txt`
   - 動画: `C:\Users\takky\OneDrive\デスクトップ\code_work\code\radio\audio\*.mp4`

※ `--script-file` 指定時は、指定したテキストファイルを読み込んで同名のmp4を `audio/` に出力します。

## BGMについて

- BGMは `C:\Users\takky\OneDrive\デスクトップ\code_work\AWS-basic-design\code\bgm` 配下の `.mp3` を使用します。
- BGMはループ再生され、台本の読み上げが長くても途切れないようにしています。
- ナレーションに対してBGM音量は控えめ（約12%）に調整しています。

## 台本の話すテンポについて

- 台本生成プロンプトに、聞き取りやすい中速テンポ・文を短めに区切る指示を追加しています。
- 重要ポイントの前後で短い間を取りやすい文構成になるよう調整しています。

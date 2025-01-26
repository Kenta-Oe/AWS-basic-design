import os
import datetime
import openai
import docx  # python-docx
from docx.shared import Pt
from secrets import OPENAI_API_KEY

########################################
# ユーザーが変更・調整しやすい変数
########################################
PROJECT_NAME = "AWS_EC2_BasicDesign"
TODAY_STR = datetime.date.today().strftime("%Y%m%d")
OUTPUT_DOCX = f"{PROJECT_NAME}_{TODAY_STR}.docx"

# テンプレートテキストファイルのパス
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEXT_TEMPLATE_PATH = os.path.join(BASE_DIR, "..", "EC2", "text_template.txt")
# EC2フォルダを出力先に指定
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "EC2")

# ChatGPTモデル指定
GPT_MODEL = "gpt-4"
TEMPERATURE = 0.3
MAX_TOKENS = 1500

########################################

def read_text_template(filepath):
    """テキストテンプレート(ユーザーが記入済み)を読み込む"""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"テンプレートファイルが見つかりません: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return content

def call_gpt_api(system_msg, user_msg):
    """ChatGPT-4 APIを呼び出して企業向け基本設計書の文面を生成"""
    openai.api_key = OPENAI_API_KEY

    response = openai.ChatCompletion.create(
        model=GPT_MODEL,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS
    )
    result = response.choices[0].message.content
    return result

def generate_word_document(doc_text, output_path):
    """doc_text(Markdown風テキストなど)をWordファイルに整形して保存する"""
    doc = docx.Document()

    # スタイル: フォントサイズや行間など必要に応じて調整
    style = doc.styles['Normal']
    font = style.font
    font.name = 'ＭＳ ゴシック'  # Windows日本語向けフォント例
    font.size = Pt(11)

    # 複数行を段落に分割
    for line in doc_text.splitlines():
        doc.add_paragraph(line)

    doc.save(output_path)
    print(f"[INFO] Wordファイルを出力しました: {output_path}")

def main():
    print("=== EC2基本設計書生成スクリプト ===")

    # 1. テンプレート読み込み
    try:
        template_text = read_text_template(TEXT_TEMPLATE_PATH)
        print("[DEBUG] テンプレートテキストを読み込み完了")
    except FileNotFoundError as e:
        print(f"エラー: {e}")
        return

    # 2. プロンプトを組み立て (system, user)
    system_content = (
        "あなたはAWSのEC2に関するインフラ設計に非常に詳しいコンサルタントです。"
        "企業向けの言葉遣いで、誰が読んでもわかりやすい説明を心がけてください。"
    )

    user_content = f"""以下は、ユーザーが記入したEC2導入ヒアリングシート(テキスト形式)です。
これを元に、企業向けの「基本設計書」を作成してください。
具体的な数値は書かれていない場合、TBDとして補足しても構いません。
構成の理由や注意点をわかりやすく書き加え、正式文書として整理してください。

--- ユーザー記入情報 開始 ---
{template_text}
--- ユーザー記入情報 終了 ---

作成時のフォーマット:
- 見出しや章立てを使用して構成
- 全体として敬体(です・ます調)で整える
- 専門用語には簡単な解説を付ける
"""

    # 3. ChatGPT-4で基本設計書を生成
    try:
        design_text = call_gpt_api(system_content, user_content)
        print("[DEBUG] AI応答を受け取りました。")
    except Exception as e:
        print(f"[ERROR] ChatGPT API呼び出しエラー: {e}")
        return

    # 4. Wordファイルに整形
    print("[INFO] Wordドキュメントを生成します...")
    # EC2フォルダに出力するように変更
    full_output_path = os.path.join(OUTPUT_DIR, OUTPUT_DOCX)
    generate_word_document(design_text, full_output_path)

    print("[DONE] 全処理が完了しました。")

if __name__ == "__main__":
    main()
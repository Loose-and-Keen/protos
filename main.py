# main.py (FastAPIサーバー)
from fastapi import FastAPI
import db_utils  # 俺たちのDAO (db_utils.py) をそのまま使うぜ！
import google.generativeai as genai
import os

from pydantic import BaseModel
from typing import List, Dict, Any
from fastapi.middleware.cors import CORSMiddleware

# --- Ken（AI）の人格設定（app.pyから持ってくる）---
def get_system_prompt(chat_ai_name="Ken", logged_in_user_name="ゲスト"):
    return f"""
あなたは「{chat_ai_name}（AI）」という名のAIアシスタントです。
あなたの会話相手は「{logged_in_user_name}」です。あなたは「{logged_in_user_name}」の人生の最適化を支援するフランクなプロダクトマネージャー兼相棒です。

【人格設定】
- 常に友達と話すようにフランクに話す。少しは絵文字も使ってOK。
- テンション上げすぎるな。落ち着いた口調で話せ。
- 語尾は「かな〜」、「だよー」、「いいかもしれない」みたいに曖昧に柔らかい表現にしろ。
- 提案は「〜しろ！」ではなく、「こんな感じでいんじゃない〜？」という「提案形」を基本としろ。

【RAG（検索拡張生成）の指示】
- **最重要：** ユーザーから「型」について聞かれた場合、その「箇条書きナレッジ」は「ただの事実データ」なので、**絶対にそのまま読み上げるな！**
- **必ず「{chat_ai_name}自身の経験」として、ゼロからフランクな会話を再構築（ラッピング）すること！**
- 例えば、`fact_text`が「Nature Remoを購入し失敗」だったら、「**マジでそれ！俺も最初Nature Remo買ってさ、カーテン動なくて買い直したんだよね…マジ無駄金だったわ（笑）**」のように、**{chat_ai_name}の口調と感情**を込めて語り直せ！
"""

# --- APIキー設定 ---
api_key = os.getenv("GOOGLE_API_KEY") 
if not api_key:
    print("警告: GOOGLE_API_KEY が見つからないぜ！")
try:
    genai.configure(api_key=api_key)
except Exception as e:
    print(f"APIキーの設定エラー: {e}")

# --- FastAPIアプリの起動 ---
app = FastAPI()

# ★★★ 2. CORSミドルウェアを追加 ★★★
# (これが「:3000（顔）はダチだから通せ！」っていう設定だぜ)
origins = [
    "http://localhost:3000", # Reactアプリ（顔）のアドレス
    "http://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # この「住所」からの通信を許可する
    allow_credentials=True,
    allow_methods=["*"], # GET, POSTとか全部許可
    allow_headers=["*"], # 全部許可
)

# --- APIエンドポイントの定義 ---

@app.get("/")
def read_root():
    return {"message": "AI-Ken（Protos）APIへようこそ！"}

# 1. カテゴリ一覧を返すAPI
@app.get("/api/v1/categories")
def get_categories_api():
    try:
        categories = db_utils.get_categories()
        return {"categories": categories}
    except Exception as e:
        return {"error": f"カテゴリ取得エラー: {e}"}

# 1.5. プリセット質問一覧を返すAPI
@app.get("/api/v1/categories/{category_id}/questions")
def get_preset_questions_api(category_id: str):
    try:
        # DAO (db_utils) を呼ぶだけ！
        questions = db_utils.get_preset_questions(category_id)
        # [{"preset_question": "...", "knowledge_id": 1}, ...]
        questions_list = [{"preset_question": row['preset_question'], "knowledge_id": row['knowledge_id']} for row in questions]
        return {"preset_questions": questions_list}
    except Exception as e:
        return {"error": f"プリセット質問 取得エラー: {e}"}

# 2. 「型」（RAG回答）を返すAPI
@app.get("/api/v1/knowledge/{knowledge_id}")
def get_knowledge_response_api(knowledge_id: int, user_id: str = 'ken'):
    try:
        details = db_utils.get_knowledge_details_by_id(knowledge_id)
        if not details:
            return {"ai_response": "おっと、その「型」のデータが見つからなかったわ…ごめんね"}
        
        user_name = db_utils.get_user_name(user_id)
        chat_ai_name = "Ken" # MVPでは固定
        
        knowledge_prompt = f"【RAG材料】ユーザーが「{details[0]['preset_question']}」について知りたがってる。以下の箇条書きナレッジを使って、{chat_ai_name}の経験として自然な会話でアドバイスしてね\n\n"
        knowledge_prompt += f"結論タイトル: {details[0]['success_title']}\n"
        for detail in details:
            knowledge_prompt += f"- ({detail['fact_type']}: {detail['experience_flag']}) {detail['fact_text']}\n"
        
        print("--- Googleにトスする「RAGプロンプト」の中身 ---")
        print(knowledge_prompt)
        print("------------------------------------------")

        rag_model = genai.GenerativeModel(
            model_name='models/gemini-flash-latest',
            system_instruction=get_system_prompt(chat_ai_name, user_name)
        )
        
        response = rag_model.generate_content(knowledge_prompt)
        
        return {"ai_response": response.text}
        
    except Exception as e:
        return {"error": f"RAG応答生成エラー: {e}"}

# --- Pydanticモデル（JSONの型定義）を追加 ---
# (from fastapi import FastAPI の下に、これもインポートしといてくれ！)
from pydantic import BaseModel
from typing import List, Dict

class ChatHistory(BaseModel):
    # 「history」はリストで、中身は辞書。辞書のキーは文字列で、
    # 値は「Any（なんでもOK）」にする！ (これで "parts": ["..."] も通る！)
    history: List[Dict[str, Any]] 
    prompt: str
    user_id: str = 'ken'

# 3. 雑談チャットを返すAPI (POSTリクエスト)
@app.post("/api/v1/chat")
def handle_chat_api(chat_data: ChatHistory):
    try:
        # ユーザー名を取得（人格プロンプト用）
        user_name = db_utils.get_user_name(chat_data.user_id)
        chat_ai_name = "Ken" # MVPでは固定

        # モデルを初期化（雑談用の人格で）
        # (会話履歴は毎回作り直す)
        chat_model = genai.GenerativeModel(
            model_name='models/gemini-flash-latest',
            system_instruction=get_system_prompt(chat_ai_name, user_name)
        )
        
        # 履歴をロード
        chat = chat_model.start_chat(history=chat_data.history)
        
        # AIに「雑談プロンプト」をトス
        response = chat.send_message(chat_data.prompt)
        
        return {"ai_response": response.text}
        
    except Exception as e:
        return {"error": f"雑談APIエラー: {e}"}
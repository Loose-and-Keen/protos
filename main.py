# main.py (FastAPIサーバー - 最終版)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # CORS
import db_utils  # 俺たちのDAO (db_utils.py)
import google.generativeai as genai
import os
from pydantic import BaseModel
from typing import List, Dict, Any 
import psycopg2 
import psycopg2.extras

# --- Pydanticモデル（JSONの型定義） ---
class ChatHistory(BaseModel):
    history: List[Dict[str, Any]] 
    prompt: str
    user_id: str = 'ken' 

# --- AIの人格設定（グローバル関数） ---
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

# --- FastAPIアプリの起動 & CORS設定 ---
app = FastAPI()

origins = [
    "http://localhost:3000", # ローカル開発用の「顔」
    "https://protos-ui.vercel.app", # Vercelの本番の「顔」
    "http://localhost:8501",         # Streamlitローカル用
    "https://prototype-b9n8fm5qngmj7rfgzp9rqd.streamlit.app" # ← Streamlit本番URLを追加！
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

# --- APIエンドポイントの定義 ---

@app.get("/")
def read_root():
    return {"message": "AI-Ken（Protos）APIへようこそ！"}

@app.get("/api/v1/debug-db-test")
def debug_db_test_api():
    """
    「頭脳（Render）」が「心臓（PostgreSQL）」と本当に接続できてるか、
    DAOを無視して「直接」テストするぜ！
    """
    print("デバッグAPI /api/v1/debug-db-test が叩かれたぜ！")
    try:
        # DB接続URLを「頭脳」の環境変数から取得
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            return {"error": "「頭脳」にDATABASE_URLが設定されてないぜ！"}

        # SSLモード（本番）で「心臓」に接続
        conn = psycopg2.connect(db_url, sslmode='require')
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        print("「心臓（PostgreSQL）」に接続成功！")
        
        # 「m_categories」に「魂」が入ってるか、SQLで直接聞く！
        cursor.execute("SELECT category_id, category_name FROM m_categories ORDER BY sort_order")
        categories = cursor.fetchall()
        print(f"「m_categories」から {len(categories)} 件のデータを取得！")

        cursor.close()
        conn.close()
        
        return {"message": "「頭N脳」と「心臓」は完璧に接続できてるぜ！", "category_count": len(categories), "categories": categories}
        
    except Exception as e:
        print(f"デバッグAPIでエラー発生！: {e}")
        return {"error": f"デバッグAPIでエラー発生！: {e}"}
    
# 1. カテゴリ一覧を返すAPI
@app.get("/api/v1/categories")
def get_categories_api():
    try:
        categories = db_utils.get_categories()
        return {"categories": categories}
    except Exception as e:
        return {"error": f"カテゴリ取得エラー: {e}"}

# ★★★ 1.5. プリセット質問一覧を返すAPI (NEW!) ★★★
@app.get("/api/v1/categories/{category_id}/questions")
def get_preset_questions_api(category_id: str):
    try:
        questions = db_utils.get_preset_questions(category_id)
        # JSON形式に変換
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
        chat_ai_name = "Ken" # MVPでは固定 (将来的にはknowledge_idから引く)
        
        knowledge_prompt = f"【RAG材料】ユーザーが「{details[0]['preset_question']}」について知りたがってる。以下の箇条書きナレッジを使って、{chat_ai_name}の経験として自然な会話でアドバイスしてね\n\n"
        knowledge_prompt += f"結論タイトル: {details[0]['success_title']}\n"
        for detail in details:
            knowledge_prompt += f"- ({detail['fact_type']}: {detail['experience_flag']}) {detail['fact_text']}\n"
        
        rag_model = genai.GenerativeModel(
            model_name='models/gemini-flash-latest',
            system_instruction=get_system_prompt(chat_ai_name, user_name)
        )
        
        response = rag_model.generate_content(knowledge_prompt)
        
        return {"ai_response": response.text}
        
    except Exception as e:
        print(f"RAG応答生成エラー: {e}") # ターミナルにもエラー出す
        return {"error": f"RAG応答生成エラー: {e}"}

# ★★★ 3. 雑談チャットを返すAPI (実装！) ★★★
@app.post("/api/v1/chat")
def handle_chat_api(chat_data: ChatHistory):
    try:
        user_name = db_utils.get_user_name(chat_data.user_id)
        chat_ai_name = "Ken" # MVPでは固定 (将来的にはタブとかから取得)

        chat_model = genai.GenerativeModel(
            model_name='models/gemini-flash-latest',
            system_instruction=get_system_prompt(chat_ai_name, user_name)
        )
        
        chat = chat_model.start_chat(history=chat_data.history)
        response = chat.send_message(chat_data.prompt)
        
        return {"ai_response": response.text}
        
    except Exception as e:
        print(f"雑談APIエラー: {e}") # ターミナルにもエラー出す
        return {"error": f"雑談APIエラー: {e}"}
# app.py (Ver 5.0 - API連携バージョン)
import streamlit as st
import requests  # ← DB Utilsの代わりに「requests」をインポート！
import os

# --- APIサーバーのURLを定義 ---
# （ローカルで動いてる「頭脳」のアドレスだぜ！）
API_BASE_URL = "https://protos-api-sgp.onrender.com"

# --- ページ設定 (変更なし) ---
st.set_page_config(
    page_title="AI-Ken Prototype",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- MVP用 ユーザーID/名前 (DBから取る必要がなくなった！) ---
# （API側が「ken」をデフォルトで知ってるからな）
LOGGED_IN_USER_ID = 'ken' 
LOGGED_IN_USER_NAME = "Ken" # MVPでは固定

# --- Streamlit アプリの UI ---
st.title(f"🤖 {LOGGED_IN_USER_NAME}のスマートライフ Prototype") 
st.caption("powered by Gemini, FastAPI & Streamlit")

# --- 会話履歴を Streamlit のセッション状態で管理 ---
# (Gemini APIキーやモデル設定は、全部「頭脳（FastAPI）」側に移ったから不要だぜ！)
if "messages" not in st.session_state:
    # 最初の挨拶
    st.session_state.messages = [{"role": "assistant", "content": f"よっ、{LOGGED_IN_USER_NAME}！何でも聞いてくれよな！👍"}]

# --- タブのカテゴリを「API」から取得！ ---
try:
    # FastAPIの「/api/v1/categories」を叩く！
    response = requests.get(f"{API_BASE_URL}/api/v1/categories")
    response.raise_for_status() # エラーがあったら例外を発生させる
    
    categories_data = response.json().get("categories", [])
    category_names = [item['category_name'] for item in categories_data]
    category_ids = [item['category_id'] for item in categories_data]
    
    tabs = st.tabs(category_names)

except Exception as e:
    st.error(f"「頭脳（API）」からカテゴリの読み込みでエラーが発生したぜ: {e}")
    st.stop()


# --- 各タブのコンテンツを作成 ---
for i, tab in enumerate(tabs):
    with tab:
        category_id = category_ids[i]
        category_name = category_names[i]
        
        if category_id != 'general':
            st.subheader(f"「Ken」の「{category_name}」の型") # 今は全部 'Ken'
            
            try:
                # APIからプリセット質問を取得 (これもAPI化が必要だが、MVPではスキップ)
                # (本当は db_utils.get_preset_questions もAPI化すべきだが、一旦ハードコードするぜ！)
                # (↑ごめん、Ken！FastAPI側に `get_preset_questions` APIを作るのを忘れてた！)
                # (↑しょうがない、いったん `db_utils` をこっちでもインポートしてごまかすぜ！笑)
                
                # --- 緊急回避（本当はAPIにしたい） ---
                import db_utils 
                preset_questions = db_utils.get_preset_questions(category_id)
                # --- ここまで ---

                if not preset_questions:
                    st.write("（このカテゴリはまだ準備中〜）")

                for question, knowledge_id in preset_questions:
                    if st.button(question, key=f"{category_id}_{knowledge_id}"):
                        st.session_state.messages.append({"role": "user", "content": question})
                        
                        try:
                            # ★★★ ここが核心！「頭脳（FastAPI）」のRAG APIを叩く！ ★★★
                            rag_response = requests.get(f"{API_BASE_URL}/api/v1/knowledge/{knowledge_id}", params={"user_id": LOGGED_IN_USER_ID})
                            rag_response.raise_for_status()
                            
                            response_text = rag_response.json().get("ai_response", "ごめん、AIがエラー吐いたわ…")
                        
                        except Exception as e:
                            response_text = f"おっと、「頭脳（API）」との通信でエラーだ: {e}"

                        st.session_state.messages.append({"role": "assistant", "content": response_text})
                        st.rerun() 

            except Exception as e:
                st.error(f"プリセット質問の読み込みエラー: {e}")

# --- チャット履歴の表示 (全タブ共通) ---
st.divider() 
st.subheader(f"💬 Ken（AI）との会話") 

chat_container = st.container(height=400) 
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# app.py の一番下の「チャット入力」部分を書き換え

# --- ユーザーからのチャット入力を受け付ける (全タブ共通) ---
if prompt := st.chat_input(f"{LOGGED_IN_USER_NAME}、メッセージを入力してくれ！"): 
    st.session_state.messages.append({"role": "user", "content": prompt})
    with chat_container.chat_message("user"): 
        st.markdown(prompt)

    try:
        # ★★★ ここが核心！「頭脳（FastAPI）」の「/api/v1/chat」を叩く！ ★★★
        
        # 1. AIに渡す「会話履歴」を整形
        # (Gemini APIの "parts" 形式に合わせるのがちと面倒だぜ！)
        history_for_api = []
        for msg in st.session_state.messages[:-1]: # 最後の（今送った）メッセージは除く
            role = "model" if msg["role"] == "assistant" else msg["role"]
            history_for_api.append({
                "role": role,
                "parts": [msg["content"]]
            })

        # 2. APIに送るデータ（JSON）
        chat_payload = {
            "history": history_for_api,
            "prompt": prompt,
            "user_id": LOGGED_IN_USER_ID
        }

        # 3. 「頭脳（FastAPI）」にPOSTリクエスト！
        chat_response = requests.post(f"{API_BASE_URL}/api/v1/chat", json=chat_payload)
        chat_response.raise_for_status() # エラーチェック

        response_text = chat_response.json().get("ai_response", "ごめん、AIがエラー吐いたわ…")
        
        # --- (ここから下は変更なし) ---
        with chat_container.chat_message("assistant"): 
            st.markdown(response_text)
        st.session_state.messages.append({"role": "assistant", "content": response_text})
        
        if len(st.session_state.messages) > 50:
             st.session_state.messages = st.session_state.messages[-50:]
             
    except Exception as e:
        st.error(f"AI（/api/v1/chat）との通信でエラーが発生しました: {e}")
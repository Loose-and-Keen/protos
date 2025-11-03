# app.py (Ver 6.0 - 最終分離版)
# 「db_utils」も「genai」も全部消したぜ！

import streamlit as st
import requests  # 「電話機」だけが友達だ！
import os

# --- APIサーバーのURLを定義 ---
# (CEOが「-sgp」に直してくれたやつな！)
API_BASE_URL = "https://protos-api-sgp.onrender.com" 

# --- MVP用 ユーザーID/名前 (ハードコード) ---
LOGGED_IN_USER_ID = 'ken' 
try:
    # ★★★ API経由で「頭脳」からユーザー名を取得！ ★★★
    # (APIが動いてなかったら、"ゲスト" になる)
    user_resp = requests.get(f"{API_BASE_URL}/api/v1/users/{LOGGED_IN_USER_ID}")
    LOGGED_IN_USER_NAME = user_resp.json().get("user_name", "ゲスト(APIエラー)")
except Exception:
    LOGGED_IN_USER_NAME = "ゲスト (API接続エラー)"

# --- ページ設定 (変更なし) ---
st.set_page_config(
    page_title="AI-Ken Prototype",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- Streamlit アプリの UI ---
st.title(f"🤖 {LOGGED_IN_USER_NAME}のスマートライフ Prototype") 
st.caption("powered by FastAPI (Render) & Streamlit (Cloud)")

# --- 会話履歴を Streamlit のセッション状態で管理 ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": f"よっ、{LOGGED_IN_USER_NAME}！何でも聞いてくれよな！👍"}]

# --- タブのカテゴリを「API」から取得！ ---
try:
    response = requests.get(f"{API_BASE_URL}/api/v1/categories")
    response.raise_for_status() 
    
    categories_data = response.json().get("categories", [])
    category_names = [item['category_name'] for item in categories_data]
    category_ids = [item['category_id'] for item in categories_data]
    
    tabs = st.tabs(category_names)

except Exception as e:
    st.error(f"「頭脳（API）」からカテゴリの読み込みに失敗したぜ: {e}")
    st.stop()


# --- 各タブのコンテンツを作成 ---
for i, tab in enumerate(tabs):
    with tab:
        category_id = category_ids[i]
        category_name = category_names[i]
        
        if category_id != 'general':
            st.subheader(f"「Ken」の「{category_name}」の型") 
            
            try:
                # ★★★「プリセット質問」もAPIから取得！★★★
                q_response = requests.get(f"{API_BASE_URL}/api/v1/categories/{category_id}/questions")
                q_response.raise_for_status()
                preset_questions = q_response.json().get("preset_questions", [])

                if not preset_questions:
                    st.write("（このカテゴリはまだ準備中〜）")

                for pq in preset_questions:
                    question = pq['preset_question']
                    knowledge_id = pq['knowledge_id']
                    
                    if st.button(question, key=f"{category_id}_{knowledge_id}"):
                        st.session_state.messages.append({"role": "user", "content": question})
                        
                        try:
                            # ★★★「RAG API」を叩く！★★★
                            rag_response = requests.get(f"{API_BASE_URL}/api/v1/knowledge/{knowledge_id}", params={"user_id": LOGGED_IN_USER_ID})
                            rag_response.raise_for_status()
                            response_json = rag_response.json()

                            if "error" in response_json:
                                response_text = f"頭脳（API）側でエラーだぜ: {response_json['error']}"
                            else:
                                response_text = response_json.get("ai_response", "ごめん、AIがエラー吐いたわ…")
                        
                        except Exception as e:
                            response_text = f"おっと、「頭脳（RAG API）」との通信でエラーだ: {e}"

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

# --- ユーザーからのチャット入力を受け付ける (全タブ共通) ---
if prompt := st.chat_input(f"{LOGGED_IN_USER_NAME}、メッセージを入力してくれ！"): 
    st.session_state.messages.append({"role": "user", "content": prompt})
    with chat_container.chat_message("user"): 
        st.markdown(prompt)

    try:
        # ★★★「雑談API」を叩く！★★★
        history_for_api = []
        for msg in st.session_state.messages[:-1]: 
            role = "model" if msg["role"] == "assistant" else msg["role"]
            history_for_api.append({"role": role, "parts": [msg["content"]]})

        chat_payload = {
            "history": history_for_api,
            "prompt": prompt,
            "user_id": LOGGED_IN_USER_ID
        }

        chat_response = requests.post(f"{API_BASE_URL}/api/v1/chat", json=chat_payload)
        chat_response.raise_for_status() 

        response_json = chat_response.json()
        if "error" in response_json:
            response_text = f"頭脳（API）側でエラーだぜ: {response_json['error']}"
        else:
            response_text = response_json.get("ai_response", "ごめん、AIがエラー吐いたわ…")
        
        # --- (ここから下は変更なし) ---
        with chat_container.chat_message("assistant"): 
            st.markdown(response_text)
        st.session_state.messages.append({"role": "assistant", "content": response_text})
        
        if len(st.session_state.messages) > 50:
             st.session_state.messages = st.session_state.messages[-50:]
             
    except Exception as e:
        st.error(f"「頭脳（Chat API）」との通信でエラーが発生しました: {e}")
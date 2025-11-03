# db_utils.py (Ver 7.0 - 最終版DAO)
# DB構築ロジック(setup_database)を「完全削除」！
# DBはCEO KenがDBeaverで「直接」管理する！

import os
import psycopg2 
import psycopg2.extras 

# --- ★★★ DB接続先を「本番」と「ローカル」で切り替える！ ★★★ ---
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("本番URLが見つからねえ。ローカルのPostgreSQL（protos_dev）に接続するぜ！")
    DATABASE_URL = "postgresql://ken@localhost:5432/protos_dev" 

def get_db_connection():
    """DB接続を返す（ポスグレ仕様）"""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL が設定されてないぜ！")
    
    if "onrender.com" in DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    else:
        conn = psycopg2.connect(DATABASE_URL)
    return conn

# --- 「setup_database()」関数は、ここから「ごっそり削除」だぜ！ ---

# --- これ以降は「DAO関数」 (ポスグレ方言バージョン) ---

def get_categories():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT category_id, category_name FROM m_categories ORDER BY sort_order")
    categories = cursor.fetchall() 
    cursor.close()
    conn.close()
    return categories

def get_preset_questions(category_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT preset_question, knowledge_id FROM m_success_stories WHERE category_id = %s", (category_id,))
    questions = cursor.fetchall()
    cursor.close()
    conn.close()
    return questions

def get_knowledge_details_by_id(knowledge_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("""
        SELECT 
            kb.success_title,
            kb.preset_question, 
            kd.fact_type,
            kd.fact_text,
            kd.experience_flag
        FROM m_experience_details kd
        JOIN m_success_stories kb ON kd.story_id = kb.story_id
        WHERE kd.story_id = %s
        ORDER BY kd.sort_order
    """, (knowledge_id,))
    details = cursor.fetchall()
    cursor.close()
    conn.close()
    return details

def get_user_name(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT user_name FROM m_users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return user['user_name']
    else:
        return "ゲスト"
# db_utils.py (Ver 5.0 - CSV Loader DAO)
import sqlite3
import os
import csv # CSVファイルを読み込むための最強モジュール

DB_NAME = "aiken_user_data.db" # 作成されるDBファイル名

# このスクリプト(db_utils.py)があるフォルダの「絶対パス」を取得
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 全てのファイルパスを、この「絶対パス」基準で定義し直す！
DB_NAME = os.path.join(BASE_DIR, "aiken_user_data.db") # DBファイル本体
CSV_USERS = os.path.join(BASE_DIR, 'data_users.csv')
CSV_CATEGORIES = os.path.join(BASE_DIR, 'data_categories.csv')
CSV_KNOWLEDGE_BASE = os.path.join(BASE_DIR, 'data_knowledge_base.csv')
CSV_KNOWLEDGE_DETAILS = os.path.join(BASE_DIR, 'data_knowledge_details.csv')

def setup_database():
    """
    DBファイルが存在しない場合（＝Streamlit Cloud起動時）に、
    CSVファイルからDBを爆速で自動構築する関数
    """
    # もしDBファイルが「まだ」無かったら、作る
    #if not os.path.exists(DB_NAME):
    # 古いDBファイルがあったら、まず削除する（クリーンな状態にする）
    if os.path.exists(DB_NAME):
        print(f"古い {DB_NAME} を発見！削除するぜ！")
        os.remove(DB_NAME)

    print("CSVからDBを爆速で構築する！")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        # --- 1. スキーマ（骨格）の作成 ---
        # (SQLファイルはもう使わない！Pythonコードに直接書くぜ！)
        cursor.execute("""
        CREATE TABLE M_Users (
            user_id TEXT PRIMARY KEY, user_name TEXT NOT NULL,
            password_hash TEXT NOT NULL, plan_type TEXT DEFAULT 'free' NOT NULL 
        )""")
        
        cursor.execute("""
        CREATE TABLE M_Categories (
            category_id TEXT PRIMARY KEY, category_name TEXT NOT NULL, sort_order INTEGER
        )""")
        
        cursor.execute("""
        CREATE TABLE M_Knowledge_Base (
            knowledge_id INTEGER PRIMARY KEY, /* AUTOINCREMENTを削除し、CSVのIDを正とする */
            category_id TEXT NOT NULL, preset_question TEXT NOT NULL, success_title TEXT,
            FOREIGN KEY (category_id) REFERENCES M_Categories (category_id)
        )""")

        cursor.execute("""
        CREATE TABLE M_Knowledge_Details (
            detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
            knowledge_id INTEGER NOT NULL, fact_type TEXT NOT NULL, 
            fact_text TEXT NOT NULL, experience_flag TEXT DEFAULT 'POSITIVE' NOT NULL, sort_order INTEGER,
            FOREIGN KEY (knowledge_id) REFERENCES M_Knowledge_Base (knowledge_id)
        )""")
        print("テーブル（骨格）の構築完了！")

        # --- 2. CSVからデータ（魂）をぶち込む ---
        # CSVファイルを読み込んでDBにINSERTする汎用ヘルパー関数
        def load_csv_to_db(csv_file, table_name, columns):
            if not os.path.exists(csv_file):
                print(f"警告: {csv_file} が見つからないぜ！スキップする。")
                return
            
            with open(csv_file, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                # カラム名を動的に生成
                cols_sql = ', '.join(columns)
                vals_sql = ', '.join(['?' for _ in columns]) # (?, ?, ?)
                
                data_to_insert = []
                for row in reader:
                    data_to_insert.append(tuple(row[col] for col in columns))
                
                if data_to_insert:
                    cursor.executemany(f"INSERT INTO {table_name} ({cols_sql}) VALUES ({vals_sql})", 
                                        data_to_insert)
                    print(f"{csv_file} から {table_name} へのデータ投入完了！")

        # 各CSVファイルを読み込む
        load_csv_to_db(CSV_USERS, 'M_Users', ['user_id', 'user_name', 'password_hash'])
        load_csv_to_db(CSV_CATEGORIES, 'M_Categories', ['category_id', 'category_name', 'sort_order'])
        load_csv_to_db(CSV_KNOWLEDGE_BASE, 'M_Knowledge_Base', ['knowledge_id', 'category_id', 'preset_question', 'success_title'])
        load_csv_to_db(CSV_KNOWLEDGE_DETAILS, 'M_Knowledge_Details', ['knowledge_id', 'fact_type', 'fact_text', 'experience_flag', 'sort_order'])

        conn.commit()
        print("DB構築完了だぜ！")
        
    except Exception as e:
        print(f"DB構築中にエラー発生！: {e}")
        conn.rollback() # 失敗したらロールバック！
    finally:
        conn.close()
#   else:
#       print("DBファイルは既に存在するぜ。起動を続ける。")

# --- アプリ起動時に必ずDBをチェック・構築 ---
setup_database()

# --- これ以降は、昨日作った「DB操作関数（DAO）」 ---
# (中身は一切変更なし！ `schema.sql` `seed.sql` が不要になっただけ！)

def get_db_connection():
    """DB接続を返す（おまじない）"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row 
    return conn

def get_categories():
    """タブに表示するカテゴリを全部持ってくる"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT category_id, category_name FROM M_Categories ORDER BY sort_order")
    categories = cursor.fetchall()
    conn.close()
    return categories

def get_preset_questions(category_id):
    """指定されたカテゴリのプリセット質問（ボタン用）を持ってくる"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT preset_question, knowledge_id FROM M_Knowledge_Base WHERE category_id = ?", (category_id,))
    questions = cursor.fetchall()
    conn.close()
    return questions

def get_knowledge_details_by_id(knowledge_id):
    """指定されたIDの「経験値の詳細（箇条書きDB）」を持ってくる (RAG用)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            kb.success_title,
            kd.fact_type,
            kd.fact_text,
            kd.experience_flag
        FROM M_Knowledge_Details kd
        JOIN M_Knowledge_Base kb ON kd.knowledge_id = kb.knowledge_id
        WHERE kd.knowledge_id = ?
        ORDER BY kd.sort_order
    """, (knowledge_id,))
    details = cursor.fetchall()
    conn.close()
    return details

def get_user_name(user_id):
    """指定されたユーザーIDのユーザー名を取得する"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_name FROM M_Users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return user['user_name']
    else:
        return "ゲスト"

def get_user_goals_by_category(user_id, category_id):
    """指定されたユーザー/カテゴリの目標リストとステータスを取得"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT goal_key, status FROM T_User_Goals WHERE user_id = ? AND category_id = ?", (user_id, category_id))
    goals = cursor.fetchall()
    conn.close()
    
    if not goals:
        # (中身は昨日と同じ... MVP用：もしT_User_Goalsにまだ目標がなかったら、M_Knowledge_Baseから作ってあげる)
        # ... (省略) ...
        pass # あとで実装しよう！
        
    return goals

def update_user_goal_status(user_id, goal_key, status):
    """ユーザーの目標ステータスを更新"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE T_User_Goals SET status = ? WHERE user_id = ? AND goal_key = ?", (status, user_id, goal_key))
    conn.commit()
    conn.close()

def get_knowledge_details_by_id(knowledge_id):
    """指定されたIDの「経験値の詳細（箇条書きDB）」を持ってくる (RAG用)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # ★★★ ここだ！ `kb.preset_question` をSELECTに追加！ ★★★
    cursor.execute("""
        SELECT 
            kb.success_title,
            kb.preset_question, 
            kd.fact_type,
            kd.fact_text,
            kd.experience_flag
        FROM M_Knowledge_Details kd
        JOIN M_Knowledge_Base kb ON kd.knowledge_id = kb.knowledge_id
        WHERE kd.knowledge_id = ?
        ORDER BY kd.sort_order
    """, (knowledge_id,))
    
    details = cursor.fetchall() # (title, question, type, text, flag)
    conn.close()
    return details
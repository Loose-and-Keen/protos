# db_utils.py (Ver 6.1 - ハイブリッドDB対応)
import os
import psycopg2 # SQLite(sqlite3)の代わりに、PostgreSQL(psycopg2)を使うぜ！
import psycopg2.extras # 辞書形式で結果を受け取るために使う
import csv

# --- ★★★ DB接続先を「本番」と「ローカル」で切り替える！ ★★★ ---

# まず、本番（Render）の環境変数 DATABASE_URL を探しに行く
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # もし無かったら（＝ローカルで開発中だったら）、
    # KenのローカルDB（protos_dev）に接続しにいくぜ！
    print("本番URLが見つからねえ。ローカルのPostgreSQL（protos_dev）に接続するぜ！")
    DATABASE_URL = "postgresql://ken@localhost:5432/protos_dev" # ユーザー名'ken', DB名'protos_dev'

# CSVファイル名（「DBの元ネタ」）の定義
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_USERS = os.path.join(BASE_DIR, 'data_users.csv')
CSV_CATEGORIES = os.path.join(BASE_DIR, 'data_categories.csv')
CSV_KNOWLEDGE_BASE = os.path.join(BASE_DIR, 'data_knowledge_base.csv')
CSV_KNOWLEDGE_DETAILS = os.path.join(BASE_DIR, 'data_knowledge_details.csv')


def get_db_connection():
    """DB接続を返す（ポスグレ仕様）"""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL が設定されてないぜ！")
    
    # ★★★ SSL接続の設定（Renderの本番DBはSSL必須！） ★★★
    if "onrender.com" in DATABASE_URL:
        # 本番（Render）の場合は、SSL接続を強制する
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    else:
        # ローカル（localhost）の場合は、SSL不要
        conn = psycopg2.connect(DATABASE_URL)
        
    return conn

def setup_database():
    """
    DBが空っぽの場合（＝初回起動時）に、
    CSVファイルからDBを爆速で自動構築する関数
    """
    conn = get_db_connection()
    # autocommit=True にしとくと、CREATE TABLEとかで楽だぜ
    conn.autocommit = True 
    cursor = conn.cursor()

    try:
        # --- 0. テーブルが存在するかチェック (ポスグレ方言) ---
        cursor.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'm_users')")
        table_exists = cursor.fetchone()[0]

        if not table_exists:
            print("テーブルが見つからないぜ！CSVからDBを爆速で構築する！")
            
            # --- 1. スキーマ（骨格）の作成 (schema.sql v4 と同じ) ---
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
            CREATE TABLE M_Success_Stories (
                story_id SERIAL PRIMARY KEY,
                creator_user_id TEXT NOT NULL, category_id TEXT, title TEXT NOT NULL, 
                FOREIGN KEY (creator_user_id) REFERENCES M_Users (user_id)
            )""")

            cursor.execute("""
            CREATE TABLE M_Experience_Details (
                detail_id SERIAL PRIMARY KEY,
                story_id INTEGER NOT NULL, fact_type TEXT NOT NULL, 
                fact_text TEXT NOT NULL, experience_flag TEXT DEFAULT 'POSITIVE' NOT NULL, sort_order INTEGER,
                FOREIGN KEY (story_id) REFERENCES M_Success_Stories (story_id)
            )""")
            print("テーブル（骨格）の構築完了！")

            # --- 2. CSVからデータ（魂）をぶち込む ---
            def load_csv_to_db(csv_file, table_name, columns):
                if not os.path.exists(csv_file):
                    print(f"警告: {csv_file} が見つからないぜ！スキップする。") 
                    return
                
                with open(csv_file, mode='r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    data_to_insert = [tuple(row[col] for col in columns) for row in reader]
                    
                    if data_to_insert:
                        cols_sql = ', '.join(columns)
                        # ポスグレは「?」じゃなくて「%s」！
                        vals_sql = ', '.join(['%s' for _ in columns]) 
                        
                        cursor.executemany(f"INSERT INTO {table_name} ({cols_sql}) VALUES ({vals_sql})", 
                                           data_to_insert)
                        print(f"{csv_file} から {table_name} へのデータ投入完了！")

            # 各CSVファイルを読み込む
            load_csv_to_db(CSV_USERS, 'm_users', ['user_id', 'user_name', 'password_hash'])
            load_csv_to_db(CSV_CATEGORIES, 'm_categories', ['category_id', 'category_name', 'sort_order'])
            # ★★★ ポスグレはテーブル名の大文字小文字を区別するから、全部「小文字」に統一！ ★★★
            load_csv_to_db(CSV_KNOWLEDGE_BASE, 'm_success_stories', ['knowledge_id', 'category_id', 'preset_question', 'success_title'])
            load_csv_to_db(CSV_KNOWLEDGE_DETAILS, 'm_experience_details', ['knowledge_id', 'fact_type', 'fact_text', 'experience_flag', 'sort_order'])

            # conn.commit() # autocommit=Trueにしたから不要
            print("DB構築完了だぜ！")
        
        else:
            print("DBテーブルは既に存在するぜ。起動を続ける。")

    except Exception as e:
        print(f"DB構築中にエラー発生！: {e}")
        # conn.rollback() # autocommit=Trueにしたから不要
    finally:
        cursor.close()
        conn.close()


# --- アプリ起動時に必ずDBをチェック・構築 ---
setup_database()

# --- これ以降は「DAO関数」 (ポスグレ方言バージョン) ---

def get_categories():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # ★★★ テーブル名を小文字に ★★★
    cursor.execute("SELECT category_id, category_name FROM m_categories ORDER BY sort_order")
    categories = cursor.fetchall() 
    cursor.close()
    conn.close()
    return categories

def get_preset_questions(category_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # ★★★ テーブル名を小文字に、プレースホルダを %s に ★★★
    cursor.execute("SELECT preset_question, knowledge_id FROM m_success_stories WHERE category_id = %s", (category_id,))
    questions = cursor.fetchall()
    cursor.close()
    conn.close()
    return questions

def get_knowledge_details_by_id(knowledge_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # ★★★ テーブル名を小文字に、プレースホルダを %s に ★★★
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
    # ★★★ テーブル名を小文字に、プレースホルダを %s に ★★★
    cursor.execute("SELECT user_name FROM m_users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return user['user_name']
    else:
        return "ゲスト"
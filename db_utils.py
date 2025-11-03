# db_utils.py (Ver 6.0 - PostgreSQL対応)
import os
import psycopg2 # SQLiteじゃなくて、PostgreSQLを使うぜ！
import psycopg2.extras # 辞書形式で結果を受け取るために使う
import csv

# --- ★★★ DB接続先を「Renderの環境変数」から取得 ★★★ ---
DATABASE_URL = os.getenv("DATABASE_URL")

# CSVファイル名（「DBの元ネタ」）の定義
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_USERS = os.path.join(BASE_DIR, 'data_users.csv')
CSV_CATEGORIES = os.path.join(BASE_DIR, 'data_categories.csv')
CSV_KNOWLEDGE_BASE = os.path.join(BASE_DIR, 'data_knowledge_base.csv')
CSV_KNOWLEDGE_DETAILS = os.path.join(BASE_DIR, 'data_knowledge_details.csv')


def get_db_connection():
    """DB接続を返す（ポスグレ仕様）"""
    if not DATABASE_URL:
        raise ValueError("環境変数 DATABASE_URL が設定されてないぜ！")
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def setup_database():
    """
    DBが空っぽの場合（＝初回起動時）に、
    CSVファイルからDBを爆速で自動構築する関数
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # --- 0. テーブルが存在するかチェック ---
        cursor.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'm_users')")
        table_exists = cursor.fetchone()[0]

        if not table_exists:
            print("テーブルが見つからないぜ！CSVからDBを爆速で構築する！")
            
            # --- 1. スキーマ（骨格）の作成 (ポスグレ仕様に微修正) ---
            # (schema.sqlはもう使わない！`main.py`実行時にこれが走る！)
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
                knowledge_id INTEGER PRIMARY KEY,
                category_id TEXT NOT NULL, preset_question TEXT NOT NULL, success_title TEXT,
                FOREIGN KEY (category_id) REFERENCES M_Categories (category_id)
            )""")

            cursor.execute("""
            CREATE TABLE M_Knowledge_Details (
                detail_id SERIAL PRIMARY KEY, /* ポスグレは AUTOINCREMENT じゃなくて SERIAL が楽 */
                knowledge_id INTEGER NOT NULL, fact_type TEXT NOT NULL, 
                fact_text TEXT NOT NULL, experience_flag TEXT DEFAULT 'POSITIVE' NOT NULL, sort_order INTEGER,
                FOREIGN KEY (knowledge_id) REFERENCES M_Knowledge_Base (knowledge_id)
            )""")
            
            cursor.execute("""
            CREATE TABLE T_User_Goals (
                user_goal_id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL, category_id TEXT NOT NULL,
                goal_key TEXT NOT NULL, status TEXT DEFAULT 'not_started' NOT NULL,
                FOREIGN KEY (user_id) REFERENCES M_Users (user_id),
                FOREIGN KEY (category_id) REFERENCES M_Categories (category_id)
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
                        # ポスグレは「?」じゃなくて「%s」を使う！
                        vals_sql = ', '.join(['%s' for _ in columns]) 
                        
                        cursor.executemany(f"INSERT INTO {table_name} ({cols_sql}) VALUES ({vals_sql})", 
                                           data_to_insert)
                        print(f"{csv_file} から {table_name} へのデータ投入完了！")

            # 各CSVファイルを読み込む
            load_csv_to_db(CSV_USERS, 'm_users', ['user_id', 'user_name', 'password_hash'])
            load_csv_to_db(CSV_CATEGORIES, 'm_categories', ['category_id', 'category_name', 'sort_order'])
            load_csv_to_db(CSV_KNOWLEDGE_BASE, 'm_knowledge_base', ['knowledge_id', 'category_id', 'preset_question', 'success_title'])
            load_csv_to_db(CSV_KNOWLEDGE_DETAILS, 'm_knowledge_details', ['knowledge_id', 'fact_type', 'fact_text', 'experience_flag', 'sort_order'])

            conn.commit()
            print("DB構築完了だぜ！")
        
        else:
            print("DBテーブルは既に存在するぜ。起動を続ける。")

    except Exception as e:
        print(f"DB構築中にエラー発生！: {e}")
        conn.rollback() 
    finally:
        cursor.close()
        conn.close()


# --- アプリ起動時に必ずDBをチェック・構築 ---
setup_database()

# --- これ以降は「DAO関数」 ---

def get_categories():
    conn = get_db_connection()
    # ポスグレは「カラム名でアクセス」するのがちょいムズいから `psycopg2.extras.DictCursor` を使う
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT category_id, category_name FROM M_Categories ORDER BY sort_order")
    categories = cursor.fetchall() 
    cursor.close()
    conn.close()
    return categories

def get_preset_questions(category_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # ポスグレは「?」じゃなくて「%s」！
    cursor.execute("SELECT preset_question, knowledge_id FROM M_Knowledge_Base WHERE category_id = %s", (category_id,))
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
        FROM M_Knowledge_Details kd
        JOIN M_Knowledge_Base kb ON kd.knowledge_id = kb.knowledge_id
        WHERE kd.knowledge_id = %s
        ORDER BY kd.sort_order
    """, (knowledge_id,))
    details = cursor.fetchall()
    cursor.close()
    conn.close()
    return details

def get_user_name(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT user_name FROM M_Users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return user['user_name']
    else:
        return "ゲスト"

# (get_user_goals_by_category と update_user_goal_status も同様に `%s` に書き換える必要があるが、
# CEOが「人生RPGは後回し」って言ったから、一旦MVPからは省略だ！)
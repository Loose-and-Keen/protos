/* schema.sql (v4 - PostgreSQL対応版) */

-- 開発中は古いテーブルを削除してリセット
DROP TABLE IF EXISTS T_User_Goals;
DROP TABLE IF EXISTS M_Experience_Details; 
DROP TABLE IF EXISTS M_Success_Stories;  
DROP TABLE IF EXISTS M_User_Personality; 
DROP TABLE IF EXISTS M_Personality_Traits; 
DROP TABLE IF EXISTS M_Categories;
DROP TABLE IF EXISTS M_Users;

/* --- 1. ユーザーマスター (M_Users) --- */
CREATE TABLE M_Users (
    user_id TEXT PRIMARY KEY,
    user_name TEXT NOT NULL,
    password_hash TEXT NOT NULL, 
    plan_type TEXT DEFAULT 'free' NOT NULL 
);

/* --- 2. 人格マスタ (M_Personality_Traits) --- */
CREATE TABLE M_Personality_Traits (
    trait_id TEXT PRIMARY KEY,
    trait_name TEXT NOT NULL,
    prompt_snippet TEXT NOT NULL
);

/* --- 3. ユーザー人格テーブル (M_User_Personality) --- */
CREATE TABLE M_User_Personality (
    user_id TEXT NOT NULL,
    trait_id TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES M_Users (user_id),
    FOREIGN KEY (trait_id) REFERENCES M_Personality_Traits (trait_id),
    PRIMARY KEY (user_id, trait_id)
);

/* --- 4. サクセスストーリー (M_Success_Stories) --- */
/* ★★★ "INTEGER PRIMARY KEY AUTOINCREMENT" を "SERIAL PRIMARY KEY" に修正 ★★★ */
CREATE TABLE M_Success_Stories (
    story_id SERIAL PRIMARY KEY, /* ← コレがポスグレの「自動連番」だぜ！ */
    creator_user_id TEXT NOT NULL, 
    category_id TEXT, 
    title TEXT NOT NULL, 
    FOREIGN KEY (creator_user_id) REFERENCES M_Users (user_id)
);

/* --- 5. 経験値の詳細 (M_Experience_Details) --- */
/* ★★★ "INTEGER PRIMARY KEY AUTOINCREMENT" を "SERIAL PRIMARY KEY" に修正 ★★★ */
CREATE TABLE M_Experience_Details (
    detail_id SERIAL PRIMARY KEY, /* ← コレがポスグレの「自動連番」だぜ！ */
    story_id INTEGER NOT NULL, 
    fact_type TEXT NOT NULL, 
    fact_text TEXT NOT NULL, 
    experience_flag TEXT DEFAULT 'POSITIVE' NOT NULL, 
    sort_order INTEGER,
    FOREIGN KEY (story_id) REFERENCES M_Success_Stories (story_id)
);

/* (CEOの判断通り、T_User_Goals（人生RPG）は「後回し」！) */
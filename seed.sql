/* seed.sql (v3) - AI-Kenの初期データ（思考OS） */

/* --- 1. ユーザー投入 (Ken = 最初の投稿者) --- */
INSERT INTO M_Users (user_id, user_name, password_hash) VALUES 
('ken', 'Ken', 'dummy_hash_ken'),
('yuki', 'Yuki', 'dummy_hash_yuki'); /* (テスト用にログインユーザーyukiも作っとくか！) */

/* --- 2. 人格マスタ (M_Personality_Traits) 投入 --- */
INSERT INTO M_Personality_Traits (trait_id, trait_name, prompt_snippet) VALUES
('frank', 'フランク', '常にタメ口でフランクに話す。絵文字も使ってOK。'),
('loose_keen', 'Loose & Keen', 'ユーザーに安心感を与えるために、「Loose & Keen」（ゆるく鋭く）なトーンを保て。'),
('propose_style', '提案形', '提案は「〜しろ！」ではなく、「こんな感じでいんじゃない〜？」という「提案形」を基本としろ。'),
('logical', 'ロジカル', '結論から話し、必ず「WHY（なぜなら）」を説明する。'),
('failure_talk', '失敗談を語る', '「FAILURE」フラグのナレッジは、特に「俺もハマったわ〜」という共感を込めて伝えろ。');

/* --- 3. ユーザー人格 (M_User_Personality) 投入 --- */
INSERT INTO M_User_Personality (user_id, trait_id) VALUES
('ken', 'frank'),
('ken', 'loose_keen'),
('ken', 'propose_style'),
('ken', 'logical'),
('ken', 'failure_talk');

/* --- 4. サクセスストーリー (M_Success_Stories) 投入 --- */
INSERT INTO M_Success_Stories (story_id, creator_user_id, category_id, title) VALUES
(1, 'ken', 'smart_home', '5000円で声操作できるようにしたい！(SwitchBotが最短ルート)'),
(2, 'ken', 'money', '投資って何から始めればいい？(S&P500と楽天)'),
(3, 'ken', 'career', 'PM（プロジェクトマネージャー）ってどうやったらなれる？'),
(4, 'ken', 'love', 'マッチングアプリ、めんどくさい… (バチェラーデート)'),
(5, 'ken', 'beauty', '男のスキンケア、何からやればいい？ (美容液と髭脱毛)'),
(6, 'ken', 'fashion', '服選ぶのめんどくさい… (仕事着の固定化)');

/* --- 5. 経験値の詳細 (M_Experience_Details) 投入 --- */
/* (Kenの「箇条書き経験値（苦労話）」だ！) */

/* スマートホーム (story_id = 1) */
INSERT INTO M_Experience_Details (story_id, fact_type, fact_text, experience_flag, sort_order) VALUES
(1, 'WHY', 'SwitchBotはカーテンや他デバイスとの拡張性が高い。', 'POSITIVE', 1),
(1, 'WHY', 'Nature Remoも人気だが、カーテン自動化に非対応なためSwitchBotを推奨。', 'POSITIVE', 2),
(1, 'FAILURE', 'Nature Remoを先に購入し、カーテン自動化できずSwitchBotに買い直した経験あり（無駄金発生）。', 'NEGATIVE', 3),
(1, 'STEP', 'メルカリで「Amazon Echo Show (中古)」を探す。(予算: 〜3000円)', 'POSITIVE', 4),
(1, 'STEP', 'メルカリで「SwitchBot Hub Mini (中古)」を探す。(予算: 〜3000円)', 'POSITIVE', 5),
(1, 'STEP', 'SwitchBotアプリでリモコンを登録し、Alexaアプリでスキル連携。', 'POSITIVE', 6),
(1, 'STEP', '「アレクサ、テレビつけて！」などで音声操作が可能になる。', 'POSITIVE', 7);

/* お金・投資 (story_id = 2) */
INSERT INTO M_Experience_Details (story_id, fact_type, fact_text, experience_flag, sort_order) VALUES
(2, 'WHY', 'NISA/DCの税制優遇を活用し、手数料最安のS&P500で世界経済の成長に乗るのが合理的。', 'POSITIVE', 1),
(2, 'FAILURE', '過去、個別株で一喜一憂したが、インデックス投資の「何もしない」運用が最も効率的と気づいた。', 'NEGATIVE', 2),
(2, 'STEP', '「楽天銀行」「楽天証券」「楽天カード」を同時に申し込む。', 'POSITIVE', 3),
(2, 'STEP', '楽天カード決済で「eMAXIS Slim 米国株式(S&P500)」をNISA枠で満額積み立てる設定。', 'POSITIVE', 4),
(2, 'STEP', 'マネーフォワードで資産全体を可視化し、あとは基本的に放置する。', 'POSITIVE', 5);

/* キャリア (story_id = 3) */
INSERT INTO M_Experience_Details (story_id, fact_type, fact_text, experience_flag, sort_order) VALUES
(3, 'WHY', 'PMのコア業務は「管理」ではなく、「ブラックボックスの可視化（WBS化）」と「完遂」。', 'POSITIVE', 1),
(3, 'FAILURE', 'SE時代に顧客要望を言語化（「こういうことっすか？」）し続けた経験がPMスキルの土台になった。', 'NEGATIVE', 2),
(3, 'STEP', '『プロジェクトマネジメントの基本がぜんぶわかる本』等の薄い基本書を1冊読む。', 'POSITIVE', 3),
(3, 'STEP', '現業務を「WBS（誰が・いつまでに・何を）」に分解する癖をつける。', 'POSITIVE', 4);

/* 恋愛 (story_id = 4) */
INSERT INTO M_Experience_Details (story_id, fact_type, fact_text, experience_flag, sort_order) VALUES
(4, 'WHY', '通常のマッチングアプリは「アポ取り」の時間が非効率。', 'POSITIVE', 1),
(4, 'WHY', 'バチェラーデートは「アポ取り」を完全自動化できるため、時間が最短。', 'POSITIVE', 2),
(4, 'STEP', 'バチェラーデートに登録し、AIのアポ組を待つ。', 'POSITIVE', 3),
(4, 'PRO_TIP', '会計は必ず奢る（信頼への投資）。', 'POSITIVE', 4),
(4, 'PRO_TIP', 'デート後にLINE交換を打診する。', 'POSITIVE', 5);

/* 美容 (story_id = 5) */
INSERT INTO M_Experience_Details (story_id, fact_type, fact_text, experience_flag, sort_order) VALUES
(5, 'WHY', '多段階のスキンケアは「めんどくさい」。重要なのは「保湿」と「強力な成分」のみ。', 'POSITIVE', 1),
(5, 'FAILURE', '様々なスキンケアを試したが、シンプルな形に落ち着いた。', 'NEGATIVE', 2),
(5, 'STEP', '日常ケア：安い大容量パック＋「いい美容液」（例: オバジC25）＋ニベア青缶（フタ）。', 'POSITIVE', 3),
(5, 'PRO_TIP', '髭脱毛（ヤグレーザー推奨、8回程度で効果実感）。', 'POSITIVE', 4);

/* ファッション (story_id = 6) */
INSERT INTO M_Experience_Details (story_id, fact_type, fact_text, experience_flag, sort_order) VALUES
(6, 'WHY', '毎日の服選びは「意思決定コスト」の無駄。', 'POSITIVE', 1),
(6, 'STEP', '仕事着：ノンアイロンジャージシャツ（白）と黒スラックスで固定化。アイロン不要、選択不要。', 'POSITIVE', 2),
(6, 'STEP', '私服：GUや街中でトレンドを把握し、Sheinの人気ランキング上位を安価に購入。', 'POSITIVE', 3),
(6, 'PRO_TIP', '失敗しても安価なため、金銭的・精神的リスクが低い。', 'POSITIVE', 4);
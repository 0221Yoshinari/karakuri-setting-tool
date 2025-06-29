import streamlit as st
import pandas as pd
import numpy as np

# --- ページ設定とデザイン ---
st.set_page_config(layout="wide", page_title="スマスロ からくりサーカス 設定判別ツール")

# 背景画像のCSS (GitHubに画像を配置した場合のパスを想定)
# **必ず YOUR_GITHUB_USERNAME と YOUR_REPO_NAME をあなたのものに置き換えてください**
background_image_css = """
<style>
/* 基本的なHTML/Bodyスタイルをリセットし、オーバーフローをstAppに任せる */
html, body {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%; /* 高さを100%に設定 */
    overflow: hidden; /* body自体のスクロールは禁止し、stAppがスクロールを制御 */
}

/* Streamlitアプリ全体のコンテナ */
.stApp {
    background-image: url("https://raw.githubusercontent.com/0221Yoshinari/karakuri-setting-tool/main/images/karakuri_bg.png"); /* ここをあなたのGitHubリポジトリ内の画像パスに修正 */
    background-size: cover; /* 画面全体を覆う */
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed; /* 背景は固定のまま、スクロールしても常に画像が見える */
    min-height: 100vh; /* アプリ全体の最小高さをビューポートの高さに合わせる */
    height: 100%; /* stAppの高さを親要素（body）に合わせる */
    overflow-y: auto; /* ★stAppコンテナ自体が縦方向にスクロールできるように設定★ */
    position: relative; /* z-indexのために必要 */
    display: flex;
    flex-direction: column; /* 子要素を縦に並べる */
}

/* 背景画像の上に重ねるオーバーレイ */
.stApp::before {
    content: "";
    position: fixed; /* オーバーレイも固定 */
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.15); /* 透明度を0.3に変更 (画像が50%程度薄く見えるように) */
    z-index: 1;
    pointer-events: none; /* ★★★ここを追加：オーバーレイがクリックやスクロールをブロックしないようにする★★★ */
}

/* メインコンテンツブロック（入力項目などがある部分） */
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    z-index: 2; /* コンテンツが背景画像より手前に来るように */
    position: relative; /* z-indexのために必要 */
    background-color: rgba(0, 0, 0, 0.7); /* コンテンツエリアの背景色を半透明に */
    border-radius: 10px;
    padding: 30px;
    flex-grow: 1; /* コンテンツブロックが利用可能なスペースを埋めるように成長 */
}

/* その他のスタイル調整（色など） */
h1, h2, h3, h4, h5, h6, p, label, .st-ck, .st-bj, .st-bq {
    color: white !important;
}
.stSelectbox div[data-baseweb="select"] {
    background-color: #333 !important;
    color: white !important;
}
.stSelectbox div[data-baseweb="select"] div[data-testid="stSelectboxDropdown"] {
    background-color: #333 !important;
    color: white !important;
}
.stTextInput > div > div > input {
    background-color: #333 !important;
    color: white !important;
}
.stButton>button {
    background-color: #D35400; /* ボタンの背景色 */
    color: white; /* ボタンの文字色 */
    border-radius: 5px;
    border: none;
    padding: 10px 20px;
}
.stButton>button:hover {
    background-color: #E67E22;
}
.css-1r6dm7f { /* markdown text color */
    color: white;
}
</style>
"""
st.markdown(background_image_css, unsafe_allow_html=True)

# ヘッダー
st.title("スマスロ からくりサーカス 設定判別ツール")
st.markdown("---")

# --- 設定示唆の基準値 (私の裁量で設定。実際の解析値と異なる場合があります) ---
# 各設定の基礎スコア（初期値）
# 設定Lは考慮しない
initial_setting_scores = {
    '設定1': 100, '設定2': 110, '設定4': 150, '設定5': 180, '設定6': 200
}

# CZ当選ゲーム数による設定スコア調整（目安）
# 低ゲーム数CZが多いほど高設定に加点、高ゲーム数CZは低設定に加点/高設定に減点
cz_point_score_adjust = {
    'low_point_bonus_high': {'設定4': 5, '設定5': 10, '設定6': 15}, # 100G以内CZ頻度が高い場合
    'over_1000_penalty': {'設定6': -100, '設定5': -50, '設定4': -20} # 1000pt超えCZが出現した場合
}

# テーブル選択率（画像情報に基づく）
table_rates = {
    '設定1': {'テーブル1': 0.49, 'テーブル2': 0.45, 'テーブル3': 0.04, 'テーブル4': 0.02},
    '設定2': {'テーブル1': 0.37, 'テーブル2': 0.54, 'テーブル3': 0.03, 'テーブル4': 0.06},
    '設定4': {'テーブル1': 0.36, 'テーブル2': 0.52, 'テーブル3': 0.04, 'テーブル4': 0.08},
    '設定5': {'テーブル1': 0.52, 'テーブル2': 0.36, 'テーブル3': 0.08, 'テーブル4': 0.04},
    '設定6': {'テーブル1': 0.42, 'テーブル2': 0.42, 'テーブル3': 0.08, 'テーブル4': 0.08},
}
# テーブル示唆の重み（各設定にどれだけ影響するか）
table_score_weights = {
    'テーブル1': {'設定1': 10, '設定2': 0, '設定4': -5, '設定5': 5, '設定6': -5}, # 奇数示唆
    'テーブル2': {'設定1': 0, '設定2': 10, '設定4': 5, '設定5': -5, '設定6': 0},  # 偶数示唆
    'テーブル3': {'設定1': -20, '設定2': -10, '設定4': 10, '設定5': 20, '設定6': 10}, # 奇数高設定示唆
    'テーブル4': {'設定1': -20, '設定2': 10, '設定4': 20, '設定5': 10, '設定6': 20}  # 偶数高設定示唆
}

# AT終了画面のスコア（画像情報に基づく）
at_end_screen_options_display = {
    'フランシーヌ': '設定6濃厚',
    'しろがね＆勝＆鳴海': '設定4以上濃厚',
    'ギイ＋阿紫花': '設定2以上濃厚',
    '女キャラ5人': '偶数設定示唆',
    '敵キャラ5人': '奇数設定示唆',
    '勝＋鳴海': 'デフォルト', # デフォルト画面
    # 以下は画像からの追加画面
    '奇数の高設定示唆画面': '奇数の高設定示唆',
    '偶数の高設定示唆画面': '偶数の高設定示唆',
    '設定2以上確定画面': '設定2以上確定',
    '設定456確定画面': '設定456確定',
}
at_end_screen_scores = {
    'フランシーヌ':           {'設定1': -100, '設定2': -100, '設定4': -100, '設定5': -100, '設定6': 500}, # 設定6濃厚
    'しろがね＆勝＆鳴海':     {'設定1': -100, '設定2': -100, '設定4': 100, '設定5': 100, '設定6': 100},  # 設定4以上濃厚
    'ギイ＋阿紫花':           {'設定1': -50,  '設定2': 50,   '設定4': 50,   '設定5': 50,   '設定6': 50},   # 設定2以上濃厚
    '女キャラ5人':            {'設定1': -10,  '設定2': 20,   '設定4': 10,   '設定5': -10,  '設定6': 0},    # 偶数設定示唆
    '敵キャラ5人':            {'設定1': 20,   '設定2': -10,  '設定4': -10,  '設定5': 10,   '設定6': 0},    # 奇数設定示唆
    '勝＋鳴海':               {'設定1': 0,    '設定2': 0,    '設定4': 0,    '設定5': 0,    '設定6': 0},    # デフォルト
    '奇数の高設定示唆画面':   {'設定1': -50,  '設定2': -20,  '設定4': 20,   '設定5': 50,   '設定6': 20},   # 奇数の高設定示唆
    '偶数の高設定示唆画面':   {'設定1': -50,  '設定2': 20,   '設定4': 50,   '設定5': 20,   '設定6': 50},   # 偶数の高設定示唆
    '設定2以上確定画面':      {'設定1': -100, '設定2': 100,  '設定4': 100,  '設定5': 100,  '設定6': 100},  # 設定2以上確定
    '設定456確定画面':        {'設定1': -100, '設定2': -100, '設定4': 150,  '設定5': 150,  '設定6': 150},  # 設定456確定
}

# 踊れ！オリンピア上乗せスコア
olympia_addon_scores = {
    '+6 (設定6濃厚)': {'設定1': -100, '設定2': -100, '設定4': -100, '設定5': -100, '設定6': 300},
    '+4 (設定4以上濃厚)': {'設定1': -50, '設定2': -50, '設定4': 100, '設定5': 100, '設定6': 100},
    '+20 (設定2以上濃厚)': {'設定1': -20, '設定2': 50, '設定4': 50, '設定5': 50, '設定6': 50}
}

# エンディングランプスコア
ending_lamp_scores = {
    '虹色 (設定6濃厚)': {'設定1': -1000, '設定2': -1000, '設定4': -1000, '設定5': -1000, '設定6': 1000} # 非常に強い示唆
}

# 運命の一撃スコア（ユーザー情報に基づき重み付け）
unmei_success_score = {
    '初回_自力成功_高設定': 100, # レア役なし・最終ゲーム小役なし成功
    '継続_自力成功_設定6_期待': 50, # 80%以上
    '継続_自力成功_設定4_期待': 30, # 60%以上
    '継続_自力失敗_低設定_示唆': -30 # 低い成功率
}

# AT直撃スコア
at_direct_hit_score_per_hit = {'設定4': 50, '設定5': 70, '設定6': 100} # 1回あたりの加点

# --- A. からくりサーカス台自体の挙動に関する入力 ---
st.header("A. 台の挙動に関する入力")

col1, col2 = st.columns(2)
with col1:
    total_games = st.number_input("1. 総ゲーム数", min_value=0, value=0, step=100)
with col2:
    at_first_hit = st.number_input("2. AT初当たり回数", min_value=0, value=0)

# CZ当選履歴
st.subheader("3. CZ当選時のゲーム数 (複数入力可)")
st.info("💡 液晶のポイント数で入力してください。1000pt超えのCZ当選は設定6期待度を大きく下げます。")
if 'cz_data' not in st.session_state:
    st.session_state.cz_data = []

def add_cz_entry():
    st.session_state.cz_data.append({'point': '', 'from_karakuri_rareyaku': False})

def remove_cz_entry(index):
    st.session_state.cz_data.pop(index)

st.button("CZ当選履歴を追加", on_click=add_cz_entry)

for i, cz_entry in enumerate(st.session_state.cz_data):
    cz_cols = st.columns([0.4, 0.4, 0.2])
    with cz_cols[0]:
        st.session_state.cz_data[i]['point'] = st.number_input(f"CZ {i+1}回目: 当選ポイント", min_value=0, value=cz_entry['point'] if cz_entry['point'] != '' else 0, key=f"cz_point_{i}")
    with cz_cols[1]:
        st.session_state.cz_data[i]['from_karakuri_rareyaku'] = st.checkbox(f"からくりレア役契機？", value=cz_entry['from_karakuri_rareyaku'], key=f"cz_rareyaku_{i}")
    with cz_cols[2]:
        st.button("削除", key=f"remove_cz_{i}", on_click=remove_cz_entry, args=(i,))

# AT終了画面
st.subheader("4. AT終了画面")
# オプションリストを確実に取得するために、ここで明示的に辞書からリストを作成
end_screen_options_list = list(at_end_screen_options_display.keys()) 

selected_end_screens = st.multiselect(
    "出現したAT終了画面を全て選択してください",
    options=end_screen_options_list, # ★★★ ここを修正 ★★★
    default=[]
)
end_screen_counts = {}
for screen in selected_end_screens:
    end_screen_counts[screen] = st.number_input(f"{screen} の出現回数", min_value=0, value=0, key=f"end_screen_count_{screen}")

# AT中のテーブル選択 (ATごとに最大3回、複数AT回数分入力)
st.subheader("5. AT中のテーブル選択")
st.info("💡 各ATのテーブル（AT開始時、成功1回目、成功2回目）を選択してください。")
if 'at_tables' not in st.session_state:
    st.session_state.at_tables = []

def add_at_entry():
    st.session_state.at_tables.append({'start': '選択なし', 'success1': '選択なし', 'success2': '選択なし'})

def remove_at_entry(index):
    st.session_state.at_tables.pop(index)

st.button("AT回を追加", on_click=add_at_entry)
table_options = ['選択なし', 'テーブル1 (奇数示唆)', 'テーブル2 (偶数示唆)', 'テーブル3 (奇数高設定示唆)', 'テーブル4 (偶数高設定示唆)']

for i, at_table in enumerate(st.session_state.at_tables):
    st.markdown(f"**--- AT {i+1}回目 ---**")
    at_cols = st.columns([0.3, 0.3, 0.3, 0.1])
    with at_cols[0]:
        st.session_state.at_tables[i]['start'] = st.selectbox(f"AT{i+1}開始時", options=table_options, index=table_options.index(at_table['start']), key=f"at{i}_start")
    with at_cols[1]:
        st.session_state.at_tables[i]['success1'] = st.selectbox(f"AT{i+1}成功1回目", options=table_options, index=table_options.index(at_table['success1']), key=f"at{i}_success1")
    with at_cols[2]:
        st.session_state.at_tables[i]['success2'] = st.selectbox(f"AT{i+1}成功2回目", options=table_options, index=table_options.index(at_table['success2']), key=f"at{i}_success2")
    with at_cols[3]:
        st.button("削除", key=f"remove_at_{i}", on_click=remove_at_entry, args=(i,))

# 踊れ！オリンピア中の上乗せ数字
st.subheader("6. 踊れ！オリンピア中の上乗せ数字")
olympia_addon = st.selectbox(
    "最も強い示唆の上乗せ数字を選択してください",
    options=['選択なし', '+6 (設定6濃厚)', '+4 (設定4以上濃厚)', '+20 (設定2以上濃厚)', 'その他']
)

# エンディング中のレア役時、筐体上部ランプ色
st.subheader("7. エンディング中のレア役時ランプ色")
ending_lamp = st.selectbox(
    "エンディング中のレア役時、筐体上部ランプ色は？",
    options=['選択なし', '虹色 (設定6濃厚)', 'その他']
)

# 運命の一撃の成功状況 (複数回入力)
st.subheader("8. 運命の一撃の成功状況")
st.info("💡 「レア役なし」かつ「最終ゲーム小役なし」での成功は強力な高設定示唆です。")

if 'unmei_first' not in st.session_state:
    st.session_state.unmei_first = []
if 'unmei_continue' not in st.session_state:
    st.session_state.unmei_continue = []

def add_unmei_first():
    if len(st.session_state.unmei_first) < 10: # 最大10回
        st.session_state.unmei_first.append({'success': '選択なし', 'trigger': '選択なし'})
    else:
        st.warning("最初の運命の一撃の最大入力回数に達しました。")

def remove_unmei_first(index):
    st.session_state.unmei_first.pop(index)

def add_unmei_continue():
    if len(st.session_state.unmei_continue) < 15: # 最大15回
        st.session_state.unmei_continue.append({'success': '選択なし', 'trigger': '選択なし'})
    else:
        st.warning("継続をかけた運命の一撃の最大入力回数に達しました。")

def remove_unmei_continue(index):
    st.session_state.unmei_continue.pop(index)

unmei_options = ['選択なし', '成功', '失敗']
trigger_options = ['選択なし', '強レア役', '弱レア役', '最終ゲーム小役', 'レア役なし・最終ゲーム小役なし']

st.markdown("**最初の運命の一撃 (最大10回)**")
st.button("最初の運命の一撃を追加", on_click=add_unmei_first)
for i, entry in enumerate(st.session_state.unmei_first):
    cols = st.columns([0.4, 0.4, 0.2])
    with cols[0]:
        st.session_state.unmei_first[i]['success'] = st.selectbox(f"初回運命 {i+1}回目: 結果", options=unmei_options, index=unmei_options.index(entry['success']), key=f"unmei_first_success_{i}")
    with cols[1]:
        # ★★★ここが変更点★★：ValueError回避 & 正しいoptions変数を指定
        current_trigger_index = trigger_options.index(entry['trigger']) if entry['trigger'] in trigger_options else 0
        st.session_state.unmei_first[i]['trigger'] = st.selectbox(f"初回運命 {i+1}回目: 契機", options=trigger_options, index=current_trigger_index, key=f"unmei_first_trigger_{i}")
    with cols[2]:
        st.button("削除", key=f"remove_unmei_first_{i}", on_click=remove_unmei_first, args=(i,))

st.markdown("**継続をかけた運命の一撃 (最大15回)**")
st.button("継続運命の一撃を追加", on_click=add_unmei_continue) # ★★★ここが変更点★★：on_on_clickをon_clickに修正
for i, entry in enumerate(st.session_state.unmei_continue):
    cols = st.columns([0.4, 0.4, 0.2])
    with cols[0]:
        st.session_state.unmei_continue[i]['success'] = st.selectbox(f"継続運命 {i+1}回目: 結果", options=unmei_options, index=unmei_options.index(entry['success']), key=f"unmei_continue_success_{i}")
    with cols[1]:
        # ★★★ここが変更点★★：ValueError回避 & 正しいoptions変数を指定
        current_trigger_index = trigger_options.index(entry['trigger']) if entry['trigger'] in trigger_options else 0
        st.session_state.unmei_continue[i]['trigger'] = st.selectbox(f"継続運命 {i+1}回目: 契機", options=trigger_options, index=current_trigger_index, key=f"unmei_continue_trigger_{i}")
    with cols[2]:
        st.button("削除", key=f"remove_unmei_continue_{i}", on_click=remove_unmei_continue, args=(i,))

# AT直撃
st.subheader("9. AT直撃")
at_direct_hit_count = st.number_input("AT直撃回数", min_value=0, value=0)
if at_direct_hit_count > 0:
    st.info("💡 AT直撃は低設定では稀な強力な高設定示唆です。")

# --- B. 店舗・外部要因に関する入力 (任意入力) ---
st.header("B. 店舗・外部要因に関する入力 (任意)")
st.info("💡 こちらの項目は任意です。入力するとより実戦的な判断が可能です。")

# ホール全体のからくりサーカス設定投入傾向
st.subheader("1. ホール全体のからくりサーカス設定投入傾向")
hall_karakuri_tendency = st.radio(
    "当ホールはからくりサーカスに普段から設定を入れる傾向がありますか？",
    options=['選択しない', '高い', '普通', '低い'],
    index=0, horizontal=True
)

# からくりサーカスはホールの主力機種か
st.subheader("2. からくりサーカスはホールの主力機種か")
is_main_machine = st.radio(
    "からくりサーカスはホールの主力機種（高稼働・人気機種）ですか？",
    options=['選択しない', 'はい', 'いいえ'],
    index=0, horizontal=True
)

# 遊技日は特定イベント日か
st.subheader("3. 遊技日は特定イベント日か")
event_day_type = st.radio(
    "本日は特定イベント日ですか？",
    options=['選択しない', '強いイベント日 (例: 周年、全台系示唆)', '弱いイベント日 (例: 特定機種示唆)', 'イベントなし'],
    index=0, horizontal=True
)

# からくりサーカス関連の取材・広告の有無
st.subheader("4. からくりサーカス関連の取材・広告の有無")
karakuri_coverage = st.radio(
    "からくりサーカス関連の取材や広告は入っていますか？",
    options=['選択しない', 'ある', 'ない'],
    index=0, horizontal=True
)

# 高設定投入示唆系の取材・広告の有無
st.subheader("5. 高設定投入示唆系の取材・広告の有無")
high_setting_coverage = st.radio(
    "ホール全体で高設定投入を示唆する取材や広告は入っていますか？",
    options=['選択しない', 'ある', 'ない'],
    index=0, horizontal=True
)

# 遊技日は通常の営業日か
st.subheader("6. 遊技日は通常の営業日か")
is_normal_day = st.radio(
    "本日は通常の営業日ですか？ (イベント日などを考慮)",
    options=['選択しない', 'はい', 'いいえ'],
    index=0, horizontal=True
)

# からくりサーカス得意演者の来店有無
st.subheader("7. からくりサーカス得意演者の来店有無")
performer_presence = st.radio(
    "からくりサーカスを得意とする来店演者はいますか？",
    options=['選択しない', 'いる', 'いない'],
    index=0, horizontal=True
)

# 過去に当ホールでからくりサーカス設定6確定経験の有無
st.subheader("8. 過去に当ホールでからくりサーカス設定6確定経験の有無")
seen_setting6_in_hall = st.radio(
    "当ホールで過去にからくりサーカスの設定6確定画面を見たことがありますか？",
    options=['選択しない', 'ある', 'ない'],
    index=0, horizontal=True
)

# 当ホールの設定6使用傾向
st.subheader("9. 当ホールの設定6使用傾向")
hall_setting6_tendency = st.radio(
    "当ホールは普段から設定6を使う傾向がありますか？",
    options=['選択しない', '高い', '普通', '低い'],
    index=0, horizontal=True
)

# 他の台の状況 (自由記述)
st.subheader("10. 他の台の状況")
other_machine_status = st.text_area(
    "周囲の台（同じ機種や他の機種）の状況を簡潔に入力してください。"
)

# --- 判別実行ボタン ---
st.markdown("---")
if st.button("設定を判別する", key="run_analysis"):
    st.subheader("### 判別結果")
    st.write("---")

    # 各設定の可能性スコアを初期化
    setting_likelihood_scores = initial_setting_scores.copy()

    # --- A. 台の挙動に関する評価 ---

    # AT初当たり確率
    if total_games > 0 and at_first_hit > 0:
        at_first_hit_rate = total_games / at_first_hit
        st.write(f"**AT初当たり確率: 1/{at_first_hit_rate:.2f}**")
        # 仮の目安で各設定にスコア加算/減算
        if at_first_hit_rate < 300: # 高設定寄り
            setting_likelihood_scores['設定4'] += 10
            setting_likelihood_scores['設定5'] += 20
            setting_likelihood_scores['設定6'] += 30
            setting_likelihood_scores['設定1'] -= 10
            setting_likelihood_scores['設定2'] -= 5
        elif at_first_hit_rate > 400: # 低設定寄り
            setting_likelihood_scores['設定1'] += 20
            setting_likelihood_scores['設定2'] += 10
            setting_likelihood_scores['設定4'] -= 10
            setting_likelihood_scores['設定5'] -= 20
            setting_likelihood_scores['設定6'] -= 30
    else:
        st.write("**AT初当たり情報は入力されていません。**")


    # CZ当選履歴とポイント
    cz_success_points = [entry['point'] for entry in st.session_state.cz_data if entry['point'] is not None and entry['point'] > 0]
    karakuri_cz_count = sum(1 for entry in st.session_state.cz_data if entry['from_karakuri_rareyaku'])

    if cz_success_points:
        st.write(f"**CZ当選履歴:** {cz_success_points} ポイント")
        total_cz_count = len(cz_success_points)
        low_cz_count = sum(1 for p in cz_success_points if p <= 100) # 100G以内を早いとする目安
        over_1000_cz_count = sum(1 for p in cz_success_points if p >= 1000)

        if total_cz_count > 0 and low_cz_count / total_cz_count >= 0.3: # 30%以上が低ポイントCZ
            st.write("→ 低ゲーム数でのCZ当選が頻繁に確認されました。")
            for s in ['設定4', '設定5', '設定6']:
                setting_likelihood_scores[s] += cz_point_score_adjust['low_point_bonus_high'].get(s, 0)
            for s in ['設定1', '設定2']:
                setting_likelihood_scores[s] -= 5 # 低設定は低ゲーム数CZが少ない

        if over_1000_cz_count > 0:
            st.warning(f"**1000ポイント超えのCZ当選 ({over_1000_cz_count}回) が確認されました。**")
            for s, penalty in cz_point_score_adjust['over_1000_penalty'].items():
                setting_likelihood_scores[s] += penalty * over_1000_cz_count # 複数回出たらさらに減点
            # 確定要素として、もし1000pt超えが複数回あれば設定6の可能性をほぼ0に
            if over_1000_cz_count >= 2:
                 setting_likelihood_scores['設定6'] = max(0, setting_likelihood_scores['設定6'] - 500) # 強力な減点


        if karakuri_cz_count > 0 and total_games > 0:
            karakuri_cz_rate = total_games / karakuri_cz_count
            st.write(f"**からくりレア役契機CZ確率: 1/{karakuri_cz_rate:.2f} ({karakuri_cz_count}回)**")
            if karakuri_cz_rate < 500: # 高設定目安
                setting_likelihood_scores['設定4'] += 10
                setting_likelihood_scores['設定5'] += 15
                setting_likelihood_scores['設定6'] += 20
                setting_likelihood_scores['設定1'] -= 5
            elif karakuri_cz_rate > 1000: # 低設定目安
                setting_likelihood_scores['設定1'] += 10
                setting_likelihood_scores['設定2'] += 5
                setting_likelihood_scores['設定4'] -= 5
                setting_likelihood_scores['設定5'] -= 10
                setting_likelihood_scores['設定6'] -= 15
    else:
        st.write("**CZ当選履歴は入力されていません。**")

    # AT終了画面
    strong_fixed_setting = None # 確定示唆を追跡
    if selected_end_screens:
        st.write("**AT終了画面:**")
        for screen, count in end_screen_counts.items():
            if count > 0:
                indication_text = at_end_screen_options_display.get(screen, '特定示唆なし')
                st.write(f"- {screen} ({count}回出現) → **{indication_text}**")
                
                # スコア加算
                for s in setting_likelihood_scores.keys():
                    if screen in at_end_screen_scores and s in at_end_screen_scores[screen]:
                        setting_likelihood_scores[s] += at_end_screen_scores[screen][s] * count

                # 確定示唆の処理 (ここが最重要)
                if "設定6濃厚" in indication_text:
                    strong_fixed_setting = '設定6'
                elif "設定4以上濃厚" in indication_text or "設定456確定" in indication_text:
                    if not strong_fixed_setting or strong_fixed_setting == '設定2以上': # より強い示唆がない場合のみ上書き
                        strong_fixed_setting = '設定4以上'
                elif "設定2以上確定" in indication_text:
                    if not strong_fixed_setting: # より強い示唆がない場合のみ上書き
                        strong_fixed_setting = '設定2以上'
    else:
        st.write("**AT終了画面は入力されていません。**")


    # AT中のテーブル選択
    if st.session_state.at_tables:
        st.write("**AT中のテーブル選択履歴:**")
        for i, at_table in enumerate(st.session_state.at_tables):
            st.write(f"AT {i+1}回目:")
            selected_tables_base = [] # 'テーブルX'だけの名前
            if at_table['start'] != '選択なし': selected_tables_base.append(at_table['start'].split(' ')[0])
            if at_table['success1'] != '選択なし': selected_tables_base.append(at_table['success1'].split(' ')[0])
            if at_table['success2'] != '選択なし': selected_tables_base.append(at_table['success2'].split(' ')[0])

            if selected_tables_base:
                st.write(f"- 選択されたテーブル: {', '.join([t + ' (' + table_indications[t] + ')' for t in selected_tables_base])}")
                for table_name in selected_tables_base:
                    for s in setting_likelihood_scores.keys():
                        setting_likelihood_scores[s] += table_score_weights.get(table_name, {}).get(s, 0)
            else:
                st.write("- (入力なし)")

    # 踊れ！オリンピア中の上乗せ数字
    if olympia_addon != '選択なし' and olympia_addon != 'その他':
        st.write(f"**踊れ！オリンピア中の上乗せ数字: {olympia_addon}**")
        for s in setting_likelihood_scores.keys():
            if olympia_addon in olympia_addon_scores and s in olympia_addon_scores[olympia_addon]:
                setting_likelihood_scores[s] += olympia_addon_scores[olympia_addon][s]
        
        # 確定示唆の処理
        if '+6' in olympia_addon:
            strong_fixed_setting = '設定6'
        elif '+4' in olympia_addon:
            if not strong_fixed_setting or strong_fixed_setting == '設定2以上':
                strong_fixed_setting = '設定4以上'
        elif '+20' in olympia_addon:
            if not strong_fixed_setting: # より強い示唆がない場合のみ上書き
                strong_fixed_setting = '設定2以上'
    else:
        st.write("**踊れ！オリンピア上乗せ数字は入力されていません。**")


    # エンディング中のレア役時、筐体上部ランプ色
    if ending_lamp == '虹色 (設定6濃厚)':
        st.write("**エンディング中ランプ色: 虹色 (設定6濃厚)**")
        for s in setting_likelihood_scores.keys():
            setting_likelihood_scores[s] += ending_lamp_scores['虹色 (設定6濃厚)'].get(s, 0)
        strong_fixed_setting = '設定6' # 虹色は最も強い確定

    # 運命の一撃の成功状況
    st.write("**運命の一撃 成功状況:**")
    total_first_unmei_eval = 0
    successful_first_unmei_no_forced = 0
    for entry in st.session_state.unmei_first:
        if entry['success'] != '選択なし': # 成功・失敗どちらでも試行回数にカウント
            total_first_unmei_eval += 1
            if entry['success'] == '成功' and entry['trigger'] == 'レア役なし・最終ゲーム小役なし':
                successful_first_unmei_no_forced += 1
                for s in setting_likelihood_scores.keys():
                    setting_likelihood_scores[s] += unmei_success_score['初回_自力成功_高設定'] # 強力な加点

    if total_first_unmei_eval > 0:
        st.write(f"- 最初の運命の一撃（自力成功）: {successful_first_unmei_no_forced}回 / {total_first_unmei_eval}回")

    total_continue_unmei_eval = 0
    successful_continue_unmei_no_forced = 0
    for entry in st.session_state.unmei_continue:
        if entry['success'] != '選択なし': # 成功・失敗どちらでも試行回数にカウント
            total_continue_unmei_eval += 1
            if entry['success'] == '成功' and entry['trigger'] not in ['強レア役', '最終ゲーム小役']: # 強制成功を除外
                successful_continue_unmei_no_forced += 1

    if total_continue_unmei_eval > 0:
        continue_unmei_rate = successful_continue_unmei_no_forced / total_continue_unmei_eval
        st.write(f"- 継続運命の一撃（自力成功）: {continue_unmei_rate:.2%} ({successful_continue_unmei_no_forced}回 / {total_continue_unmei_eval}回)")
        
        # 成功率に応じてスコア加算
        if continue_unmei_rate >= unmei_success_rates['継続運命の一撃_設定6_自力']: # 80%
            setting_likelihood_scores['設定6'] += unmei_success_score['継続_自力成功_設定6_期待']
            setting_likelihood_scores['設定5'] += unmei_success_score['継続_自力成功_設定4_期待'] # 5も恩恵あり
        elif continue_unmei_rate >= unmei_success_rates['継続運命の一撃_設定4_自力']: # 60%
            setting_likelihood_scores['設定4'] += unmei_success_score['継続_自力成功_設定4_期待']
            setting_likelihood_scores['設定5'] += unmei_success_score['継続_自力成功_設定4_期待']
        elif continue_unmei_rate < unmei_success_rates['継続_自力失敗_低設定_示唆'] and successful_continue_unmei_no_forced == 0: # 低い成功率かつ自力成功が0ならさらに減点
            for s in ['設定1', '設定2']:
                setting_likelihood_scores[s] += abs(unmei_success_score['継続_自力失敗_低設定_示唆']) # 低設定側に加点
            for s in ['設定4', '設定5', '設定6']:
                setting_likelihood_scores[s] += unmei_success_score['継続_自力失敗_低設定_示唆'] # 高設定側から減点
    else:
        st.write("運命の一撃は入力されていません。")

    # AT直撃
    if at_direct_hit_count > 0:
        st.write(f"**AT直撃回数: {at_direct_hit_count}回**")
        for s in ['設定4', '設定5', '設定6']:
            setting_likelihood_scores[s] += at_direct_hit_score_per_hit.get(s, 0) * at_direct_hit_count # 直撃回数に応じて加点
        # 直撃回数が多ければ高設定示唆を強化
        if at_direct_hit_count >= 2:
            if not strong_fixed_setting: # 他のより強い示唆がない場合のみ
                 strong_fixed_setting = '設定4以上'


    # --- B. 店舗・外部要因に関する評価 (スコアリング) ---
    st.markdown("---")
    st.subheader("### 店舗・外部要因からの評価")
    
    external_score_multiplier = 0 # 外部要因の総合的な影響度

    external_score_map = {
        'hall_karakuri_tendency': {'高い': 0.10, '普通': 0, '低い': -0.10, '選択しない': 0}, # 倍率として影響
        'is_main_machine': {'はい': 0.05, 'いいえ': 0, '選択しない': 0},
        'event_day_type': {'強いイベント日 (例: 周年、全台系示唆)': 0.20, '弱いイベント日 (例: 特定機種示唆)': 0.10, 'イベントなし': -0.05, '選択しない': 0},
        'karakuri_coverage': {'ある': 0.05, 'ない': 0, '選択しない': 0},
        'high_setting_coverage': {'ある': 0.15, 'ない': 0, '選択しない': 0},
        'performer_presence': {'いる': 0.10, 'いない': 0, '選択しない': 0},
        'seen_setting6_in_hall': {'ある': 0.25, 'ない': -0.10, '選択しない': 0}, # 過去の実績は非常に重要
        'hall_setting6_tendency': {'高い': 0.15, '普通': 0, '低い': -0.15, '選択しない': 0},
    }

    # 各外部要因の倍率を計算
    external_score_multiplier += external_score_map['hall_karakuri_tendency'].get(hall_karakuri_tendency, 0)
    external_score_multiplier += external_score_map['is_main_machine'].get(is_main_machine, 0)
    external_score_multiplier += external_score_map['event_day_type'].get(event_day_type, 0)
    external_score_multiplier += external_score_map['karakuri_coverage'].get(karakuri_coverage, 0)
    external_score_multiplier += external_score_map['high_setting_coverage'].get(high_setting_coverage, 0)
    external_score_multiplier += external_score_map['performer_presence'].get(performer_presence, 0)
    external_score_multiplier += external_score_map['seen_setting6_in_hall'].get(seen_setting6_in_hall, 0)
    external_score_multiplier += external_score_map['hall_setting6_tendency'].get(hall_setting6_tendency, 0)

    # 各設定スコアに外部要因の倍率を適用（高設定に有利に働くように）
    # ただし、低設定への影響は小さくする
    for s in setting_likelihood_scores.keys():
        if s in ['設定4', '設定5', '設定6']:
            setting_likelihood_scores[s] *= (1 + external_score_multiplier)
        elif s in ['設定1', '設定2']:
            # 低設定は外部要因の影響を小さくするか、逆の影響を持たせる（例: 高設定期待が高い日は低設定の期待度が下がる）
            setting_likelihood_scores[s] *= (1 - external_score_multiplier * 0.5) # 高設定寄りなら低設定は少し下がる
        setting_likelihood_scores[s] = max(1, setting_likelihood_scores[s]) # スコアが0以下にならないように最低1を設定

    if other_machine_status:
        st.write(f"**その他の台の状況:** {other_machine_status}")


    # --- 総合判定（各設定の可能性と高設定期待度） ---
    st.markdown("---")
    st.subheader("### 総合判定")

    # 確定示唆によるフィルタリングとスコアの強制
    if strong_fixed_setting:
        st.success(f"**🎉 {strong_fixed_setting}確定レベルの強力な示唆が確認されました！ 🎉**")
        for s in list(setting_likelihood_scores.keys()):
            if strong_fixed_setting == '設定6':
                if s != '設定6': setting_likelihood_scores[s] = 0
            elif strong_fixed_setting == '設定4以上':
                if s in ['設定1', '設定2']: setting_likelihood_scores[s] = 0
            elif strong_fixed_setting == '設定2以上':
                if s == '設定1': setting_likelihood_scores[s] = 0
        
        # 確定示唆が出た場合のスコア調整（設定6を極端に高くする等）
        if strong_fixed_setting == '設定6':
            setting_likelihood_scores['設定6'] = 1000000 # 圧倒的に高く
            # 他の設定は0にする（既にされているが念のため）
            for s in setting_likelihood_scores:
                if s != '設定6':
                    setting_likelihood_scores[s] = 0.0001 # 完全に0だと割り算で問題が出るので微小な値
        elif strong_fixed_setting == '設定4以上':
            for s in ['設定4', '設定5', '設定6']: setting_likelihood_scores[s] = max(1000, setting_likelihood_scores[s] * 2)
        elif strong_fixed_setting == '設定2以上':
            for s in ['設定2', '設定4', '設定5', '設定6']: setting_likelihood_scores[s] = max(500, setting_likelihood_scores[s] * 1.5)

    # 全てのスコアが0の場合の処理 (微小な値を入れたので不要になる可能性あり)
    total_score_sum = sum(setting_likelihood_scores.values())
    if total_score_sum == 0 or total_score_sum < 0.01: # ほぼ0の場合も考慮
        st.info("現時点では判断できる材料が少ないか、相殺する要素が多いです。")
        st.write("各設定の可能性:")
        for s in setting_likelihood_scores.keys():
            st.write(f"- {s}: 0.00%")
        st.write("**高設定期待度: 0.00%**")
    else:
        # 各設定の可能性パーセンテージを計算
        st.write("**各設定の可能性 (私の裁量による目安):**")
        probabilities = {}
        for s, score in setting_likelihood_scores.items():
            prob = (score / total_score_sum) * 100
            probabilities[s] = prob
            st.write(f"- **{s}: {prob:.2f}%**")

        # 高設定期待度（設定4,5,6の合計）
        high_setting_prob = probabilities.get('設定4', 0) + probabilities.get('設定5', 0) + probabilities.get('設定6', 0)
        st.markdown(f"**### 高設定期待度: {high_setting_prob:.2f}%**")

        # 総合的なメッセージ
        if high_setting_prob >= 80:
            st.success("🎉 高設定（特に設定6）である可能性が非常に高いです！🎉")
        elif high_setting_prob >= 60:
            st.success("✨ 高設定である可能性が高いです！✨")
        elif high_setting_prob >= 40:
            st.warning("👍 中間設定以上、または高設定に期待できる要素があります。")
        else:
            st.error("👎 低設定である可能性が高いか、高設定を否定する要素が見られます。")

    st.markdown("---")
    st.write("**詳細な示唆内容:**")
    # ここに各示唆内容をまとめる処理を再追加
    final_indications = []
    # AT初当たり
    if total_games > 0 and at_first_hit > 0:
        at_first_hit_rate = total_games / at_first_hit
        if at_first_hit_rate < 300: final_indications.append("AT初当たりが良好。")
        elif at_first_hit_rate > 400: final_indications.append("AT初当たりが重め。")
    
    # CZ当選
    if cz_success_points:
        total_cz_count = len(cz_success_points)
        low_cz_count = sum(1 for p in cz_success_points if p <= 100)
        if total_cz_count > 0 and low_cz_count / total_cz_count >= 0.3: final_indications.append("低ゲーム数でのCZ当選が頻繁。")
        if over_1000_cz_count > 0: final_indications.append(f"1000pt超えCZ当選({over_1000_cz_count}回)あり。")
        if karakuri_cz_count > 0 and total_games > 0:
            karakuri_cz_rate = total_games / karakuri_cz_count
            if karakuri_cz_rate < 500: final_indications.append("からくりレア役契機CZ良好。")
            elif karakuri_cz_rate > 1000: final_indications.append("からくりレア役契機CZ低め。")

    # AT終了画面
    for screen, count in end_screen_counts.items():
        if count > 0:
            final_indications.append(f"AT終了画面「{screen}」({count}回)出現。")

    # AT中のテーブル
    for i, at_table in enumerate(st.session_state.at_tables):
        selected_tables_base = []
        if at_table['start'] != '選択なし': selected_tables_base.append(at_table['start'].split(' ')[0])
        if at_table['success1'] != '選択なし': selected_tables_base.append(at_table['success1'].split(' ')[0])
        if at_table['success2'] != '選択なし': selected_tables_base.append(at_table['success2'].split(' ')[0])
        for table_name in selected_tables_base:
            if table_name in ['テーブル3', 'テーブル4']:
                final_indications.append(f"AT中の{table_name}選択を確認。")
            
    # 踊れ！オリンピア
    if olympia_addon != '選択なし' and olympia_addon != 'その他': final_indications.append(f"踊れ！オリンピアで{olympia_addon}出現。")

    # エンディングランプ
    if ending_lamp == '虹色 (設定6濃厚)': final_indications.append("エンディングランプ虹色出現。")

    # 運命の一撃
    if successful_first_unmei_no_forced > 0: final_indications.append(f"初回運命の一撃で自力成功({successful_first_unmei_no_forced}回)確認。")
    if total_continue_unmei_eval > 0:
        if continue_unmei_rate >= unmei_success_rates['継続運命の一撃_設定6_自力']: final_indications.append("継続運命の一撃成功率が非常に高い。")
        elif continue_unmei_rate >= unmei_success_rates['継続運命の一撃_設定4_自力']: final_indications.append("継続運命の一撃成功率が高め。")
        elif continue_unmei_rate < unmei_success_rates['継続_自力失敗_低設定_示唆'] and successful_continue_unmei_no_forced == 0: final_indications.append("継続運命の一撃成功率が低め。")

    # AT直撃
    if at_direct_hit_count > 0: final_indications.append(f"AT直撃({at_direct_hit_count}回)確認。")

    # 外部要因
    if external_score_multiplier > 0.05: final_indications.append("店舗・外部要因で高設定期待度が増加。")
    elif external_score_multiplier < -0.05: final_indications.append("店舗・外部要因で高設定期待度が減少。")
    if other_machine_status: final_indications.append(f"その他の台の状況: {other_machine_status}")


    if final_indications:
        for ind in final_indications:
            st.write(f"- {ind}")
    else:
        st.write("現時点では特段の示唆はありません。")

    st.write("\n_※表示される数値は、提供された情報と私の裁量による重み付けに基づいた「可能性の目安」です。実際の統計的な確率ではありませんので、最終的な判断はご自身の責任で行ってください。_")
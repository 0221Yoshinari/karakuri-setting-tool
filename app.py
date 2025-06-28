import streamlit as st
import pandas as pd
import numpy as np

# --- ページ設定とデザイン ---
st.set_page_config(layout="wide", page_title="スマスロ からくりサーカス 設定判別ツール")

# 背景画像のCSS (GitHubに画像を配置した場合のパスを想定)
# 実際の画像パスはデプロイ後に適宜調整してください
background_image_css = """
<style>
.stApp {
    background-image: url("https://raw.githubusercontent.com/0221Yoshinari/karakuri-setting-tool/main/images/karakuri_bg.png");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
}
.stApp::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.6); /* 背景画像の視認性を高めるためのオーバーレイ */
    z-index: 1;
}
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    z-index: 2; /* コンテンツが背景画像より手前に来るように */
    position: relative;
    background-color: rgba(0, 0, 0, 0.7); /* コンテンツエリアの背景色を半透明に */
    border-radius: 10px;
    padding: 30px;
}
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

# --- 設定示唆の基準値 (実際の解析値に合わせて調整してください) ---
# CZ当選ゲーム数割合 (仮の数値、画像から読み取ったものと分析結果を元に調整)
# これはあくまで例で、実際の運用で調整が必要です
cz_game_dist_heaven = {1: 0.15, 51: 0.85} # 1-50G, 51-100G
cz_game_dist_normal_a_c = {101: 0.01, 201: 0.14, 301: 0.01, 401: 0.19, 501: 0.01, 601: 0.14, 701: 0.01, 801: 0.14, 901: 0.01, 1001: 0.22, 1101: 0.12}
cz_game_dist_normal_b = {101: 0.10, 201: 0.02, 301: 0.20, 401: 0.02, 501: 0.20, 601: 0.02, 701: 0.44}

# テーブル選択率 (画像から読み取り、簡略化して設定差を強調)
table_rates = {
    '設定1': {'テーブル1': 0.49, 'テーブル2': 0.45, 'テーブル3': 0.04, 'テーブル4': 0.02},
    '設定2': {'テーブル1': 0.37, 'テーブル2': 0.54, 'テーブル3': 0.03, 'テーブル4': 0.06},
    '設定4': {'テーブル1': 0.36, 'テーブル2': 0.52, 'テーブル3': 0.04, 'テーブル4': 0.08},
    '設定5': {'テーブル1': 0.52, 'テーブル2': 0.36, 'テーブル3': 0.08, 'テーブル4': 0.04},
    '設定6': {'テーブル1': 0.42, 'テーブル2': 0.42, 'テーブル3': 0.08, 'テーブル4': 0.08},
}

# テーブル示唆
table_indications = {
    'テーブル1': '奇数示唆 (鳴海→勝→鳴海)',
    'テーブル2': '偶数示唆 (勝→鳴海→勝)',
    'テーブル3': '奇数の高設定示唆 (鳴海→勝→勝)',
    'テーブル4': '偶数の高設定示唆 (勝→鳴海→鳴海)'
}

# AT終了画面の確率 (設定456確定台のデータと一般情報を元に仮定)
# ここも公式の正確な振り分けがあれば更新してください
at_end_screen_probs = {
    '設定1': {'デフォルト': 0.70, '奇数示唆': 0.10, '偶数示唆': 0.10, '設定2以上確定': 0.05, '設定456確定': 0.03, '設定6濃厚': 0.02},
    '設定456': {'デフォルト': 0.603, '奇数の高設定示唆': 0.064, '偶数の高設定示唆': 0.092, '設定2以上確定': 0.070, '設定456確定': 0.170, '設定6濃厚': 0.001}, # 設定6濃厚は非常に低いが0ではない
    '設定6': {'デフォルト': 0.50, '奇数の高設定示唆': 0.05, '偶数の高設定示唆': 0.07, '設定2以上確定': 0.05, '設定456確定': 0.20, '設定6濃厚': 0.13}, # 設定6濃厚の出現率を他より高くする
}
# AT終了画面の選択肢
at_end_screen_options = {
    'フランシーヌ': '設定6濃厚',
    'しろがね＆勝＆鳴海': '設定4以上濃厚',
    'ギイ＋阿紫花': '設定2以上濃厚',
    '女キャラ5人': '偶数設定示唆',
    '敵キャラ5人': '奇数設定示唆',
    '勝＋鳴海': 'デフォルト',
    '奇数の高設定示唆': '奇数の高設定示唆', # 新しく追加された画面
    '偶数の高設定示唆': '偶数の高設定示唆', # 新しく追加された画面
    '設定2以上確定画面': '設定2以上確定',
    '設定456確定画面': '設定456確定',
}

# 運命の一撃 成功率 (仮の数値、ユーザーからの情報に基づき)
# 強レア役は100%, 弱レア役は25%, 最終ゲーム子役で100%
# ここでは「レア役・子役なし」の自力成功率を想定
unmei_success_rates = {
    '最初の運命の一撃_自力_高設定': 0.10, # 数値は目安
    '継続運命の一撃_設定6_自力': 0.80,
    '継続運命の一撃_設定4_自力': 0.60,
    '継続運命の一撃_低設定_自力': 0.30, # 数値は目安
}

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
selected_end_screens = st.multiselect(
    "出現したAT終了画面を全て選択してください",
    options=list(at_end_screen_options.keys()),
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
    st.session_state.unmei_first.append({'success': '選択なし', 'trigger': '選択なし'})

def remove_unmei_first(index):
    st.session_state.unmei_first.pop(index)

def add_unmei_continue():
    st.session_state.unmei_continue.append({'success': '選択なし', 'trigger': '選択なし'})

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
        st.session_state.unmei_first[i]['trigger'] = st.selectbox(f"初回運命 {i+1}回目: 契機", options=trigger_options, index=trigger_options.index(entry['trigger']), key=f"unmei_first_trigger_{i}")
    with cols[2]:
        st.button("削除", key=f"remove_unmei_first_{i}", on_click=remove_unmei_first, args=(i,))

st.markdown("**継続をかけた運命の一撃 (最大15回)**")
st.button("継続運命の一撃を追加", on_click=add_unmei_continue)
for i, entry in enumerate(st.session_state.unmei_continue):
    cols = st.columns([0.4, 0.4, 0.2])
    with cols[0]:
        st.session_state.unmei_continue[i]['success'] = st.selectbox(f"継続運命 {i+1}回目: 結果", options=unmei_options, index=unmei_options.index(entry['success']), key=f"unmei_continue_success_{i}")
    with cols[1]:
        st.session_state.unmei_continue[i]['trigger'] = st.selectbox(f"継続運命 {i+1}回目: 契機", options=trigger_options, index=trigger_options.index(entry['trigger']), key=f"unmei_continue_trigger_{i}")
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

    # 初期スコアと示唆リスト
    overall_score = 0
    indications = []
    confidence_level = "低い" # 初期値

    # --- A. 台の挙動に関する評価 ---

    # AT初当たり確率
    if total_games > 0:
        at_first_hit_rate = total_games / at_first_hit if at_first_hit > 0 else float('inf')
        st.write(f"**AT初当たり確率: 1/{at_first_hit_rate:.2f}**")
        if at_first_hit_rate < 300: # 高設定目安 (仮)
            indications.append("AT初当たりが良好なため、高設定の可能性あり。")
            overall_score += 5
        elif at_first_hit_rate > 400: # 低設定目安 (仮)
            indications.append("AT初当たりが重いため、低設定の可能性あり。")
            overall_score -= 5
        else:
            indications.append("AT初当たりは中間設定域。")

    # CZ当選履歴とポイント
    cz_success_points = [entry['point'] for entry in st.session_state.cz_data if entry['point'] > 0]
    karakuri_cz_count = sum(1 for entry in st.session_state.cz_data if entry['from_karakuri_rareyaku'])

    if cz_success_points:
        st.write(f"**CZ当選履歴:** {cz_success_points} ポイント")
        low_cz_count = sum(1 for p in cz_success_points if p <= 100) # 100G以内を早いとする目安
        mid_cz_count = sum(1 for p in cz_success_points if 100 < p <= 500)
        high_cz_count = sum(1 for p in cz_success_points if 500 < p <= 999)
        over_1000_cz_count = sum(1 for p in cz_success_points if p >= 1000)

        if low_cz_count > len(cz_success_points) * 0.3: # 30%以上が低ポイントCZ
            indications.append("低ゲーム数でのCZ当選が頻繁に確認されました。天国モード移行率に期待。")
            overall_score += 4
        if over_1000_cz_count > 0:
            indications.append(f"**1000ポイント超えのCZ当選 ({over_1000_cz_count}回) が確認されました。設定6の可能性は大幅に低下します。**")
            overall_score -= (over_1000_cz_count * 10) # 1回で-10点など、強力な減点

        if karakuri_cz_count > 0 and total_games > 0:
            karakuri_cz_rate = total_games / karakuri_cz_count
            st.write(f"**からくりレア役契機CZ確率: 1/{karakuri_cz_rate:.2f} ({karakuri_cz_count}回)**")
            if karakuri_cz_rate < 500: # 目安
                indications.append("からくりレア役契機のCZ当選率が良好です。高設定期待度アップ。")
                overall_score += 5
            elif karakuri_cz_rate > 1000: # 目安
                indications.append("からくりレア役契機のCZ当選率が低めです。低設定の可能性。")
                overall_score -= 3
    else:
        st.write("**CZ当選履歴は入力されていません。**")

    # AT終了画面
    if selected_end_screens:
        st.write("**AT終了画面:**")
        for screen, count in end_screen_counts.items():
            if count > 0:
                indication_text = at_end_screen_options.get(screen, '特定示唆なし')
                st.write(f"- {screen} ({count}回出現) → **{indication_text}**")
                if "設定6濃厚" in indication_text:
                    overall_score += 50
                    confidence_level = "非常に高い"
                elif "設定4以上濃厚" in indication_text or "設定456確定" in indication_text:
                    overall_score += 30
                    confidence_level = "高い"
                elif "設定2以上濃厚" in indication_text:
                    overall_score += 15
                elif "高設定示唆" in indication_text:
                    overall_score += 10
                elif "偶数設定示唆" in indication_text or "奇数設定示唆" in indication_text:
                    overall_score += 5

    # AT中のテーブル選択
    if st.session_state.at_tables:
        st.write("**AT中のテーブル選択履歴:**")
        for i, at_table in enumerate(st.session_state.at_tables):
            st.write(f"AT {i+1}回目:")
            selected_tables = []
            if at_table['start'] != '選択なし': selected_tables.append(at_table['start'].split(' ')[0])
            if at_table['success1'] != '選択なし': selected_tables.append(at_table['success1'].split(' ')[0])
            if at_table['success2'] != '選択なし': selected_tables.append(at_table['success2'].split(' ')[0])

            if selected_tables:
                st.write(f"- 選択されたテーブル: {', '.join(selected_tables)}")
                for table_name in selected_tables:
                    if table_name in ['テーブル3', 'テーブル4']:
                        indications.append(f"{table_name} ({table_indications[table_name]})の選択が確認されました。高設定期待度アップ。")
                        overall_score += 8
            else:
                st.write("- (入力なし)")

    # 踊れ！オリンピア中の上乗せ数字
    if olympia_addon != '選択なし' and olympia_addon != 'その他':
        st.write(f"**踊れ！オリンピア中の上乗せ数字: {olympia_addon}**")
        if '+6' in olympia_addon:
            indications.append("踊れ！オリンピア「+6」出現 → 設定6濃厚！")
            overall_score += 40
            confidence_level = "非常に高い"
        elif '+4' in olympia_addon:
            indications.append("踊れ！オリンピア「+4」出現 → 設定4以上濃厚！")
            overall_score += 25
            confidence_level = "高い"
        elif '+20' in olympia_addon:
            indications.append("踊れ！オリンピア「+20」出現 → 設定2以上濃厚！")
            overall_score += 10

    # エンディング中のレア役時、筐体上部ランプ色
    if ending_lamp == '虹色 (設定6濃厚)':
        st.write("**エンディング中ランプ色: 虹色 (設定6濃厚)**")
        indications.append("エンディング中ランプが虹色 → 設定6濃厚！")
        overall_score += 50
        confidence_level = "非常に高い"

    # 運命の一撃の成功状況
    st.write("**運命の一撃 成功状況:**")
    total_first_unmei = len(st.session_state.unmei_first)
    total_continue_unmei = len(st.session_state.unmei_continue)

    rare_yakunashi_first_success = sum(1 for entry in st.session_state.unmei_first if entry['success'] == '成功' and entry['trigger'] == 'レア役なし・最終ゲーム小役なし')
    if rare_yakunashi_first_success > 0:
        indications.append(f"最初の運命の一撃でレア役・最終ゲーム小役なし成功 ({rare_yakunashi_first_success}回)を確認。これは非常に強力な高設定示唆です！")
        overall_score += (rare_yakunashi_first_success * 20) # 1回あたり20点

    successful_continue_unmei_no_forced = 0
    total_continue_unmei_eval = 0
    for entry in st.session_state.unmei_continue:
        if entry['success'] == '成功':
            if entry['trigger'] not in ['強レア役', '最終ゲーム小役']: # 強制成功を除外
                successful_continue_unmei_no_forced += 1
                total_continue_unmei_eval += 1
            elif entry['trigger'] in ['強レア役', '最終ゲーム小役']: # 強制成功も試行回数に含めるか検討、今回は含める
                 total_continue_unmei_eval += 1
        elif entry['success'] == '失敗':
             total_continue_unmei_eval += 1

    if total_continue_unmei_eval > 0:
        continue_unmei_rate = successful_continue_unmei_no_forced / total_continue_unmei_eval
        st.write(f"継続運命の一撃 (レア役・最終ゲーム小役なし) 成功率: {continue_unmei_rate:.2%} ({successful_continue_unmei_no_forced}回 / {total_continue_unmei_eval}回)")
        if continue_unmei_rate >= 0.80:
            indications.append("継続運命の一撃成功率が非常に高いです (80%以上)。設定6の期待大！")
            overall_score += 15
        elif continue_unmei_rate >= 0.60:
            indications.append("継続運命の一撃成功率が比較的高めです (60%以上)。設定4以上の期待。")
            overall_score += 8
        elif continue_unmei_rate < 0.40:
            indications.append("継続運命の一撃成功率が低めです。低設定の可能性。")
            overall_score -= 5
    else:
        st.write("継続運命の一撃は入力されていません。")

    # AT直撃
    if at_direct_hit_count > 0:
        st.write(f"**AT直撃回数: {at_direct_hit_count}回**")
        indications.append(f"AT直撃 ({at_direct_hit_count}回) が確認されました。これは強力な高設定示唆です！")
        overall_score += (at_direct_hit_count * 15) # 1回あたり15点


    # --- B. 店舗・外部要因に関する評価 (スコアリング) ---
    st.markdown("---")
    st.subheader("### 店舗・外部要因からの評価")
    external_score = 0

    # スコアリング定義 (上記提案に基づいて設定)
    external_scores = {
        'hall_karakuri_tendency': {'高い': 3, '普通': 0, '低い': -3, '選択しない': 0},
        'is_main_machine': {'はい': 2, 'いいえ': 0, '選択しない': 0},
        'event_day_type': {'強いイベント日 (例: 周年、全台系示唆)': 5, '弱いイベント日 (例: 特定機種示唆)': 3, 'イベントなし': 0, '選択しない': 0},
        'karakuri_coverage': {'ある': 2, 'ない': 0, '選択しない': 0},
        'high_setting_coverage': {'ある': 4, 'ない': 0, '選択しない': 0},
        'is_normal_day': {'はい': 0, 'いいえ': 0, '選択しない': 0}, # この項目自体はスコアに直接寄与せず、イベント日などで判断
        'performer_presence': {'いる': 3, 'いない': 0, '選択しない': 0},
        'seen_setting6_in_hall': {'ある': 5, 'ない': 0, '選択しない': 0},
        'hall_setting6_tendency': {'高い': 4, '普通': 0, '低い': -4, '選択しない': 0},
    }

    external_score += external_scores['hall_karakuri_tendency'].get(hall_karakuri_tendency, 0)
    external_score += external_scores['is_main_machine'].get(is_main_machine, 0)
    external_score += external_scores['event_day_type'].get(event_day_type, 0)
    external_score += external_scores['karakuri_coverage'].get(karakuri_coverage, 0)
    external_score += external_scores['high_setting_coverage'].get(high_setting_coverage, 0)
    # is_normal_day はevent_day_typeで判断
    external_score += external_scores['performer_presence'].get(performer_presence, 0)
    external_score += external_scores['seen_setting6_in_hall'].get(seen_setting6_in_hall, 0)
    external_score += external_scores['hall_setting6_tendency'].get(hall_setting6_tendency, 0)

    if external_score > 0:
        indications.append(f"店舗・外部要因からの加点要素が確認されました (スコア: +{external_score}点)。高設定投入の期待度が高まります。")
    elif external_score < 0:
        indications.append(f"店舗・外部要因からの減点要素が確認されました (スコア: {external_score}点)。高設定投入の期待度が低めです。")
    else:
        indications.append("店舗・外部要因からは特段の加点・減点要素は見られません。")

    if other_machine_status:
        st.write(f"**その他の台の状況:** {other_machine_status}")

    overall_score += external_score

    st.markdown("---")
    st.subheader("### 総合判定")

    if confidence_level == "非常に高い":
        st.success("**🎉 設定6濃厚の強力な示唆が複数確認されました！ 設定6である可能性が非常に高いです！ 🎉**")
    elif confidence_level == "高い":
        st.success("**✨ 設定4以上濃厚の示唆や、設定6示唆の要素が確認されました。高設定の可能性が高いです！ ✨**")
    elif overall_score >= 20: # 閾値は調整してください
        st.warning(f"**👍 高設定に期待できる要素が複数確認されました！ (総合スコア: {overall_score})**")
    elif overall_score >= 0:
        st.info(f"**🤔 現時点では判断が難しいです。引き続き、より強い示唆や数値の変化に注目してください。 (総合スコア: {overall_score})**")
    else:
        st.error(f"**👎 低設定を示唆する要素や、高設定を否定する要素が確認されました。遊技継続は慎重に。 (総合スコア: {overall_score})**")

    st.markdown("---")
    st.write("**詳細な示唆内容:**")
    if indications:
        for ind in indications:
            st.write(f"- {ind}")
    else:
        st.write("現時点では特段の示唆はありません。")

    st.write("\n_※このツールは提供された情報に基づいた推測であり、実際の遊技結果やホールの状況によって設定は変動します。最終的な判断はご自身の責任で行ってください。_")
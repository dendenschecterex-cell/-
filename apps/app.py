import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re

# ページ設定
st.set_page_config(page_title="合同会社霞海喜実績管理", layout="wide")

# カラー設定（本所＝青、葛西＝オレンジ）
COLOR_MAP = {
    "かすみ介護相談室": "#1f77b4",      # ビジネス・ブルー
    "かすみ介護相談室葛西": "#ff7f0e"  # エネルギッシュ・オレンジ
}

# デザインとフォントの徹底調整
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap" rel="stylesheet">
    <style>
    * { font-family: 'Noto Sans JP', sans-serif; }
    
    /* 全体の背景 */
    .stApp { background-color: #f4f7f9; }
    
    /* ヘッダーデザイン */
    .header-box {
        background: linear-gradient(135deg, #1e3d59 0%, #2d547a 100%);
        padding: 30px;
        border-radius: 15px;
        color: white;
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* 指標カードのデザイン */
    .metric-card {
        background: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        border-top: 5px solid #1f77b4;
        text-align: center;
    }
    .metric-label { font-size: 20px; color: #666; font-weight: 700; }
    .metric-value { font-size: 55px; color: #1e3d59; font-weight: 900; margin: 10px 0; }
    
    /* セクション見出し */
    .section-title {
        font-size: 28px;
        font-weight: 900;
        color: #1e3d59;
        margin-top: 40px;
        margin-bottom: 20px;
        border-left: 8px solid #ff7f0e;
        padding-left: 15px;
    }

    /* アップローダーを隠す */
    [data-testid="stFileUploaderFileName"], [data-testid="stFileUploaderFileData"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

# ヘッダー表示
st.markdown('<div class="header-box"><h1 style="margin:0; font-size:40px;">🏢 合同会社霞海喜 経営管理システム</h1><p style="margin:5px 0 0 0; opacity:0.8;">Executive Management Dashboard</p></div>', unsafe_allow_html=True)

# --- ファイルアップロード（開閉式） ---
with st.expander("📥 CSVデータ取込（ファイルをドロップ後、閉じてください）"):
    uploaded_files = st.file_uploader("", type="csv", accept_multiple_files=True, label_visibility="collapsed")

# 報酬計算ロジック
def estimate_revenue(kaigodo):
    k = str(kaigodo)
    u_price = 10.9
    if '介１' in k or '介２' in k: units = 1086
    elif '介３' in k or '介４' in k or '介５' in k: units = 1398
    elif '支' in k: units = 442
    else: units = 0
    return int(units * u_price)

def get_branch(cm_name):
    if any(kw in str(cm_name) for kw in ["中村", "鈴木", "西野"]): return "かすみ介護相談室"
    return "かすみ介護相談室葛西"

def get_month_from_filename(filename):
    match = re.search(r'(\d{4})[.-](\d{1,2})', filename)
    if match: return f"{match.group(1)}-{int(match.group(2)):02d}"
    return None

all_data_list = []
if uploaded_files:
    for file in uploaded_files:
        month_label = get_month_from_filename(file.name)
        if month_label:
            try:
                df = pd.read_csv(file, encoding='utf-8')
            except:
                df = pd.read_csv(file, encoding='shift-jis')
            df = df.dropna(subset=['利用者名'])
            df['年月'] = month_label
            df['拠点'] = df['ケアマネ'].apply(get_branch)
            df['概算報酬'] = df['要介護度'].apply(estimate_revenue)
            all_data_list.append(df)

if all_data_list:
    df_all = pd.concat(all_data_list).drop_duplicates(subset=['利用者名', '年月'])
    months = sorted(df_all['年月'].unique(), reverse=True)
    
    # 月選択
    selected_month = st.selectbox("📅 表示月を選択", months)
    df_latest = df_all[df_all['年月'] == selected_month]

    # --- 1. 最重要指標 (KPI) ---
    st.markdown('<p class="section-title">📊 全体コンディション</p>', unsafe_allow_html=True)
    kpi1, kpi2 = st.columns(2)
    with kpi1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">総利用者数</div><div class="metric-value">{len(df_latest)} <span style="font-size:25px;">件</span></div></div>', unsafe_allow_html=True)
    with kpi2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">総見込報酬</div><div class="metric-value">¥ {df_latest["概算報酬"].sum():,} <span style="font-size:25px;">円</span></div></div>', unsafe_allow_html=True)

    # --- 2. ケアマネ別売上ランキング (経営者が次に気にするもの) ---
    st.markdown('<p class="section-title">🏆 ケアマネジャー別 売上実績</p>', unsafe_allow_html=True)
    cm_summary = df_latest.groupby(['ケアマネ', '拠点']).agg({'概算報酬':'sum'}).reset_index().sort_values('概算報酬', ascending=False)
    fig_rank = px.bar(cm_summary, x='ケアマネ', y='概算報酬', text='概算報酬', color='拠点', color_discrete_map=COLOR_MAP)
    fig_rank.update_traces(texttemplate='¥%{text:,.0f}', textposition='outside', textfont=dict(size=16, color="black", family="Noto Sans JP"))
    fig_rank.update_layout(xaxis_tickfont_size=18, plot_bgcolor="rgba(0,0,0,0)", yaxis_visible=False)
    st.plotly_chart(fig_rank, use_container_width=True)

    # --- 3. 拠点別詳細・介護度内訳 ---
    st.markdown('<p class="section-title">📍 拠点別 詳細分析</p>', unsafe_allow_html=True)
    col_b1, col_b2 = st.columns(2)
    branches = ["かすみ介護相談室", "かすみ介護相談室葛西"]
    
    for branch, col in zip(branches, [col_b1, col_b2]):
        with col:
            df_b = df_latest[df_latest['拠点'] == branch]
            rev_b = df_b['概算報酬'].sum()
            st.markdown(f'<div style="background:{COLOR_MAP[branch]}; color:white; padding:15px; border-radius:10px; font-weight:900; font-size:22px; text-align:center;">{branch}<br><span style="font-size:28px;">¥ {rev_b:,} 円 ({len(df_b)}件)</span></div>', unsafe_allow_html=True)
            care_data = df_b['要介護度'].value_counts().reset_index()
            fig_pie = px.pie(care_data, values='count', names='要介護度', hole=0.5, color_discrete_sequence=px.colors.qualitative.Prism)
            fig_pie.update_traces(textinfo='percent+label', textfont_size=16)
            fig_pie.update_layout(margin=dict(t=30, b=0, l=0, r=0), height=350)
            st.plotly_chart(fig_pie, use_container_width=True)

    # --- 4. 月次推移 (縦棒グラフ) ---
    st.markdown('<p class="section-title">📈 12ヶ月推移分析（縦棒グラフ）</p>', unsafe_allow_html=True)
    trend_df = df_all.groupby(['年月', '拠点']).agg({'利用者名':'count', '概算報酬':'sum'}).reset_index()
    trend_df['月'] = trend_df['年月'].apply(lambda x: f"{int(x.split('-')[1])}月")

    t_col1, t_col2 = st.columns(2)
    with t_col1:
        fig_t_rev = px.bar(trend_df, x='月', y='概算報酬', color='拠点', barmode='group', title="売上の推移 (円)", color_discrete_map=COLOR_MAP)
        fig_t_rev.update_layout(font_size=14, xaxis_title="", yaxis_title="報酬額")
        st.plotly_chart(fig_t_rev, use_container_width=True)
    with t_col2:
        fig_t_cnt = px.bar(trend_df, x='月', y='利用者名', color='拠点', barmode='group', title="件数の推移 (件)", color_discrete_map=COLOR_MAP)
        fig_t_cnt.update_layout(font_size=14, xaxis_title="", yaxis_title="利用者数")
        st.plotly_chart(fig_t_cnt, use_container_width=True)

    # --- 5. 担当者ドリルダウン ---
    st.markdown('<p class="section-title">🔍 担当者別 詳細カルテ</p>', unsafe_allow_html=True)
    selected_cm = st.selectbox("確認したい担当者を選択", ["-- 選択してください --"] + list(cm_summary['ケアマネ'].unique()))
    
    if selected_cm != "-- 選択してください --":
        cm_data = df_latest[df_latest['ケアマネ'] == selected_cm]
        cm_all_time_rev = df_all[df_all['ケアマネ'] == selected_cm]['概算報酬'].sum()
        
        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("当月件数", f"{len(cm_data)} 件")
        c_m2.metric("当月売上", f"¥ {cm_data['概算報酬'].sum():,} 円")
        c_m3.metric("累計売上額 (全期間)", f"¥ {cm_all_time_rev:,} 円")
        
        st.dataframe(cm_data[['利用者名', '要介護度', 'メモ', '概算報酬']].style.format({"概算報酬": "¥{:,.0f}"}), use_container_width=True)

else:
    st.info("CSVファイルをアップロードしてください（例：2026.04_実績.csv）")

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re

# ページ設定
st.set_page_config(page_title="合同会社霞海喜実績管理", layout="wide")

# CSS（謎の文字が出ないように修正済）
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@900&display=swap');
    
    .stApp { background-color: #f8f9fa; }
    
    /* 巨大なメトリクスカード */
    .metric-container {
        display: flex;
        justify-content: space-around;
        gap: 20px;
        margin-bottom: 40px;
    }
    .m-card {
        background: white;
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        width: 100%;
        text-align: center;
        border-bottom: 10px solid #1f77b4;
    }
    .m-label { font-size: 30px; font-weight: bold; color: #555; margin-bottom: 10px; }
    .m-value { font-size: 100px; font-weight: 900; color: #1e3d59; line-height: 1; }
    .m-unit { font-size: 40px; font-weight: bold; color: #1e3d59; }

    /* セクション見出し */
    .section-header {
        font-size: 40px;
        font-weight: 900;
        color: #1e3d59;
        margin: 50px 0 20px 0;
        padding: 10px 20px;
        border-left: 15px solid #ff7f0e;
        background: #fff;
        border-radius: 5px;
    }

    /* アップローダー関連を隠す */
    [data-testid="stFileUploaderFileName"], [data-testid="stFileUploaderFileData"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

# ヘッダー
st.markdown('<div style="background:#1e3d59; padding:40px; border-radius:20px; color:white; text-align:center; margin-bottom:40px;"><h1 style="font-size:60px; margin:0;">🏢 合同会社霞海喜 経営管理システム</h1></div>', unsafe_allow_html=True)

# --- ファイルアップロード ---
with st.expander("📥 データを更新する（ここをクリックしてファイルをドロップ）"):
    uploaded_files = st.file_uploader("", type="csv", accept_multiple_files=True, label_visibility="collapsed")

# 報酬計算
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
    selected_month = st.selectbox("📅 表示月を選択", months)
    df_latest = df_all[df_all['年月'] == selected_month]

    # --- 1. 最重要指標 (巨大化) ---
    st.markdown('<p class="section-header">💰 全体コンディション</p>', unsafe_allow_html=True)
    rev_total = df_latest['概算報酬'].sum()
    cnt_total = len(df_latest)
    
    st.markdown(f"""
    <div class="metric-container">
        <div class="m-card"><div class="m-label">総利用者数</div><div class="m-value">{cnt_total}<span class="m-unit"> 件</span></div></div>
        <div class="m-card"><div class="m-label">総見込報酬</div><div class="m-value">¥ {rev_total:,}<span class="m-unit"> 円</span></div></div>
    </div>
    """, unsafe_allow_html=True)

    # --- 2. ケアマネ別売上ランキング ---
    st.markdown('<p class="section-header">🏆 ケアマネ別 売上ランキング</p>', unsafe_allow_html=True)
    cm_summary = df_latest.groupby(['ケアマネ', '拠点']).agg({'概算報酬':'sum'}).reset_index().sort_values('概算報酬', ascending=False)
    fig_rank = px.bar(cm_summary, x='ケアマネ', y='概算報酬', text='概算報酬', color='拠点', 
                        color_discrete_map={"かすみ介護相談室": "#1f77b4", "かすみ介護相談室葛西": "#ff7f0e"})
    fig_rank.update_traces(texttemplate='¥%{text:,.0f}', textposition='outside', textfont_size=20)
    fig_rank.update_layout(xaxis_tickfont_size=22, height=600, yaxis_visible=False, plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_rank, use_container_width=True)

    # --- 3. 拠点別・介護度内訳 (円グラフ見切れ対策) ---
    st.markdown('<p class="section-header">📍 拠点別 詳細分析</p>', unsafe_allow_html=True)
    col_b1, col_b2 = st.columns(2)
    branches = [("かすみ介護相談室", col_b1, "#1f77b4"), ("かすみ介護相談室葛西", col_b2, "#ff7f0e")]
    
    for branch, col, color in branches:
        with col:
            df_b = df_latest[df_latest['拠点'] == branch]
            rev_b = df_b['概算報酬'].sum()
            st.markdown(f'<div style="background:{color}; color:white; padding:20px; border-radius:15px; font-weight:900; font-size:30px; text-align:center; margin-bottom:20px;">{branch}<br>¥ {rev_b:,} 円 ({len(df_b)}件)</div>', unsafe_allow_html=True)
            care_data = df_b['要介護度'].value_counts().reset_index()
            fig_pie = px.pie(care_data, values='count', names='要介護度', hole=0.5, 
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            # 文字切れ対策
            fig_pie.update_traces(textinfo='percent+label', textfont_size=20, textposition='outside')
            fig_pie.update_layout(margin=dict(t=50, b=50, l=50, r=50), height=500, showlegend=True, legend=dict(font=dict(size=18)))
            st.plotly_chart(fig_pie, use_container_width=True)

    # --- 4. 12ヶ月推移 (横幅フル活用 + データラベル追加) ---
    st.markdown('<p class="section-header">📈 月次推移分析（縦棒フルサイズ）</p>', unsafe_allow_html=True)
    trend_df = df_all.groupby(['年月', '拠点']).agg({'利用者名':'count', '概算報酬':'sum'}).reset_index()
    trend_df['月'] = trend_df['年月'].apply(lambda x: f"{int(x.split('-')[1])}月")

    # 売上推移
    fig_t_rev = px.bar(trend_df, x='月', y='概算報酬', color='拠点', barmode='group', text='概算報酬',
                       title="【売上の推移】 (円)", color_discrete_map={"かすみ介護相談室": "#1f77b4", "かすみ介護相談室葛西": "#ff7f0e"})
    fig_t_rev.update_traces(texttemplate='¥%{text:,.0f}', textposition='outside', textfont_size=16)
    fig_t_rev.update_layout(height=600, xaxis_tickfont_size=20, yaxis_title="報酬額", font=dict(size=18))
    st.plotly_chart(fig_t_rev, use_container_width=True)

    # 件数推移
    fig_t_cnt = px.bar(trend_df, x='月', y='利用者名', color='拠点', barmode='group', text='利用者名',
                       title="【件数の推移】 (件)", color_discrete_map={"かすみ介護相談室": "#1f77b4", "かすみ介護相談室葛西": "#ff7f0e"})
    fig_t_cnt.update_traces(texttemplate='%{text}件', textposition='outside', textfont_size=18)
    fig_t_cnt.update_layout(height=600, xaxis_tickfont_size=20, yaxis_title="利用者数", font=dict(size=18))
    st.plotly_chart(fig_t_cnt, use_container_width=True)

    # --- 5. 担当者別ドリルダウン ---
    st.markdown('<p class="section-header">🔍 担当者別 詳細カルテ</p>', unsafe_allow_html=True)
    selected_cm = st.selectbox("担当者名を選択してください", ["-- 選択してください --"] + list(cm_summary['ケアマネ'].unique()))
    
    if selected_cm != "-- 選択してください --":
        cm_data = df_latest[df_latest['ケアマネ'] == selected_cm]
        cm_all_time_rev = df_all[df_all['ケアマネ'] == selected_cm]['概算報酬'].sum()
        
        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("当月件数", f"{len(cm_data)} 件")
        c_m2.metric("当月売上額", f"¥ {cm_data['概算報酬'].sum():,} 円")
        c_m3.metric("全期間累計売上", f"¥ {cm_all_time_rev:,} 円")
        
        st.dataframe(cm_data[['利用者名', '要介護度', 'メモ', '概算報酬']].style.format({"概算報酬": "¥{:,.0f}"}), use_container_width=True)

else:
    st.info("CSVファイルをアップロードしてください（例：2026.04_実績.csv）")

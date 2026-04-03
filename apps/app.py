import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re

# ページ設定
st.set_page_config(page_title="合同会社霞海喜実績管理", layout="wide")

# CSS（デザイン調整）
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@900&display=swap');
    .stApp { background-color: #f8f9fa; }
    
    /* 巨大なメトリクス */
    .metric-container { display: flex; justify-content: space-around; gap: 20px; margin-bottom: 20px; }
    .m-card {
        background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        width: 100%; text-align: center; border-bottom: 8px solid #1f77b4;
    }
    .m-label { font-size: 22px; font-weight: bold; color: #555; margin-bottom: 5px; }
    .m-value { font-size: 65px; font-weight: 900; color: #1e3d59; line-height: 1.1; }
    .m-unit { font-size: 25px; font-weight: bold; color: #1e3d59; }

    /* セクション見出し */
    .section-header {
        font-size: 35px; font-weight: 900; color: #1e3d59; margin: 40px 0 20px 0;
        padding: 12px 20px; border-left: 12px solid #ff7f0e; background: #fff; border-radius: 5px;
    }

    [data-testid="stFileUploaderFileName"], [data-testid="stFileUploaderFileData"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

# ヘッダー
st.markdown('<div style="background:#1e3d59; padding:30px; border-radius:15px; color:white; text-align:center; margin-bottom:30px;"><h1 style="font-size:45px; margin:0;">🏢 合同会社霞海喜 経営管理システム</h1></div>', unsafe_allow_html=True)

# --- ファイルアップロード ---
with st.expander("📥 データを取込・更新（終わったら閉じてください）"):
    uploaded_files = st.file_uploader("", type="csv", accept_multiple_files=True, label_visibility="collapsed")

# 報酬計算（江戸川区：1級地 10.9円）
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
            df = df.dropna(subset=['利用者名', 'ケアマネ'])
            df['年月'] = month_label
            df['拠点'] = df['ケアマネ'].apply(get_branch)
            df['概算報酬'] = df['要介護度'].apply(estimate_revenue)
            all_data_list.append(df)

if all_data_list:
    df_all = pd.concat(all_data_list).drop_duplicates(subset=['利用者名', '年月'])
    months_asc = sorted(df_all['年月'].unique()) 
    months_desc = months_asc[::-1] 
    
    def to_jp_month(ym):
        y, m = ym.split('-')
        return f"{y}年{int(m)}月"

    selected_month = st.selectbox("📅 表示する月を選択してください", months_desc)
    df_latest = df_all[df_all['年月'] == selected_month]

    # --- 1. メイン指標（選択月と累計） ---
    st.markdown(f'<p class="section-header">💰 {to_jp_month(selected_month)} 実績状況</p>', unsafe_allow_html=True)
    rev_monthly = df_latest['概算報酬'].sum()
    cnt_monthly = len(df_latest)
    rev_total_all = df_all['概算報酬'].sum()

    st.markdown(f"""
    <div class="metric-container">
        <div class="m-card"><div class="m-label">当月利用者数</div><div class="m-value">{cnt_monthly}<span class="m-unit"> 件</span></div></div>
        <div class="m-card"><div class="m-label">当月見込報酬</div><div class="m-value">¥ {rev_monthly:,}<span class="m-unit"> 円</span></div></div>
        <div class="m-card" style="border-bottom-color:#ff7f0e;"><div class="m-label">全期間累計売上</div><div class="m-value">¥ {rev_total_all:,}<span class="m-unit"> 円</span></div></div>
    </div>
    """, unsafe_allow_html=True)

    # --- 2. ケアマネ別ランキング（当月実績メイン＋累計併記） ---
    st.markdown(f'<p class="section-header">🏆 ケアマネ別：{to_jp_month(selected_month)}実績（累計売上も表示）</p>', unsafe_allow_html=True)
    
    # 当月集計
    monthly_cm = df_latest.groupby(['ケアマネ', '拠点']).agg({'概算報酬':'sum'}).reset_index()
    # 累計集計
    total_cm = df_all.groupby('ケアマネ').agg({'概算報酬':'sum'}).reset_index()
    total_cm.columns = ['ケアマネ', '累計報酬']
    # 合体
    rank_df = pd.merge(monthly_cm, total_cm, on='ケアマネ').sort_values('概算報酬', ascending=False)

    fig_rank = go.Figure()
    # 拠点で色分けするためにループ
    for branch, color in [("かすみ介護相談室", "#1f77b4"), ("かすみ介護相談室葛西", "#ff7f0e")]:
        b_df = rank_df[rank_df['拠点'] == branch]
        fig_rank.add_trace(go.Bar(
            x=b_df['ケアマネ'], y=b_df['概算報酬'], name=branch, marker_color=color,
            customdata=b_df['累計報酬'],
            text=b_df.apply(lambda r: f"当月 ¥{r['概算報酬']:,}<br><span style='font-size:12px;'>累計 ¥{r['累計報酬']:,}</span>", axis=1),
            textposition='outside',
            textfont=dict(size=14, color="black")
        ))
    
    fig_rank.update_layout(
        xaxis_tickfont_size=18, height=600, margin=dict(t=80),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(0,0,0,0)", yaxis_visible=False
    )
    st.plotly_chart(fig_rank, use_container_width=True)

    # --- 3. 拠点別 詳細分析 ---
    st.markdown('<p class="section-header">📍 拠点別 詳細内訳</p>', unsafe_allow_html=True)
    col_b1, col_b2 = st.columns(2)
    branches = [("かすみ介護相談室", col_b1, "#1f77b4"), ("かすみ介護相談室葛西", col_b2, "#ff7f0e")]
    for branch, col, color in branches:
        with col:
            df_b = df_latest[df_latest['拠点'] == branch]
            rev_b = df_b['概算報酬'].sum()
            st.markdown(f'<div style="background:{color}; color:white; padding:15px; border-radius:15px; font-weight:900; font-size:25px; text-align:center; margin-bottom:10px;">{branch}<br>¥ {rev_b:,} 円 ({len(df_b)}件)</div>', unsafe_allow_html=True)
            care_data = df_b['要介護度'].value_counts().reset_index()
            fig_pie = px.pie(care_data, values='count', names='要介護度', hole=0.4, 
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_pie.update_traces(textinfo='label+percent', textposition='inside', insidetextfont=dict(size=18, color="black"))
            fig_pie.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=500, showlegend=True, 
                                  legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5, font=dict(size=14)))
            st.plotly_chart(fig_pie, use_container_width=True)

    # --- 4. 月次推移分析 ---
    st.markdown('<p class="section-header">📈 月次推移分析（時系列順）</p>', unsafe_allow_html=True)
    trend_df = df_all.groupby(['年月', '拠点']).agg({'利用者名':'count', '概算報酬':'sum'}).reset_index().sort_values('年月')
    trend_df['表示年月'] = trend_df['年月'].apply(to_jp_month)

    fig_t_rev = px.bar(trend_df, x='表示年月', y='概算報酬', color='拠点', barmode='group', text='概算報酬',
                       color_discrete_map={"かすみ介護相談室": "#1f77b4", "かすみ介護相談室葛西": "#ff7f0e"})
    fig_t_rev.update_traces(texttemplate='¥%{text:,.0f}', textposition='outside', textfont_size=16)
    fig_t_rev.update_layout(title="【報酬の推移】", height=500, xaxis_tickfont_size=18, xaxis_title="", font=dict(size=16))
    st.plotly_chart(fig_t_rev, use_container_width=True)

    fig_t_cnt = px.bar(trend_df, x='表示年月', y='利用者名', color='拠点', barmode='group', text='利用者名',
                       color_discrete_map={"かすみ介護相談室": "#1f77b4", "かすみ介護相談室葛西": "#ff7f0e"})
    fig_t_cnt.update_traces(texttemplate='%{text}件', textposition='outside', textfont_size=16)
    fig_t_cnt.update_layout(title="【件数の推移】", height=500, xaxis_tickfont_size=18, xaxis_title="", font=dict(size=16))
    st.plotly_chart(fig_t_cnt, use_container_width=True)

    # --- 5. 担当者別 詳細カルテ ---
    st.markdown('<p class="section-header">🔍 担当者別 詳細カルテ</p>', unsafe_allow_html=True)
    cm_list = sorted([str(x) for x in df_latest['ケアマネ'].dropna().unique()])
    selected_cm = st.selectbox("担当者名を選択してください", ["-- 選択してください --"] + cm_list)
    if selected_cm != "-- 選択してください --":
        cm_data = df_latest[df_latest['ケアマネ'] == selected_cm]
        cm_total_row = total_cm[total_cm['ケアマネ'] == selected_cm]
        cm_total_val = cm_total_row['累計報酬'].values[0] if not cm_total_row.empty else 0
        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("当月件数", f"{len(cm_data)} 件")
        c_m2.metric("当月売上", f"¥ {cm_data['概算報酬'].sum():,} 円")
        c_m3.metric("全期間累計売上", f"¥ {cm_total_val:,} 円")
        st.dataframe(cm_data[['利用者名', '要介護度', 'メモ', '概算報酬']].style.format({"概算報酬": "¥{:,.0f}"}), use_container_width=True)

else:
    st.info("CSVファイルをアップロードしてください。ファイル名は『2026.04_xxx.csv』のように始めてください。")

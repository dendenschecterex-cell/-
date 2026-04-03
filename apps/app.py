import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import re

# ページ設定
st.set_page_config(page_title="合同会社霞海喜実績管理", layout="wide")

# 文字を巨大にするCSS
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 70px !important; font-weight: bold !important; color: #1f77b4 !important; }
    [data-testid="stMetricLabel"] { font-size: 30px !important; font-weight: bold !important; }
    .main-title { font-size: 45px; font-weight: bold; color: #2c3e50; border-bottom: 6px solid #1f77b4; }
    .branch-label { font-size: 30px; font-weight: bold; color: #000; background-color: #f0f2f6; padding: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">🏢 合同会社霞海喜 実績管理システム</p>', unsafe_allow_html=True)

# --- 1. ファイルアップローダー ---
st.subheader("📁 CSVファイルをまとめてアップロード")
st.caption("※ファイル名の先頭を『2026.04_xxx.csv』のようにしてアップしてください")
uploaded_files = st.file_uploader("CSVファイルを選択してください（複数可）", type="csv", accept_multiple_files=True)

# 報酬計算（江戸川区: 1級地 10.9円）
def estimate_revenue(kaigodo):
    k = str(kaigodo)
    unit_price = 10.9
    if '介１' in k or '介２' in k: units = 1086
    elif '介３' in k or '介４' in k or '介５' in k: units = 1398
    elif '支' in k: units = 442
    else: units = 0
    return int(units * unit_price)

# 拠点判別
def get_branch(cm_name):
    cm_name = str(cm_name)
    if any(kw in cm_name for kw in ["中村", "鈴木", "西野"]): return "かすみ介護相談室"
    else: return "かすみ介護相談室葛西"

# ファイル名から年月を抜く関数（エラーに強い形式）
def get_month_from_filename(filename):
    match = re.search(r'(\d{4})[.-](\d{1,2})', filename)
    if match:
        year = match.group(1)
        month = f"{int(match.group(2)):02d}"
        return f"{year}-{month}"
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
    months = sorted(df_all['年月'].unique())
    latest_month = months[-1]
    df_latest = df_all[df_all['年月'] == latest_month]

    # --- 【最上段】メイン指標 ---
    st.divider()
    st.subheader(f"📊 {latest_month} 最新の全体実績")
    t1, t2 = st.columns(2)
    t1.metric("全体の総利用者数", f"{len(df_latest)} 件")
    t2.metric("全体の見込報酬", f"¥{df_latest['概算報酬'].sum():,} 円")

    # --- 【中段】拠点別の比較分析 ---
    st.divider()
    st.header(f"📍 {latest_month} 拠点別の実績比較")
    
    b_summary = df_latest.groupby('拠点').agg({'利用者名':'count', '概算報酬':'sum'}).reset_index()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<p class="branch-label">拠点別：件数と報酬の比較</p>', unsafe_allow_html=True)
        # エラーに強い2軸グラフの作成
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(go.Bar(x=b_summary['拠点'], y=b_summary['利用者名'], name='件数', 
                             marker_color='#1f77b4', text=b_summary['利用者名'], textposition='auto',
                             textfont=dict(size=20)), secondary_y=False)
        
        fig.add_trace(go.Bar(x=b_summary['拠点'], y=b_summary['概算報酬'], name='報酬', 
                             marker_color='#ff7f0e', text=b_summary['概算報酬'].apply(lambda x: f"¥{x:,}円"),
                             textposition='auto', textfont=dict(size=18)), secondary_y=True)
        
        fig.update_layout(
            xaxis=dict(tickfont=dict(size=26, color="black", family="Arial Black")),
            legend=dict(font=dict(size=18)),
            margin=dict(l=20, r=20, t=40, b=20)
        )
        fig.update_yaxes(title_text="件数", secondary_y=False, titlefont=dict(size=20))
        fig.update_yaxes(title_text="報酬（円）", secondary_y=True, titlefont=dict(size=20))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<p class="branch-label">拠点別：介護度の内訳</p>', unsafe_allow_html=True)
        fig_care = px.histogram(df_latest, x='拠点', color='要介護度', barmode='group', text_auto=True)
        fig_care.update_layout(font=dict(size=20), xaxis=dict(tickfont=dict(size=26, color="black")))
        st.plotly_chart(fig_care, use_container_width=True)

    # --- 【下段】月次推移グラフ ---
    if len(months) > 1:
        st.divider()
        st.header("📈 報酬・利用者数の月次推移")
        trend_df = df_all.groupby(['年月', '拠点']).agg({'利用者名':'count', '概算報酬':'sum'}).reset_index()
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.plotly_chart(px.line(trend_df, x='年月', y='概算報酬', color='拠点', markers=True, title="報酬推移（円）"), use_container_width=True)
        with col_t2:
            st.plotly_chart(px.line(trend_df, x='年月', y='利用者名', color='拠点', markers=True, title="件数推移（件）"), use_container_width=True)

    # --- ケアマネランキング ---
    st.divider()
    st.header("🏆 ケアマネ別 売上ランキング")
    cm_summary = df_latest.groupby(['ケアマネ', '拠点']).agg({'概算報酬':'sum'}).reset_index().sort_values('概算報酬', ascending=False)
    fig_rank = px.bar(cm_summary, x='ケアマネ', y='概算報酬', text='概算報酬', color='拠点')
    fig_rank.update_traces(texttemplate='%{text:,.0f} 円', textposition='outside', textfont=dict(size=20))
    fig_rank.update_layout(font=dict(size=18), xaxis=dict(tickfont=dict(size=24, color="black")))
    st.plotly_chart(fig_rank, use_container_width=True)

else:
    st.info("CSVファイルをアップロードしてください。ファイル名は『2026.04_xxx.csv』のように始めてください。")

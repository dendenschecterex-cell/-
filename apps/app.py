import streamlit as st
import pandas as pd
import plotly.express as px
import re

# ページ設定
st.set_page_config(page_title="合同会社霞海喜実績管理", layout="wide")

# スタイリッシュにするためのCSS
st.markdown("""
    <style>
    /* メイン数字を巨大に */
    [data-testid="stMetricValue"] { font-size: 75px !important; font-weight: 800 !important; color: #1f77b4 !important; }
    [data-testid="stMetricLabel"] { font-size: 28px !important; font-weight: bold !important; color: #555 !important; }
    /* タイトルデザイン */
    .main-title { font-size: 42px; font-weight: 900; color: #1e3d59; border-left: 10px solid #1f77b4; padding-left: 20px; margin-bottom: 30px; }
    /* グラフのラベルを真っ黒で大きく */
    .branch-header { font-size: 32px; font-weight: 900; color: #000; margin-top: 20px; }
    /* アップローダー部分をスッキリ */
    .stExpander { border: 2px solid #1f77b4 !important; border-radius: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">🏢 合同会社霞海喜 実績管理システム</p>', unsafe_allow_html=True)

# --- 1. スタイリッシュなアップローダー（開閉式） ---
with st.expander("📥 ここをクリックしてCSVファイルをアップロードしてください", expanded=True):
    uploaded_files = st.file_uploader("ナーシングのCSVを選択（ファイル名の先頭を 2026.04_ のようにしてください）", type="csv", accept_multiple_files=True)

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

# ファイル名から年月を抜く関数
def get_month_from_filename(filename):
    match = re.search(r'(\d{4})[.-](\d{1,2})', filename)
    if match:
        return f"{match.group(1)}-{int(match.group(2)):02d}"
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
    st.subheader(f"📊 {latest_month} 最新実績")
    m1, m2 = st.columns(2)
    m1.metric("全体の総利用者数", f"{len(df_latest)} 件")
    m2.metric("全体の見込報酬", f"¥{df_latest['概算報酬'].sum():,} 円")

    # --- 【中段】拠点別の比較分析 ---
    st.divider()
    st.markdown(f'<p class="branch-header">📍 {latest_month} 拠点別の実績分析</p>', unsafe_allow_html=True)
    
    b_summary = df_latest.groupby('拠点').agg({'利用者名':'count', '概算報酬':'sum'}).reset_index()
    
    # 拠点が新しく増えても対応
    col_b1, col_b2 = st.columns(2)
    
    with col_b1:
        # 件数のグラフ（エラー回避のため独立）
        fig_count = px.bar(b_summary, x='拠点', y='利用者名', text_auto=True, title="【拠点別】利用者数（件）",
                           color='拠点', color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_count.update_traces(textfont_size=25, textposition='outside')
        fig_count.update_layout(xaxis=dict(tickfont=dict(size=24, color="black", family="Arial Black")),
                                yaxis=dict(title="件数", tickfont=dict(size=18)))
        st.plotly_chart(fig_count, use_container_width=True)

    with col_b2:
        # 報酬のグラフ（エラー回避のため独立・スケールを最適化）
        fig_rev = px.bar(b_summary, x='拠点', y='概算報酬', text='概算報酬', title="【拠点別】概算報酬（円）",
                         color='拠点', color_discrete_sequence=px.colors.qualitative.Bold)
        fig_rev.update_traces(texttemplate='¥%{text:,.0f} 円', textposition='outside', textfont_size=22)
        fig_rev.update_layout(xaxis=dict(tickfont=dict(size=24, color="black", family="Arial Black")),
                              yaxis=dict(title="報酬（円）", tickfont=dict(size=18)))
        # 報酬の差をハッキリ見せるために、最大値に合わせてY軸を調整
        fig_rev.update_yaxes(range=[0, b_summary['概算報酬'].max() * 1.2])
        st.plotly_chart(fig_rev, use_container_width=True)

    # --- 拠点別の介護度分布 ---
    st.divider()
    st.markdown('<p class="branch-header">📋 拠点別の介護度内訳（なぜ売上が違うか？）</p>', unsafe_allow_html=True)
    fig_care = px.histogram(df_latest, x='拠点', color='要介護度', barmode='group', text_auto=True,
                            color_discrete_sequence=px.colors.qualitative.Vivid)
    fig_care.update_layout(font=dict(size=18), xaxis=dict(tickfont=dict(size=24, color="black")))
    st.plotly_chart(fig_care, use_container_width=True)

    # --- 【下段】月次推移グラフ ---
    if len(months) > 1:
        st.divider()
        st.markdown('<p class="branch-header">📈 過去からの月次推移分析</p>', unsafe_allow_html=True)
        trend_df = df_all.groupby(['年月', '拠点']).agg({'利用者名':'count', '概算報酬':'sum'}).reset_index()
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.plotly_chart(px.line(trend_df, x='年月', y='概算報酬', color='拠点', markers=True, title="売上の推移"), use_container_width=True)
        with col_t2:
            st.plotly_chart(px.line(trend_df, x='年月', y='利用者名', color='拠点', markers=True, title="件数の推移"), use_container_width=True)

    # --- ケアマネランキング ---
    st.divider()
    st.markdown('<p class="branch-header">🏆 ケアマネ別 売上ランキング</p>', unsafe_allow_html=True)
    cm_summary = df_latest.groupby(['ケアマネ', '拠点']).agg({'概算報酬':'sum'}).reset_index().sort_values('概算報酬', ascending=False)
    fig_rank = px.bar(cm_summary, x='ケアマネ', y='概算報酬', text='概算報酬', color='拠点')
    fig_rank.update_traces(texttemplate='¥%{text:,.0f} 円', textposition='outside', textfont=dict(size=20))
    fig_rank.update_layout(xaxis=dict(tickfont=dict(size=24, color="black")))
    st.plotly_chart(fig_rank, use_container_width=True)

else:
    st.info("CSVファイルをアップロードしてください。ファイル名は『2026.04_xxx.csv』のように始めてください。")

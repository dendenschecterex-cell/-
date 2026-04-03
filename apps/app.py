import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ページ設定
st.set_page_config(page_title="合同会社霞海喜実績管理", layout="wide")

# 文字を巨大にするCSS
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 60px !important; font-weight: bold !important; color: #1f77b4 !important; }
    [data-testid="stMetricLabel"] { font-size: 25px !important; font-weight: bold !important; }
    .main-title { font-size: 40px; font-weight: bold; color: #2c3e50; border-bottom: 5px solid #1f77b4; }
    .branch-label { font-size: 24px; font-weight: bold; color: #333; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">🏢 合同会社霞海喜 実績管理システム（12ヶ月分析版）</p>', unsafe_allow_html=True)

# --- 1. ファイルアップローダー（複数対応） ---
st.subheader("📁 CSVファイルをアップロード（複数まとめて12ヶ月分など選択可）")
uploaded_files = st.file_uploader("ナーシングのCSVファイルをすべて選択してください（複数選択可）", type="csv", accept_multiple_files=True)

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

# データ処理
all_data = []
if uploaded_files:
    for file in uploaded_files:
        try:
            df = pd.read_csv(file, encoding='utf-8')
        except:
            df = pd.read_csv(file, encoding='shift-jis')
        
        df = df.dropna(subset=['利用者名'])
        # ファイル内の「作成 年月日」から年月を抽出（なければファイル名からなど）
        df['年月'] = pd.to_datetime(df['作成 年月日']).dt.strftime('%Y-%m')
        df['拠点'] = df['ケアマネ'].apply(get_branch)
        df['概算報酬'] = df['要介護度'].apply(estimate_revenue)
        all_data.append(df)

if all_data:
    df_main = pd.concat(all_data).drop_duplicates(subset=['利用者名', '年月'])
    latest_month = sorted(df_main['年月'].unique())[-1]
    df_latest = df_main[df_main['年月'] == latest_month]

    # --- 【最上段】巨大な数字 ---
    st.divider()
    t1, t2 = st.columns(2)
    t1.metric(f"📈 {latest_month} 総利用者数", f"{len(df_latest)} 件")
    t2.metric(f"💰 {latest_month} 総見込報酬", f"¥{df_latest['概算報酬'].sum():,} 円")

    # --- 【中段】拠点別の比較分析 ---
    st.divider()
    st.header(f"📍 {latest_month} 拠点別の実績・内訳比較")
    
    # 拠点別集計
    b_summary = df_latest.groupby('拠点').agg({'利用者名':'count', '概算報酬':'sum'}).reset_index()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<p class="branch-label">【件数と売上の比較】</p>', unsafe_allow_html=True)
        # 件数と売上の2軸グラフで差を明確にする
        fig_compare = go.Figure()
        fig_compare.add_trace(go.Bar(x=b_summary['拠点'], y=b_summary['利用者名'], name='利用者数（件）', 
                                     text=b_summary['利用者名'], textposition='auto', marker_color='#1f77b4'))
        fig_compare.add_trace(go.Bar(x=b_summary['拠点'], y=b_summary['概算報酬'], name='報酬（円）', 
                                     text=b_summary['概算報酬'].apply(lambda x: f"¥{x:,}"), textposition='auto', marker_color='#ff7f0e', yaxis='y2'))
        
        fig_compare.update_layout(
            yaxis=dict(title="利用者数（件）", titlefont=dict(size=20), tickfont=dict(size=18)),
            yaxis2=dict(title="報酬（円）", titlefont=dict(size=20), tickfont=dict(size=18), overlaying='y', side='right'),
            legend=dict(font=dict(size=18)),
            font=dict(size=18, color="black"),
            xaxis=dict(tickfont=dict(size=22, color="black")) # 拠点名を大きく
        )
        st.plotly_chart(fig_compare, use_container_width=True)

    with col2:
        st.markdown('<p class="branch-label">【拠点別の介護度内訳】</p>', unsafe_allow_html=True)
        # 拠点ごとの介護度分布（これで売上の差の理由がわかる）
        fig_care_branch = px.bar(df_latest, x='拠点', color='要介護度', title="拠点別 介護度分布",
                                 color_discrete_sequence=px.colors.qualitative.Safe)
        fig_care_branch.update_layout(font=dict(size=18), xaxis=dict(tickfont=dict(size=22, color="black")))
        st.plotly_chart(fig_care_branch, use_container_width=True)

    # --- 【下段】12ヶ月の推移グラフ ---
    st.divider()
    st.header("📈 報酬・利用者数の月次推移（過去データ）")
    trend_df = df_main.groupby(['年月', '拠点']).agg({'利用者名':'count', '概算報酬':'sum'}).reset_index()
    
    fig_trend = px.line(trend_df, x='年月', y='概算報酬', color='拠点', markers=True, 
                        title="月次報酬推移（円）", line_shape='linear')
    fig_trend.update_layout(font=dict(size=18), yaxis=dict(tickfont=dict(size=18)))
    st.plotly_chart(fig_trend, use_container_width=True)

    # --- ケアマネランキング ---
    st.divider()
    st.header("🏆 ケアマネ別 売上貢献度")
    cm_summary = df_latest.groupby(['ケアマネ', '拠点']).agg({'概算報酬':'sum'}).reset_index().sort_values('概算報酬', ascending=False)
    fig_rank = px.bar(cm_summary, x='ケアマネ', y='概算報酬', text='概算報酬', color='拠点')
    fig_rank.update_traces(texttemplate='%{text:,.0f} 円', textposition='outside')
    fig_rank.update_layout(font=dict(size=18), xaxis=dict(tickfont=dict(size=20, color="black")))
    st.plotly_chart(fig_rank, use_container_width=True)

else:
    st.info("複数のCSVファイルをアップロードすると、月次推移グラフが表示されます。")

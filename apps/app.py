import streamlit as st
import pandas as pd
import plotly.express as px
import re

# ページ設定
st.set_page_config(page_title="合同会社霞海喜実績管理", layout="wide")

# カラー設定（きみどり & ピンク）
COLOR_MAP = {
    "かすみ介護相談室": "#90EE90",      # きみどり (Light Green)
    "かすみ介護相談室葛西": "#FFB6C1"  # ピンク (Light Pink)
}

# CSSでデザイン調整
st.markdown(f"""
    <style>
    [data-testid="stMetricValue"] {{ font-size: 80px !important; font-weight: 800 !important; color: #2c3e50 !important; }}
    [data-testid="stMetricLabel"] {{ font-size: 30px !important; font-weight: bold !important; }}
    .main-title {{ font-size: 45px; font-weight: 900; color: #1e3d59; border-left: 15px solid #90EE90; padding-left: 20px; }}
    .section-header {{ font-size: 35px; font-weight: 900; color: #000; margin-top: 30px; background: #f8f9fa; padding: 10px; border-radius: 10px; }}
    /* アップロード後のファイル名一覧を隠す（極力スッキリさせる） */
    [data-testid="stFileUploaderFileName"] {{ display: none; }}
    [data-testid="stFileUploaderFileData"] {{ display: none; }}
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">🏢 合同会社霞海喜 実績管理システム</p>', unsafe_allow_html=True)

# --- 1. アップローダー（不要な表示を隠す設定） ---
with st.expander("📥 CSVアップロード（ここをクリックしてファイルを入れ、終わったら閉じてください）", expanded=True):
    uploaded_files = st.file_uploader("CSVを選択", type="csv", accept_multiple_files=True, label_visibility="collapsed")

# 報酬計算（江戸川区: 1級地 10.9円）
def estimate_revenue(kaigodo):
    k = str(kaigodo)
    unit_price = 10.9
    if '介１' in k or '介２' in k: units = 1086
    elif '介３' in k or '介４' in k or '介５' in k: units = 1398
    elif '支' in k: units = 442
    else: units = 0
    return int(units * unit_price)

def get_branch(cm_name):
    if any(kw in str(cm_name) for kw in ["中村", "鈴木", "西野"]): return "かすみ介護相談室"
    else: return "かすみ介護相談室葛西"

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
    
    # --- 月選択プルダウン ---
    st.divider()
    selected_month = st.selectbox("📅 表示する月を選択してください", months)
    df_latest = df_all[df_all['年月'] == selected_month]

    # --- 【最上段】メイン指標 ---
    m1, m2 = st.columns(2)
    m1.metric(f"{selected_month} 総利用者数", f"{len(df_latest)} 件")
    m2.metric(f"{selected_month} 総見込報酬", f"¥{df_latest['概算報酬'].sum():,} 円")

    # --- 【中段1】売上ランキング（中段へ移動） ---
    st.markdown('<p class="section-header">🏆 ケアマネ別 売上ランキング</p>', unsafe_allow_html=True)
    cm_summary = df_latest.groupby(['ケアマネ', '拠点']).agg({'概算報酬':'sum'}).reset_index().sort_values('概算報酬', ascending=False)
    fig_rank = px.bar(cm_summary, x='ケアマネ', y='概算報酬', text='概算報酬', color='拠点',
                        color_discrete_map=COLOR_MAP)
    fig_rank.update_traces(texttemplate='¥%{text:,.0f} 円', textposition='outside', textfont_size=20)
    fig_rank.update_layout(xaxis=dict(tickfont=dict(size=24, color="black", family="Arial Black")), yaxis_title="概算報酬（円）")
    st.plotly_chart(fig_rank, use_container_width=True)

    # --- 【中段2】拠点別の比較 ---
    st.markdown(f'<p class="section-header">📍 {selected_month} 拠点別の実績比較</p>', unsafe_allow_html=True)
    b_summary = df_latest.groupby('拠点').agg({'利用者名':'count', '概算報酬':'sum'}).reset_index()
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        fig_count = px.bar(b_summary, x='拠点', y='利用者名', text_auto=True, title="利用者数（件）",
                           color='拠点', color_discrete_map=COLOR_MAP)
        fig_count.update_traces(textfont_size=25, textposition='outside')
        fig_count.update_layout(xaxis=dict(tickfont=dict(size=26, color="black", family="Arial Black")), showlegend=False)
        st.plotly_chart(fig_count, use_container_width=True)
    with col_b2:
        fig_rev = px.bar(b_summary, x='拠点', y='概算報酬', text='概算報酬', title="概算報酬（円）",
                         color='拠点', color_discrete_map=COLOR_MAP)
        fig_rev.update_traces(texttemplate='¥%{text:,.0f} 円', textposition='outside', textfont_size=22)
        fig_rev.update_layout(xaxis=dict(tickfont=dict(size=26, color="black", family="Arial Black")), showlegend=False)
        st.plotly_chart(fig_rev, use_container_width=True)

    # --- 【中段3】介護度内訳（円グラフへ変更） ---
    st.markdown('<p class="section-header">📋 拠点別の介護度内訳（円グラフ）</p>', unsafe_allow_html=True)
    col_p1, col_p2 = st.columns(2)
    
    branches = ["かすみ介護相談室", "かすみ介護相談室葛西"]
    cols = [col_p1, col_p2]
    
    for branch, col in zip(branches, cols):
        with col:
            df_b = df_latest[df_latest['拠点'] == branch]
            if not df_b.empty:
                care_data = df_b['要介護度'].value_counts().reset_index()
                care_data.columns = ['要介護度', '人数']
                fig_pie = px.pie(care_data, values='人数', names='要介護度', title=f"【{branch}】内訳",
                                 hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_pie.update_traces(textinfo='percent+label', textfont_size=18)
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.write(f"{branch}のデータはありません")

    # --- 【下段】月次推移グラフ（日本語月表記へ修正） ---
    if len(months) > 1:
        st.markdown('<p class="section-header">📈 月次推移分析（過去データ）</p>', unsafe_allow_html=True)
        trend_df = df_all.groupby(['年月', '拠点']).agg({'利用者名':'count', '概算報酬':'sum'}).reset_index()
        # 表示用の月名（2026-04 -> 4月）に変換
        trend_df['表示月'] = trend_df['年月'].apply(lambda x: f"{int(x.split('-')[1])}月")
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            fig_t1 = px.line(trend_df, x='表示月', y='概算報酬', color='拠点', markers=True, title="売上の推移（円）",
                             color_discrete_map=COLOR_MAP)
            fig_t1.update_layout(font=dict(size=18), xaxis_title="月")
            st.plotly_chart(fig_t1, use_container_width=True)
        with col_t2:
            fig_t2 = px.line(trend_df, x='表示月', y='利用者名', color='拠点', markers=True, title="件数の推移（件）",
                             color_discrete_map=COLOR_MAP)
            fig_t2.update_layout(font=dict(size=18), xaxis_title="月")
            st.plotly_chart(fig_t2, use_container_width=True)

else:
    st.info("CSVファイルをアップロードしてください（例：2026.04_xxx.csv）")

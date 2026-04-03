import streamlit as st
import pandas as pd
import plotly.express as px

# ページの設定
st.set_page_config(page_title="合同会社霞海喜実績管理", layout="wide")

# CSSで数字を大きく、見やすく調整
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 40px; color: #1f77b4; }
    .main-title { font-size: 32px; font-weight: bold; color: #2c3e50; border-bottom: 3px solid #1f77b4; padding-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">🏢 合同会社霞海喜 実績管理システム</p>', unsafe_allow_html=True)

# 1. ファイルアップローダー
col_f1, col_f2 = st.columns(2)
with col_f1:
    old_file = st.file_uploader("📅 1. 先月のCSVを選択", type="csv")
with col_f2:
    new_file = st.file_uploader("📅 2. 今月のCSVを選択", type="csv")

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
    branch_a_keywords = ["中村", "鈴木", "西野"]
    if any(kw in cm_name for kw in branch_a_keywords):
        return "かすみ介護相談室"
    else:
        return "かすみ介護相談室葛西"

def process_data(file):
    if file is None: return None
    try:
        df = pd.read_csv(file, encoding='utf-8')
    except:
        df = pd.read_csv(file, encoding='shift-jis')
    df = df.dropna(subset=['利用者名'])
    df['拠点'] = df['ケアマネ'].apply(get_branch)
    df['概算報酬'] = df['要介護度'].apply(estimate_revenue)
    return df

df_old = process_data(old_file)
df_new = process_data(new_file)

if df_new is not None:
    # --- 【最上段】メイン指標 ---
    total_rev = df_new['概算報酬'].sum()
    total_users = len(df_new)
    
    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("全体の総利用者数", f"{total_users} 件")
    m2.metric("全体の見込報酬", f"¥{total_rev:,} 円")
    
    if df_old is not None:
        new_names = set(df_new['利用者名']) - set(df_old['利用者名'])
        lost_names = set(df_old['利用者名']) - set(df_new['利用者名'])
        diff = len(new_names) - len(lost_names)
        m3.metric("前月比の増減", f"{diff:+} 名", f"新規:{len(new_names)} / 終了:{len(lost_names)}")

    # --- 【上段】介護度別割合（円グラフ） ---
    st.divider()
    st.subheader("📊 事業所全体の介護度分布")
    care_counts = df_new['要介護度'].fillna('不明').value_counts().reset_index()
    care_counts.columns = ['要介護度', '人数']
    fig_care = px.pie(care_counts, values='人数', names='要介護度', hole=0.5, 
                      color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_care.update_traces(textinfo='percent+label', textfont_size=15)
    st.plotly_chart(fig_care, use_container_width=True)

    # --- 【中段】拠点別比較（棒グラフ） ---
    st.divider()
    st.header("📍 拠点別の実績比較")
    branch_summary = df_new.groupby('拠点').agg({'利用者名': 'count', '概算報酬': 'sum'}).reset_index()
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        fig_b1 = px.bar(branch_summary, x='拠点', y='利用者名', text_auto=True,
                        title="拠点別 利用者数（件）", color='拠点', color_discrete_map={"かすみ介護相談室":"#1f77b4", "かすみ介護相談室葛西":"#ff7f0e"})
        fig_b1.update_traces(texttemplate='%{y} 件', textposition='outside')
        st.plotly_chart(fig_b1, use_container_width=True)
    
    with col_b2:
        # 概算報酬の比較（カンマ付き、円表記）
        fig_b2 = px.bar(branch_summary, x='拠点', y='概算報酬', text='概算報酬',
                        title="拠点別 概算報酬（円）", color='拠点', color_discrete_map={"かすみ介護相談室":"#1f77b4", "かすみ介護相談室葛西":"#ff7f0e"})
        fig_b2.update_traces(texttemplate='%{text:,.0f} 円', textposition='outside')
        # グラフの差がハッキリ見えるようにY軸を調整
        fig_b2.update_layout(yaxis=dict(range=[0, branch_summary['概算報酬'].max() * 1.2]))
        st.plotly_chart(fig_b2, use_container_width=True)

    # --- 【下段】ケアマネ報酬ランキング ---
    st.divider()
    st.header("🏆 ケアマネ別 売上貢献度ランキング")
    cm_summary = df_new.groupby(['ケアマネ', '拠点']).agg({'利用者名': 'count', '概算報酬': 'sum'}).reset_index().sort_values('概算報酬', ascending=False)
    
    fig_cm_rev = px.bar(cm_summary, x='ケアマネ', y='概算報酬', text='概算報酬', color='拠点',
                        title="担当者別 概算報酬ランキング")
    fig_cm_rev.update_traces(texttemplate='%{text:,.0f} 円', textposition='outside')
    st.plotly_chart(fig_cm_rev, use_container_width=True)

    # --- 【最下段】担当者別ドリルダウン ---
    st.divider()
    st.header("🔍 担当者別の詳細データ")
    selected_cm = st.selectbox("詳しく見たい担当者を選択してください", ["-- 選択してください --"] + list(cm_summary['ケアマネ'].unique()))

    if selected_cm != "-- 選択してください --":
        person_df = df_new[df_new['ケアマネ'] == selected_cm].copy()
        # 報酬をカンマ付き文字列に変換して表示用にする
        person_df['概算報酬（円）'] = person_df['概算報酬'].apply(lambda x: f"¥{x:,}")
        
        st.subheader(f"【{selected_cm}】さんの担当リスト")
        st.write(f"担当件数: **{len(person_df)} 件**  /  概算報酬合計: **¥{person_df['概算報酬'].sum():,} 円**")
        st.dataframe(person_df[['利用者名', '要介護度', '保険者', '概算報酬（円）', 'メモ']], use_container_width=True)

else:
    st.info("CSVファイルをアップロードしてください。")

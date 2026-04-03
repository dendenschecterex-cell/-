import streamlit as st
import pandas as pd
import plotly.express as px

# ページの設定
st.set_page_config(page_title="合同会社霞海喜実績管理", layout="wide")
st.title("🏢 合同会社霞海喜 実績管理システム")

# 1. ファイルアップローダー
col_f1, col_f2 = st.columns(2)
with col_f1:
    old_file = st.file_uploader("1. 先月のCSVを選択", type="csv")
with col_f2:
    new_file = st.file_uploader("2. 今月のCSVを選択", type="csv")

# 報酬計算ロジック（江戸川区: 1級地 10.9円想定）
def estimate_revenue(kaigodo):
    k = str(kaigodo)
    unit_price = 10.9
    # 居宅介護支援費（令和6年度改定 おおよその単価）
    if '介１' in k or '介２' in k:
        units = 1086  # 居宅1
    elif '介３' in k or '介４' in k or '介５' in k:
        units = 1398  # 居宅2
    elif '支' in k:
        units = 442   # 介護予防（委託等）
    else:
        units = 0
    return int(units * unit_price)

# 拠点判別ロジック
def get_branch(cm_name):
    cm_name = str(cm_name)
    # 中村、鈴木、西野、鈴木（鈴木さんは2人いる想定で「鈴木」が含まれれば本所）
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
    # 拠点と報酬を追加
    df['拠点'] = df['ケアマネ'].apply(get_branch)
    df['概算報酬'] = df['要介護度'].apply(estimate_revenue)
    return df

df_old = process_data(old_file)
df_new = process_data(new_file)

if df_new is not None:
    # --- 全体サマリー ---
    st.divider()
    total_rev = df_new['概算報酬'].sum()
    total_users = len(df_new)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("総利用者数", f"{total_users} 名")
    c2.metric("総概算報酬", f"¥{total_rev:,}")
    
    if df_old is not None:
        new_names = set(df_new['利用者名']) - set(df_old['利用者名'])
        lost_names = set(df_old['利用者名']) - set(df_new['利用者名'])
        diff = len(new_names) - len(lost_names)
        c3.metric("前月比増減", f"{diff:+} 名", f"新規:{len(new_names)} / 終了:{len(lost_names)}")

    # --- 拠点別分析 ---
    st.header("📍 拠点別 実績比較")
    branch_summary = df_new.groupby('拠点').agg({
        '利用者名': 'count',
        '概算報酬': 'sum'
    }).reset_index()
    branch_summary.columns = ['拠点', '利用者数', '概算報酬合計']

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        fig_b1 = px.bar(branch_summary, x='拠点', y='利用者数', text='利用者数', title="拠点別 利用者数", color='拠点')
        st.plotly_chart(fig_b1, use_container_width=True)
    with col_b2:
        fig_b2 = px.bar(branch_summary, x='拠点', y='概算報酬合計', text='概算報酬合計', title="拠点別 概算報酬", color='拠点')
        st.plotly_chart(fig_b2, use_container_width=True)

    # --- ケアマネ別報酬ランキング ---
    st.header("🏆 ケアマネ別 概算報酬ランキング")
    cm_summary = df_new.groupby(['ケアマネ', '拠点']).agg({
        '利用者名': 'count',
        '概算報酬': 'sum'
    }).reset_index().sort_values('概算報酬', ascending=False)
    
    fig_cm_rev = px.bar(cm_summary, x='ケアマネ', y='概算報酬', text='概算報酬', color='拠点', 
                        title="ケアマネジャー別 売上貢献度（概算）")
    st.plotly_chart(fig_cm_rev, use_container_width=True)

    # --- 担当者詳細ドリルダウン ---
    st.header("🔍 担当者別 詳細データ")
    selected_cm = st.selectbox("詳しく見たい担当者を選択してください", ["-- 選択してください --"] + list(cm_summary['ケアマネ'].unique()))

    if selected_cm != "-- 選択してください --":
        person_df = df_new[df_new['ケアマネ'] == selected_cm]
        p_count = len(person_df)
        p_rev = person_df['概算報酬'].sum()
        
        st.subheader(f"【{selected_cm}】さんの担当状況")
        st.write(f"担当件数: {p_count}件 / 概算月間報酬: ¥{p_rev:,}")
        st.table(person_df[['利用者名', '要介護度', '保険者', '概算報酬', 'メモ']])

else:
    st.info("CSVファイルをアップロードしてください。")

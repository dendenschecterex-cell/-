import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="ケアマネ業務分析", layout="wide")
st.title("📊 居宅支援・お客さん増減分析")

col_a, col_b = st.columns(2)
with col_a:
    old_file = st.file_uploader("1. 先月のCSVを選択", type="csv")
with col_b:
    new_file = st.file_uploader("2. 今月のCSVを選択", type="csv")

def load_nursing_csv(file):
    if file is None: return None
    try:
        df = pd.read_csv(file, encoding='utf-8')
    except:
        df = pd.read_csv(file, encoding='shift-jis')
    return df.dropna(subset=['利用者名'])

df_old = load_nursing_csv(old_file)
df_new = load_nursing_csv(new_file)

if df_new is not None:
    st.divider()
    total_count = len(df_new)
    if df_old is not None:
        old_names = set(df_old['利用者名'])
        new_names = set(df_new['利用者名'])
        shinki = new_names - old_names
        shuryo = old_names - new_names
        c1, c2, c3 = st.columns(3)
        c1.metric("総利用者数", f"{total_count} 名")
        c2.success(f"🌟 新規: {len(shinki)}名")
        c3.error(f"👋 終了: {len(shuryo)}名")
        if len(shinki) > 0: st.info(f"新規: {', '.join(list(shinki))}")
        if len(shuryo) > 0: st.warning(f"終了: {', '.join(list(shuryo))}")
    else:
        st.metric("総利用者数", f"{total_count} 名")

    st.divider()
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        cm_counts = df_new['ケアマネ'].fillna('未設定').value_counts().reset_index()
        cm_counts.columns = ['ケアマネ', '件数']
        st.plotly_chart(px.bar(cm_counts, x='ケアマネ', y='件数', text='件数', title="担当者別件数"), use_container_width=True)
    with col_g2:
        care_counts = df_new['要介護度'].fillna('不明').value_counts().reset_index()
        care_counts.columns = ['要介護度', '人数']
        st.plotly_chart(px.pie(care_counts, values='人数', names='要介護度', hole=0.4, title="介護度割合"), use_container_width=True)
    st.subheader("🔍 利用者名簿")
    st.dataframe(df_new[['利用者名', 'ケアマネ', '要介護度', 'メモ']], use_container_width=True)
else:
    st.info("CSVファイルをアップロードしてください。")

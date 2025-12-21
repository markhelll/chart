import streamlit as st
import pandas as pd
import altair as alt
import datetime

# ==========================================
# 👇 ここにスプレッドシートのURL（CSV形式）を貼る
CSV_URL = "https://docs.google.com/spreadsheets/d/e/xxxxx...../pub?output=csv"
# ==========================================

st.set_page_config(page_title="My金利ウォッチ", page_icon="🏦", layout="wide")

st.title("🏦 My金利ウォッチ (Pro)")
st.caption("データベース: Googleスプレッドシート (毎日自動蓄積中)")

# データの読み込み関数
@st.cache_data(ttl=600)
def load_data():
    try:
        df = pd.read_csv(CSV_URL)
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except Exception as e:
        return None

df = load_data()

if df is None:
    st.error("データの読み込みに失敗しました。URLを確認してください。")
else:
    # --- サイドバー設定 ---
    st.sidebar.header("表示設定")
    
    # 時間足の選択
    timeframe = st.sidebar.radio(
        "期間（足）を選択",
        ["分足 (Raw)", "日足 (Daily)", "週足 (Weekly)", "年足 (Yearly)"],
        index=1
    )
    st.sidebar.info("※銀行金利は分単位では変動しないため、「分足」は記録された全ての生データを表示します。")

    # --- データの加工 ---
    df_sorted = df.sort_values('Date')
    df_indexed = df_sorted.set_index('Date')

    if "週足" in timeframe:
        df_display = df_indexed.resample('W').last().reset_index()
    elif "年足" in timeframe:
        df_display = df_indexed.resample('A').last().reset_index()
    elif "分足" in timeframe:
        # 生データそのまま
        df_display = df_sorted
    else:
        # 日足 (重複があればその日の最終値を採用)
        df_display = df_indexed.resample('D').last().dropna().reset_index()

    # --- 1. 最新ステータス ---
    latest = df_sorted.iloc[-1]
    st.markdown(f"### 📊 現在の金利 ({latest['Date'].strftime('%Y/%m/%d')} 時点)")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("日銀政策金利", f"{latest['BOJ']}%")
    col2.metric("三菱UFJ (店頭)", f"{latest['MUFG']}%")
    col3.metric("横浜銀行 (店頭)", f"{latest['Yokohama']}%")

    # --- 2. 直近1週間の比較表 ---
    st.markdown("### 🗓 直近7日間の動き")
    last_7_days = df_sorted.tail(7).sort_values('Date', ascending=False)
    last_7_days['Date'] = last_7_days['Date'].dt.strftime('%Y-%m-%d')
    st.dataframe(last_7_days.set_index('Date'), use_container_width=True)

    # --- 3. メインチャート ---
    st.markdown(f"### 📈 長期推移チャート ({timeframe})")
    
    chart_data = df_display.melt('Date', var_name='Bank', value_name='Rate')
    
    chart = alt.Chart(chart_data).mark_line(interpolate='step-after', point=True).encode(
        x=alt.X('Date:T', title='日付'),
        y=alt.Y('Rate:Q', title='金利 (%)', scale=alt.Scale(domain=[0, 3.5])),
        color=alt.Color('Bank:N', title='銀行名'),
        tooltip=['Date:T', 'Bank', 'Rate']
    ).interactive()

    st.altair_chart(chart, use_container_width=True)

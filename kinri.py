import streamlit as st
import pandas as pd
import altair as alt

# ==========================================
# 👇 ここにURLが入っているか再確認！
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8hJRst-sZ2V_rzHW77OK5NBbDGRwJ8O7bYNoofq2l7gtqE8ZzPSUq39xPI4IDp4-q1NXdapzo-hZE/pub?output=csv"
# ==========================================

st.set_page_config(page_title="My金利ウォッチ", page_icon="🏦", layout="wide")

if st.sidebar.button("🔄 データを強制更新"):
    st.cache_data.clear()
    st.rerun()

st.title("🏦 My金利ウォッチ (Pro)")

@st.cache_data(ttl=600)
def load_data():
    try:
        df = pd.read_csv(CSV_URL)
        # データが空っぽの場合の対策
        if df.empty:
            return None
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except Exception:
        return None

df = load_data()

# --- ここで「データがあるか？」をチェック ---
if df is None or df.empty:
    st.error("⚠️ データが読み込めませんでした。")
    st.info("以下の2点を確認してください：")
    st.markdown("""
    1. **URLは正しいですか？** (`output=csv` で終わる公開用URL)
    2. **スプレッドシートは空っぽではないですか？** (1行目に `Date,BOJ...` という見出しが必要です)
    """)
else:
    # データがある場合のみ処理を実行
    df_sorted = df.sort_values('Date')
    
    # 1. 最新ステータス
    latest = df_sorted.iloc[-1] # ← ここでエラーが出ていた！
    st.markdown(f"### 📊 現在の金利 ({latest['Date'].strftime('%Y/%m/%d')} 時点)")
    col1, col2, col3 = st.columns(3)
    col1.metric("日銀政策金利", f"{latest['BOJ']}%")
    col2.metric("三菱UFJ", f"{latest['MUFG']}%")
    col3.metric("横浜銀行", f"{latest['Yokohama']}%")

    st.divider()

    # 2. 直近リスト
    st.subheader("🗓 直近の金利履歴")
    last_7_days = df_sorted.tail(7).sort_values('Date', ascending=False)
    last_7_days['Date'] = last_7_days['Date'].dt.strftime('%Y-%m-%d')
    st.dataframe(last_7_days.set_index('Date'), use_container_width=True)

    st.divider()

    # 3. チャート
    st.sidebar.header("チャート設定")
    timeframe = st.sidebar.radio("期間（足）", ["分足", "日足", "週足", "年足"], index=1)

    df_indexed = df_sorted.set_index('Date')
    if "週足" in timeframe:
        df_display = df_indexed.resample('W').last().reset_index()
    elif "年足" in timeframe:
        df_display = df_indexed.resample('A').last().reset_index()
    elif "分足" in timeframe:
        df_display = df_sorted
    else:
        df_display = df_indexed.resample('D').last().dropna().reset_index()

    st.subheader(f"📈 推移チャート ({timeframe})")
    chart_data = df_display.melt('Date', var_name='Bank', value_name='Rate')
    chart = alt.Chart(chart_data).mark_line(interpolate='step-after', point=True).encode(
        x=alt.X('Date:T', title='日付'),
        y=alt.Y('Rate:Q', title='金利 (%)'),
        color=alt.Color('Bank:N', title='銀行名'),
        tooltip=['Date', 'Bank', 'Rate']
    ).interactive()
    st.altair_chart(chart, use_container_width=True)

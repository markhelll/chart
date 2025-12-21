import streamlit as st
import pandas as pd
import altair as alt

# ==========================================
# 👇 ここにスプレッドシートのURL（CSV形式）を貼る
# ※「.../pub?output=csv」で終わるURLです
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8hJRst-sZ2V_rzHW77OK5NBbDGRwJ8O7bYNoofq2l7gtqE8ZzPSUq39xPI4IDp4-q1NXdapzo-hZE/pub?output=csv"
# ==========================================

st.set_page_config(page_title="My金利ウォッチ", page_icon="🏦", layout="wide")

# --- 画面右上に「キャッシュクリア」ボタンを配置 ---
if st.sidebar.button("🔄 データを強制更新"):
    st.cache_data.clear()
    st.rerun()

st.title("🏦 My金利ウォッチ (Pro)")
st.caption("データベース: Googleスプレッドシート")

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
    st.info("ヒント: スプレッドシートの「ウェブに公開」で「CSV」形式を選びましたか？")
else:
    df_sorted = df.sort_values('Date')
    
    # --- 1. 最新ステータス (3つの数字) ---
    latest = df_sorted.iloc[-1]
    st.markdown(f"### 📊 現在の金利 ({latest['Date'].strftime('%Y/%m/%d')} 時点)")
    col1, col2, col3 = st.columns(3)
    col1.metric("日銀政策金利", f"{latest['BOJ']}%")
    col2.metric("三菱UFJ (店頭)", f"{latest['MUFG']}%")
    col3.metric("横浜銀行 (店頭)", f"{latest['Yokohama']}%")

    st.divider() # 区切り線

    # --- 2. 直近7日間の比較リスト (ここに配置！) ---
    st.subheader("🗓 直近の金利履歴 (New!)")
    st.caption("※直近7回分の記録を表示しています")
    
    # 最新7件を取得して、新しい日付順に並べ替え
    last_7_days = df_sorted.tail(7).sort_values('Date', ascending=False)
    
    # 日付を見やすく整形
    last_7_days['Date'] = last_7_days['Date'].dt.strftime('%Y-%m-%d')
    
    # リスト表示
    st.dataframe(
        last_7_days.set_index('Date'), 
        use_container_width=True
    )

    st.divider() # 区切り線

    # --- 3. チャート設定と表示 ---
    st.sidebar.header("チャート設定")
    timeframe = st.sidebar.radio(
        "期間（足）を選択",
        ["分足 (Raw)", "日足 (Daily)", "週足 (Weekly)", "年足 (Yearly)"],
        index=1
    )

    # データの加工（足の変換）
    df_indexed = df_sorted.set_index('Date')
    if "週足" in timeframe:
        df_display = df_indexed.resample('W').last().reset_index()
    elif "年足" in timeframe:
        df_display = df_indexed.resample('A').last().reset_index()
    elif "分足" in timeframe:
        df_display = df_sorted
    else:
        df_display = df_indexed.resample('D').last().dropna().reset_index()

    st.subheader(f"📈 長期推移チャート ({timeframe})")
    
    chart_data = df_display.melt('Date', var_name='Bank', value_name='Rate')
    
    chart = alt.Chart(chart_data).mark_line(interpolate='step-after', point=True).encode(
        x=alt.X('Date:T', title='日付'),
        y=alt.Y('Rate:Q', title='金利 (%)', scale=alt.Scale(domain=[0, 3.5])),
        color=alt.Color('Bank:N', title='銀行名'),
        tooltip=['Date:T', 'Bank', 'Rate']
    ).interactive()

    st.altair_chart(chart, use_container_width=True)

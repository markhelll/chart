import streamlit as st
import pandas as pd
import altair as alt

# ==========================================
# 👇 スプレッドシートのCSV URL（変更なし）
CSV_URL = "https://docs.google.com/spreadsheets/d/e/xxxxx...../pub?output=csv"
# ==========================================

st.set_page_config(page_title="My金利ウォッチ", page_icon="🏦")

st.title("🏦 My金利ウォッチ (リアル推移版)")

# サイドバー設定
st.sidebar.header("表示設定")

# 1. 時間足の選択
timeframe = st.sidebar.radio(
    "期間（足）を選択",
    ["日足 (Daily)", "週足 (Weekly)", "月足 (Monthly)", "年足 (Yearly)"],
    index=0
)

# データの読み込み関数
@st.cache_data(ttl=600) # 10分ごとに更新
def load_data():
    try:
        # CSVを読み込む
        df = pd.read_csv(CSV_URL)
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except Exception as e:
        return None

# データ処理
raw_df = load_data()

if raw_df is None:
    st.error("データの読み込みに失敗しました。URLを確認してください。")
else:
    # --- データの再サンプリング（足の変更）処理 ---
    # まず日付をインデックスにする
    df_indexed = raw_df.set_index('Date')
    
    if "週足" in timeframe:
        # 週ごとの最終データを採用
        df_resampled = df_indexed.resample('W').last().reset_index()
    elif "月足" in timeframe:
        # 月ごとの最終データ
        df_resampled = df_indexed.resample('M').last().reset_index()
    elif "年足" in timeframe:
        # 年ごとの最終データ
        df_resampled = df_indexed.resample('A').last().reset_index()
    else:
        # 日足（そのまま）
        df_resampled = raw_df.copy()
        # ※金利は「分単位」で変わらないため、分足は日足と同じ扱いにしています

    # 最新データの表示（一番下の行）
    latest = df_resampled.iloc[-1]
    
    st.markdown(f"### 現在の金利 ({latest['Date'].strftime('%Y/%m/%d')} 時点)")
    col1, col2, col3 = st.columns(3)
    col1.metric("日銀政策金利", f"{latest['BOJ']}%")
    col2.metric("三菱UFJ (店頭)", f"{latest['MUFG']}%")
    col3.metric("横浜銀行 (店頭)", f"{latest['Yokohama']}%")

    # --- チャート描画 ---
    st.subheader(f"📈 金利推移チャート ({timeframe})")
    
    # Altair用にデータを変形
    chart_data = df_resampled.melt('Date', var_name='Bank', value_name='Rate')
    
    # 折れ線グラフ (step補間で金利特有の階段状の動きを表現)
    chart = alt.Chart(chart_data).mark_line(interpolate='step-after', point=True).encode(
        x=alt.X('Date:T', title='日付'),
        y=alt.Y('Rate:Q', title='金利 (%)', scale=alt.Scale(domain=[0, 3.5])),
        color=alt.Color('Bank:N', title='銀行名'),
        tooltip=[
            alt.Tooltip('Date:T', format='%Y-%m-%d'), 
            'Bank', 
            'Rate'
        ]
    ).interactive()

    st.altair_chart(chart, use_container_width=True)

    # 生データ確認用
    with st.expander("詳細データ履歴"):
        st.dataframe(df_resampled.sort_values('Date', ascending=False))

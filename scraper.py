import streamlit as st
import pandas as pd
import altair as alt

# ==========================================
# 👇 ここにさっきコピーしたURLを貼り付ける
# （" " の引用符は消さないで、その中に入れてください）
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8hJRst-sZ2V_rzHW77OK5NBbDGRwJ8O7bYNoofq2l7gtqE8ZzPSUq39xPI4IDp4-q1NXdapzo-hZE/pub?output=csv"
# ==========================================

st.set_page_config(page_title="My金利ウォッチ", page_icon="🏦")

st.title("🏦 My金利ウォッチ")
st.caption(f"データソース: Googleスプレッドシート (自動更新)")

# データの読み込み
@st.cache_data(ttl=3600) # 1時間キャッシュして表示を高速化
def load_data():
    try:
        df = pd.read_csv(CSV_URL)
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except Exception as e:
        return None

df = load_data()

if df is None:
    st.error("データの読み込みに失敗しました。URLが正しいか確認してください。")
    st.info("ヒント: スプレッドシートの「ウェブに公開」で「CSV」形式を選びましたか？")
else:
    # 最新データの表示
    latest = df.iloc[-1]
    
    # 見やすく3列で表示
    col1, col2, col3 = st.columns(3)
    col1.metric("日銀政策金利", f"{latest['BOJ']}%")
    col2.metric("三菱UFJ (変動)", f"{latest['MUFG']}%", delta_color="inverse")
    col3.metric("横浜銀行", f"{latest['Yokohama']}%", delta_color="inverse")

    # チャートの描画
    st.subheader("📈 金利推移チャート")
    
    # データをチャート用に変形（ピボット解除）
    chart_data = df.melt('Date', var_name='Bank', value_name='Rate')
    
    # インタラクティブなチャートを作成
    chart = alt.Chart(chart_data).mark_line(point=True).encode(
        x='Date:T',
        y=alt.Y('Rate:Q', scale=alt.Scale(domain=[0, 3.0])), # 縦軸の範囲（0%〜3%）
        color='Bank:N',
        tooltip=['Date', 'Bank', 'Rate']
    ).interactive()
    
    st.altair_chart(chart, use_container_width=True)

    # 生データの確認
    with st.expander("詳細データを見る"):
        st.dataframe(df.sort_values('Date', ascending=False))
        
    # 手動更新ボタン
    if st.button("最新データを再読み込み"):
        st.cache_data.clear()
        st.rerun()

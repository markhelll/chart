import pandas as pd
import datetime
import os
import random

# 保存するファイル名
DATA_FILE = "interest_rate_history.csv"

def fetch_rates():
    # 本来はここで requests と BeautifulSoup で銀行サイトを見に行きます
    # まずは仕組みが動くか確認するため、昨日の数字に少し変化を加えるダミーにします
    
    today = datetime.date.today()
    
    # テスト用ダミーデータ（本番ではここをスクレイピングコードに書き換えます）
    return {
        "Date": today,
        "BOJ (Policy)": 0.50,
        "MUFG (Variable)": 2.475,
        "Yokohama (Variable)": 2.675 + random.choice([0, 0.01, -0.01]), # 微妙に変動させる
        "Johoku (Prime)": 1.675
    }

def main():
    print("データ収集を開始します...")
    new_data = fetch_rates()
    
    # 既存データの読み込みまたは新規作成
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
    else:
        df = pd.DataFrame(columns=new_data.keys())
    
    # 日付の重複チェック（念のため文字列で比較）
    df['Date'] = df['Date'].astype(str)
    today_str = str(new_data["Date"])
    
    if today_str in df['Date'].values:
        print(f"{today_str} のデータは既にあります。スキップします。")
    else:
        # 新しいデータを追加
        new_row = pd.DataFrame([new_data])
        # concatを使って結合
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        print(f"データを追加保存しました: {new_data}")

if __name__ == "__main__":
    main()

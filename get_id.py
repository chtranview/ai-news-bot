"""
get_id.py — 臨時 Flask Webhook 伺服器，用來取得 LINE User ID。

使用方式：
  1. 執行: .venv\Scripts\python get_id.py
  2. 用 ngrok 或 localtunnel 暴露 port 5000
  3. 在 LINE Developers Console 設定 Webhook URL 為 https://<your-url>/callback
  4. 傳訊息給你的 LINE Bot，即可在終端機看到 User ID
"""
from flask import Flask, request
import json

app = Flask(__name__)

@app.route("/callback", methods=["POST"])
def callback():
    print("\n========== INCOMING WEBHOOK ==========")
    body = request.get_data(as_text=True)
    print(f"Request Body: {body}")
    try:
        data = json.loads(body)
        for event in data.get("events", []):
            user_id = event.get("source", {}).get("userId")
            if user_id:
                print("\n" + "=" * 40)
                print(f"YOUR USER ID IS: {user_id}")
                print("=" * 40 + "\n")
            else:
                print("No User ID found in this event.")
    except Exception as e:
        print(f"Error parsing JSON: {e}")
    return "OK"

if __name__ == "__main__":
    print("Starting Webhook Server on port 5000...")
    print("Waiting for LINE events...")
    app.run(port=5000)

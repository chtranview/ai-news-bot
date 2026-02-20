# QUICKSTARTUP — 5 分鐘部署 ai-news-bot

## Step 1：安裝環境

```powershell
cd C:\Users\chtra\.gemini\antigravity\workspace\ai-news-bot
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

---

## Step 2：設定環境變數

編輯 `.env` 填入你的金鑰：

```ini
GEMINI_API_KEY=你的金鑰          # https://aistudio.google.com/app/apikey
LINE_CHANNEL_ACCESS_TOKEN=你的token
LINE_USER_ID=你的userId
```

> 還沒有 LINE User ID？先跳到 Step 2.5

### Step 2.5（選用）：取得 LINE User ID

```powershell
# 1. 啟動 Webhook 伺服器
.venv\Scripts\python get_id.py

# 2. 另開終端，用 ngrok 暴露（需安裝 ngrok）
ngrok http 5000
```
在 LINE Developers Console 設定 Webhook URL 為 `https://<ngrok網址>/callback`，  
傳訊息給 Bot，終端機即顯示 `YOUR USER ID IS: Uxxxxxxxx`。

---

## Step 3：自我測試（建議先跑）

```powershell
.venv\Scripts\python self_test.py --skip-network
```

預期結果：files、modules 顯示 `[PASS]`，env 顯示 `[WARN]`（未載入 .env，正常）。

---

## Step 4：Dry-run 驗證流程

```powershell
.venv\Scripts\python main.py --dry-run
```

預期結果：印出 10 則繁體中文假摘要，結尾顯示 `[DRY-RUN] LINE message not sent.`

---

## Step 5：完整自我測試（含 LINE 推送）

```powershell
# 先設定環境變數（本次終端機生效）
$env:GEMINI_API_KEY="你的金鑰"
$env:LINE_CHANNEL_ACCESS_TOKEN="你的token"
$env:LINE_USER_ID="你的userId"

# 完整測試含 LINE 推送
.venv\Scripts\python self_test.py --send-test --message "ai-news-bot 部署測試成功"
```

預期結果：LINE 收到測試訊息，終端顯示 `[PASS] send-test`。

---

## Step 6：正式執行

```powershell
.venv\Scripts\python main.py
```

預期結果：LINE 收到今日 AI 新聞摘要（繁體中文，10 則）。

---

## Step 7：部署到 GitHub Actions

1. 推送專案到 GitHub。
2. 設定 Repo Secrets（Settings → Secrets and variables → Actions）：
   - `GEMINI_API_KEY`
   - `LINE_CHANNEL_ACCESS_TOKEN`
   - `LINE_USER_ID`
3. 到 **Actions** → **Daily AI News** → **Run workflow** 手動觸發一次。
4. 確認 Actions 狀態為 `Success`、LINE 收到真實新聞摘要。
5. 之後每日台北時間 06:00 自動執行。

---

## 成功判斷清單

| 項目 | 確認方式 |
|------|----------|
| ✅ self_test 通過 | `self_test.py --skip-network` 顯示 `RESULT: PASS` |
| ✅ dry-run 正常 | `main.py --dry-run` 印出繁中假摘要 |
| ✅ LINE 測試訊息 | `--send-test` 後 LINE 收到訊息 |
| ✅ 正式執行 | `main.py` 後 LINE 收到真實新聞 |
| ✅ Actions 成功 | GitHub Actions 最近執行狀態為 `Success` |

---

## 指令速查表

```powershell
# 自我測試
.venv\Scripts\python self_test.py
.venv\Scripts\python self_test.py --skip-network
.venv\Scripts\python self_test.py --skip-dry-run
.venv\Scripts\python self_test.py --send-test
.venv\Scripts\python self_test.py --send-test --message "自訂訊息"

# 主程式
.venv\Scripts\python main.py --dry-run
.venv\Scripts\python main.py

# 工具
.venv\Scripts\python get_id.py
```
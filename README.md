# ai-news-bot

每天早上 6 點（台北時間）自動搜尋 10 則「AI 人工智慧」熱門新聞，使用 Gemini + Google Search Grounding 生成**繁體中文**摘要，並透過 LINE Messaging API 推送。

## 功能

- **Google Search Grounding**：Gemini 直接上網搜尋，無需額外爬蟲
- **繁體中文摘要**：Prompt 明確要求中文輸出，直接發送至 LINE
- **tenacity 自動重試**：API 呼叫失敗自動重試（最多 5 次）
- **`--dry-run` 模式**：本機驗證流程，不發送 LINE、不需 API Key
- **`self_test.py`**：5 步驟自我檢查（檔案、模組、環境變數、網路、dry-run）
- **`get_id.py`**：Flask Webhook 工具，快速取得 LINE User ID
- **GitHub Actions**：每日台北時間 06:00 自動執行

## 專案結構

```
ai-news-bot/
├── main.py                            # 主程式
├── self_test.py                       # 自我測試工具
├── get_id.py                          # 取得 LINE User ID 工具
├── requirements.txt                   # Python 套件
├── .env                               # 環境變數（本機用，勿 commit）
├── README.md
├── QUICKSTARTUP.md
└── .github/
    └── workflows/
        └── daily_news.yml             # GitHub Actions 排程
```

## 環境需求

- Python 3.10+
- 套件：見 `requirements.txt`（google-genai、tenacity、line-bot-sdk、flask）
- 環境變數（Secrets）：
  - `GEMINI_API_KEY`（Gemini API — 取得：[Google AI Studio](https://aistudio.google.com/app/apikey)）
  - `LINE_CHANNEL_ACCESS_TOKEN`（[LINE Developers Console](https://developers.line.biz/console/)）
  - `LINE_USER_ID`

---

## 本機啟動（Windows）

### 1. 建立虛擬環境

```powershell
python -m venv .venv
```

### 2. 安裝依賴

```powershell
.venv\Scripts\pip install -r requirements.txt
```

### 3. 設定 `.env`（建議方式）

```ini
GEMINI_API_KEY=你的金鑰
LINE_CHANNEL_ACCESS_TOKEN=你的token
LINE_USER_ID=你的userId
```

或直接設定目前終端機環境變數：

```powershell
$env:GEMINI_API_KEY="你的金鑰"
$env:LINE_CHANNEL_ACCESS_TOKEN="你的token"
$env:LINE_USER_ID="你的userId"
```

### 4. 執行

```powershell
# 完整執行（搜尋新聞 + Gemini 摘要 + 發送 LINE）
.venv\Scripts\python main.py

# Dry-run（不需 API Key，不發送 LINE，印出假摘要驗證流程）
.venv\Scripts\python main.py --dry-run
```

---

## 自我測試（self_test.py）

### 基本檢查（檔案 + 模組 + 環境變數 + 網路 + dry-run）

```powershell
.venv\Scripts\python self_test.py
```

### 略過網路檢查（離線環境）

```powershell
.venv\Scripts\python self_test.py --skip-network
```

### 略過 dry-run 測試

```powershell
.venv\Scripts\python self_test.py --skip-dry-run
```

### 含 LINE 推送測試（需設定環境變數）

```powershell
.venv\Scripts\python self_test.py --send-test
```

### 自訂測試訊息

```powershell
.venv\Scripts\python self_test.py --send-test --message "ai-news-bot 部署測試成功"
```

### 預期輸出

```
========================================
  ai-news-bot self test
========================================

[1/5] files...
[PASS] file: main.py
[PASS] file: requirements.txt
[PASS] file: .github/workflows/daily_news.yml

[2/5] modules...
[PASS] module: tenacity
[PASS] module: google.genai
[PASS] module: linebot

[3/5] env...
[PASS] env: GEMINI_API_KEY = AIzaSy...
[PASS] env: LINE_CHANNEL_ACCESS_TOKEN = xyz789...
[PASS] env: LINE_USER_ID = U1234a...

[4/5] connectivity...
[PASS] connectivity: Gemini API (HTTP 200)
[PASS] connectivity: LINE API (HTTP 200)
[PASS] connectivity: Google (HTTP 200)

[5/5] dry-run...
[PASS] dry-run: main.py --dry-run ok

========================================
  RESULT: PASS
========================================
```

---

## 取得 LINE User ID（get_id.py）

1. 啟動 Flask Webhook 伺服器：
   ```powershell
   .venv\Scripts\python get_id.py
   ```
2. 用 [ngrok](https://ngrok.com) 暴露 port 5000：
   ```powershell
   ngrok http 5000
   ```
3. 在 LINE Developers Console → Messaging API → Webhook URL 填入 ngrok 網址 + `/callback`
4. 傳訊息給 Bot，終端機即顯示 `YOUR USER ID IS: Uxxxxxxxx`

---

## GitHub Actions 部署

1. 將專案推到 GitHub。
2. 進入 Repo → **Settings** → **Secrets and variables** → **Actions**。
3. 新增 Secrets：
   - `GEMINI_API_KEY`
   - `LINE_CHANNEL_ACCESS_TOKEN`
   - `LINE_USER_ID`
4. 到 **Actions** 頁面手動執行 `Daily AI News`（`workflow_dispatch`）確認成功。
5. 排程會於每日台北時間 06:00（UTC 22:00）自動執行。

---

## 指令速查表

| 指令 | 說明 |
|------|------|
| `.venv\Scripts\python main.py` | 完整執行（搜尋 + 摘要 + LINE 推送） |
| `.venv\Scripts\python main.py --dry-run` | 不發 LINE、缺 API Key 用假摘要 |
| `.venv\Scripts\python self_test.py` | 完整自我檢查 |
| `.venv\Scripts\python self_test.py --skip-network` | 略過網路連線檢查 |
| `.venv\Scripts\python self_test.py --skip-dry-run` | 略過 dry-run 測試 |
| `.venv\Scripts\python self_test.py --send-test` | 含 LINE 推送測試 |
| `.venv\Scripts\python get_id.py` | 啟動 Webhook 取得 LINE User ID |

---

## 常見問題

| 問題 | 解法 |
|------|------|
| 沒收到 LINE 訊息 | 檢查 `LINE_CHANNEL_ACCESS_TOKEN`、`LINE_USER_ID` |
| Gemini 呼叫失敗 | 檢查 `GEMINI_API_KEY` 是否有效、配額是否用盡 |
| Actions 失敗 | 到 Actions log 查看各步驟輸出，確認 Secrets 設定正確 |
| `--dry-run` 無輸出 | 確認在 `ai-news-bot/` 目錄下執行 |
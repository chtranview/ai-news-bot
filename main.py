import os
import sys
import argparse
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
from linebot import LineBotApi
from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@retry(
    retry=retry_if_exception_type(Exception),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    stop=stop_after_attempt(5)
)
def _call_gemini(client, model_id, prompt):
    """呼叫 Gemini API，附帶 Google Search Grounding（有 tenacity 自動重試）。"""
    return client.models.generate_content(
        model=model_id,
        contents=prompt,
        config=GenerateContentConfig(
            tools=[Tool(google_search=GoogleSearch())],
            response_modalities=["TEXT"],
        )
    )

def _clean_summary(text: str) -> str:
    """去除 Gemini 可能輸出的開場白，直接從固定標題行開始。"""
    header = "以下是過去 24 小時內的熱門人工智慧(AI) 新聞摘要："
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if header in line:
            return "\n".join(lines[i:]).strip()
    # 找不到標題行時，去除空行和不含數字編號的前置行
    for i, line in enumerate(lines):
        if line.strip() and (line.strip()[0].isdigit() or line.strip().startswith("以下")):
            return "\n".join(lines[i:]).strip()
    return text.strip()

def generate_news_summary():
    """使用 Gemini + Google Search Grounding 生成 AI 新聞摘要（繁體中文）。"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logging.error("GEMINI_API_KEY not found.")
        return "Error: Gemini API key missing."

    logging.info("Initializing Gemini client...")
    client = genai.Client(api_key=api_key)
    model_id = "gemini-2.0-flash"

    prompt = (
        "你是一個新聞播報機器人。請直接輸出內容，禁止加任何開場白、問候語、確認句或說明文字。"
        "請搜尋過去 24 小時內最熱門的 10 則 AI（人工智慧）新聞。"
        "嚴格以繁體中文輸出，不含英文標題或連結。"
        "輸出格式如下，第一行固定為：\n"
        "以下是過去 24 小時內的熱門人工智慧(AI) 新聞摘要：\n"
        "接著以編號列表 1-10 列出每則新聞的繁體中文摘要，每則一行，簡潔扼要。"
        "禁止輸出『好的』、『請稍等』等任何開場白，直接從標題行開始。"
    )

    logging.info("Generating content with Google Search Grounding...")
    try:
        response = _call_gemini(client, model_id, prompt)
        if response.text:
            return _clean_summary(response.text)
        logging.warning("No text returned in response.")
        return "No news summary generated."
    except Exception as e:
        logging.error(f"Gemini API error (after retries): {e}")
        return "Error generating summary."

def make_fallback_summary():
    """Dry-run 模式下、無 API key 時使用的本地假摘要。"""
    return (
        "以下是過去 24 小時內的熱門人工智慧(AI) 新聞摘要：\n"
        "（DRY-RUN 模式：未設定 GEMINI_API_KEY，使用本地假摘要）\n\n"
        "1. OpenAI 發布新一代模型，效能大幅提升\n"
        "2. Google DeepMind 在蛋白質預測取得突破\n"
        "3. 台灣企業加速導入 AI 應用\n"
        "4. 歐盟 AI 法案正式生效，影響全球科技業\n"
        "5. NVIDIA 發表新一代 AI 晶片架構\n"
        "6. Meta 開源新大型語言模型\n"
        "7. 微軟 Copilot 整合更多辦公應用\n"
        "8. AI 生成影片技術持續進化\n"
        "9. 醫療 AI 輔助診斷準確率創新高\n"
        "10. AI 資安威脅引發各國關注"
    )

def send_line_message(message):
    """推播訊息至 LINE。"""
    channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.getenv("LINE_USER_ID")
    if not channel_access_token or not user_id:
        logging.error("Line API credentials missing.")
        return
    line_bot_api = LineBotApi(channel_access_token)
    try:
        line_bot_api.push_message(user_id, TextSendMessage(text=message))
        logging.info("Message sent to Line successfully.")
    except LineBotApiError as e:
        logging.error(f"Line API error: {e}")

def main():
    parser = argparse.ArgumentParser(description="AI News Bot")
    parser.add_argument("--dry-run", action="store_true", help="只印出摘要，不發 LINE 訊息")
    args = parser.parse_args()

    logging.info("Starting AI News Bot...")

    if args.dry_run and not os.getenv("GEMINI_API_KEY"):
        logging.info("[DRY-RUN] GEMINI_API_KEY not set, using fallback summary.")
        summary = make_fallback_summary()
    else:
        summary = generate_news_summary()

    logging.info("Summary generated.")
    print(summary)

    if args.dry_run:
        print("\n[DRY-RUN] LINE message not sent.")
        return

    if summary and "Error" not in summary:
        send_line_message(summary)
    else:
        logging.warning("Skipping Line message due to error or empty summary.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

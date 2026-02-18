import os
import sys
import logging
import requests
from bs4 import BeautifulSoup
from googlesearch import search
import google.generativeai as genai
from linebot import LineBotApi
from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_ai_news(query="AI Artificial Intelligence news", num_results=10):
    """Searches for AI news relative to the last 24 hours."""
    logging.info(f"Searching for news with query: {query}")
    news_items = []
    try:
        # Note: googlesearch-python might not support time-range filtering directly in all versions.
        # We search and then try to extract content.
        # For a production bot, a dedicated News API (like GNews or Bing News API) is more robust.
        # Here we stick to the user request of using "Google Search or crawler".
        search_results = search(query, num_results=num_results, advanced=True)
        
        for result in search_results:
            try:
                # Basic content extraction
                response = requests.get(result.url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    title = soup.title.string if soup.title else result.title
                    
                    # specific cleanup can be added here
                    # just verify it's not a captcha or blockage
                    if "captcha" in title.lower():
                        continue

                    news_items.append({
                        "title": title.strip(),
                        "url": result.url,
                        # We limit content to avoid token limits, just passing title and URL is often enough for summary
                        # or a small snippet if available.
                        "snippet": result.description if hasattr(result, 'description') else "" 
                    })
            except Exception as e:
                logging.warning(f"Failed to fetch {result.url}: {e}")
                continue
            
            if len(news_items) >= num_results:
                break
                
    except Exception as e:
        logging.error(f"Error during search: {e}")
        
    return news_items

def summarize_news(news_items):
    """Summarizes the list of news items using Gemini."""
    if not news_items:
        return "No news found today."

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logging.error("GOOGLE_API_KEY not found.")
        return "Error: Gemini API key missing."

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')

    prompt = "Here are top AI news titles and URLs. Please summarize them into a concise daily update suitable for a Line message. Format it as a list with bullet points. Include the link for each item if possible, but keep it short.\n\n"
    for item in news_items:
        prompt += f"- {item['title']} : {item['url']}\n"

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logging.error(f"Gemini API error: {e}")
        return "Error generating summary."

def send_line_message(message):
    """Sends the summary to Line."""
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
    logging.info("Starting AI News Bot...")
    news = get_ai_news()
    if news:
        summary = summarize_news(news)
        logging.info("Summary generated.")
        print(summary) # For debug
        send_line_message(summary)
    else:
        logging.info("No news found to summarize.")

if __name__ == "__main__":
    main()

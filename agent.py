import requests
import feedparser
from datetime import datetime

TELEGRAM_TOKEN = "8085970857:AAFmT8XntTHOtlpelBZ6BwxympuaODGhxbE"
CHAT_ID = None

RSS_FEEDS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
    "https://www.reuters.com/technology/cryptocurrency/rss"
]

KEYWORDS = [
    "regulation", "sec", "etf", "fed", "interest rate",
    "inflation", "bank", "economy", "bitcoin", "ethereum"
]

def get_chat_id():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    r = requests.get(url).json()
    return r["result"][-1]["message"]["chat"]["id"]

def important(entry):
    text = (entry.title + entry.summary).lower()
    return any(k in text for k in KEYWORDS)

def run():
    global CHAT_ID
    if not CHAT_ID:
        CHAT_ID = get_chat_id()

    messages = []
    for feed in RSS_FEEDS:
        data = feedparser.parse(feed)
        for e in data.entries[:5]:
            if important(e):
                messages.append(f"📰 {e.title}")

    if not messages:
        messages.append("Brak istotnych newsów makro/krypto dziś.")

    msg = f"📅 {datetime.utcnow().date()}\n\n" + "\n".join(messages)

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg})

if __name__ == "__main__":
    run()

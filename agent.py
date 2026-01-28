import requests
import feedparser
from datetime import datetime, timedelta
import json
import os

# --- Twój pełny token bota ---
TELEGRAM_TOKEN = "8590798509:AAFYXHCEbsSTTZgt4TrcA3peL9UhstF33wg"
CHAT_ID = None

# --- RSS źródła ---
RSS_FEEDS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
    "https://www.reuters.com/technology/cryptocurrency/rss"
]

# --- Słowa kluczowe ---
KEYWORDS_BTC = ["bitcoin"]
KEYWORDS_ETH = ["ethereum"]
KEYWORDS_MACRO = ["regulation", "sec", "etf", "fed", "interest rate", "inflation", "bank", "economy"]

# --- Plik do przechowywania ocen wpływu tygodniowych ---
DATA_FILE = "weekly_data.json"

# --- Ocena wpływu ---
def evaluate_impact(entry):
    text = (entry.title + entry.summary).lower()
    if any(word in text for word in ["boost", "positive", "support"]):
        return 3  # wysoki wpływ
    elif any(word in text for word in ["risk", "concern", "crisis", "drop"]):
        return 1  # niski/negatywny wpływ
    else:
        return 2  # średni wpływ

def impact_icon(score):
    return {1: "🔴", 2: "🟡", 3: "🟢"}.get(score, "🟡")

# --- Krótki komentarz po polsku ---
def short_comment(entry):
    text = entry.title + " " + entry.summary
    if "bitcoin" in text.lower():
        return "Potencjalny wpływ na Bitcoin / kryptowaluty, długoterminowo istotne."
    if "ethereum" in text.lower():
        return "Potencjalny wpływ na Ethereum, długoterminowo istotne."
    return "Istotny news makroekonomiczny dla rynku krypto."

# --- Sprawdzanie ważności ---
def important(entry, keywords):
    text = (entry.title + entry.summary).lower()
    return any(k in text for k in keywords)

# --- Pobranie zapisanych ocen tygodniowych ---
def load_weekly_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

# --- Zapis ocen do pliku ---
def save_weekly_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# --- Generowanie raportu tygodniowego ---
def weekly_report(data):
    if not data:
        return "Brak newsów w tym tygodniu."

    avg_score = sum(d["score"] for d in data) / len(data)
    if avg_score >= 2.6:
        trend = "🟢 Pozytywny"
    elif avg_score <= 1.4:
        trend = "🔴 Negatywny"
    else:
        trend = "🟡 Neutralny"

    top_news = sorted(data, key=lambda x: x["score"], reverse=True)[:3]
    top_lines = [f"{impact_icon(d['score'])} {d['title']}\n➡️ {d['comment']}" for d in top_news]

    report = f"📅 Podsumowanie tygodnia ({datetime.utcnow().date() - timedelta(days=6)} - {datetime.utcnow().date()})\n\n"
    report += f"Trend rynku: {trend}\nŚrednia ocena newsów: {avg_score:.2f}/3\n\n"
    report += "Najważniejsze newsy tygodnia:\n" + "\n\n".join(top_lines)
    return report

# --- Wysyłka na Telegram ---
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": message})

# --- Uruchomienie agenta ---
def run():
    btc_news, eth_news, macro_news = [], [], []
    weekly_data = load_weekly_data()

    for feed in RSS_FEEDS:
        data = feedparser.parse(feed)
        for e in data.entries[:10]:
            score = evaluate_impact(e)
            comment = short_comment(e)
            msg_line = f"{impact_icon(score)} {e.title}\n➡️ {comment}"

            if important(e, KEYWORDS_BTC):
                btc_news.append((score, msg_line))
            elif important(e, KEYWORDS_ETH):
                eth_news.append((score, msg_line))
            elif important(e, KEYWORDS_MACRO):
                macro_news.append((score, msg_line))

            # --- dodanie do tygodniowej bazy danych ---
            if important(e, KEYWORDS_BTC + KEYWORDS_ETH + KEYWORDS_MACRO):
                weekly_data.append({
                    "score": score,
                    "title": e.title,
                    "comment": comment,
                    "date": str(datetime.utcnow().date())
                })

    # --- Sortowanie po wpływie ---
    btc_news.sort(reverse=True)
    eth_news.sort(reverse=True)
    macro_news.sort(reverse=True)
    all_news = btc_news + eth_news + macro_news
    top_news = [line for _, line in all_news[:3]] or ["Brak istotnych newsów dziś."]

    # --- Raport dzienny ---
    report = f"📅 {datetime.utcnow().date()}\n\n"
    report += "🔥 Najważniejsze newsy dnia:\n" + "\n\n".join(top_news) + "\n\n"
    if btc_news:
        report += "💎 Bitcoin:\n" + "\n\n".join([line for _, line in btc_news]) + "\n\n"
    if eth_news:
        report += "Ξ Ethereum:\n" + "\n\n".join([line for _, line in eth_news]) + "\n\n"
    if macro_news:
        report += "🌐 Makroekonomia:\n" + "\n\n".join([line for _, line in macro_news]) + "\n\n"

    # --- Podsumowanie dnia ---
    summary = "📌 Podsumowanie dnia: "
    if all_news:
        max_score = max(score for score, _ in all_news)
        if max_score == 3:
            summary += "Dzień z pozytywnymi / kluczowymi newsami dla rynku."
        elif max_score == 1:
            summary += "Dzień z ryzykiem lub negatywnymi sygnałami na rynku."
        else:
            summary += "Dzień ze średnim wpływem newsów na rynek."
    else:
        summary += "Brak istotnych newsów."

    report += summary

    # --- Wysyłka codzienna ---
    send_telegram(report)

    # --- Zapis do tygodniowego pliku ---
    save_weekly_data(weekly_data)

    # --- Cotygodniowy raport (poniedziałek) ---
    if datetime.utcnow().weekday() == 0:  # 0 = poniedziałek
        week_report = weekly_report(weekly_data)
        send_telegram(week_report)
        # --- Czyścimy dane po tygodniu ---
        save_weekly_data([])

if __name__ == "__main__":
    run()

import os
import requests
import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

BBC_BUSINESS_RSS = "https://feeds.bbci.co.uk/news/business/rss.xml"
YAHOO_FINANCE_RSS = "https://finance.yahoo.com/news/rssindex"

analyzer = SentimentIntensityAnalyzer()


def rss_items(url: str, limit: int = 15) -> list[dict]:
    feed = feedparser.parse(url)
    items = []
    for entry in feed.entries[:limit]:
        items.append({
            "title": getattr(entry, "title", ""),
            "summary": getattr(entry, "summary", ""),
            "link": getattr(entry, "link", ""),
            "source": getattr(feed.feed, "title", "RSS"),
        })
    return items


def fmp_stock_news(symbols: list[str], limit: int = 20) -> list[dict]:
    api_key = os.getenv("FMP_API_KEY")
    if not api_key:
        return []

    joined = ",".join(symbols)
    url = "https://financialmodelingprep.com/stable/news/stock"
    params = {"symbols": joined, "limit": limit, "apikey": api_key}
    try:
        r = requests.get(url, params=params, timeout=8)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return []

    items = []
    for row in data[:limit]:
        items.append({
            "title": row.get("title", ""),
            "summary": row.get("text", "") or row.get("site", ""),
            "link": row.get("url", ""),
            "source": row.get("publisher", "FMP"),
        })
    return items


def collect_news(mag7: list[str]) -> list[dict]:
    items = []
    items.extend(rss_items(BBC_BUSINESS_RSS, 10))
    items.extend(rss_items(YAHOO_FINANCE_RSS, 10))
    items.extend(fmp_stock_news(mag7, 20))
    return items


def score_news_sentiment(items: list[dict]) -> dict:
    """Bullish points out of 20 using VADER sentiment."""
    if not items:
        return {"points": 10, "avg_compound": 0.0, "items": [], "notes": ["No news items loaded; neutral news score."]}

    scored = []
    compounds = []
    for item in items:
        text = f"{item.get('title','')} {item.get('summary','')}"
        comp = analyzer.polarity_scores(text)["compound"]
        compounds.append(comp)
        item = dict(item)
        item["compound"] = comp
        scored.append(item)

    avg = sum(compounds) / max(len(compounds), 1)

    # Map VADER compound roughly from [-1,1] to [0,20]
    points = round((avg + 1) * 10, 1)
    points = max(0, min(20, points))

    notes = [f"Average headline sentiment compound score: {avg:.2f}."]
    return {"points": points, "avg_compound": avg, "items": scored, "notes": notes}

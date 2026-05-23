import requests
import feedparser
import urllib.parse
from datetime import datetime, date, timedelta
from app.config import settings
import logging
import time

logger = logging.getLogger(__name__)

def fetch_newsapi(query="gold price OR gold market OR gold commodity", page_size=50) -> list:
    """
    Fetch news from NewsAPI.org.
    """
    if not settings.news_api_key:
        logger.warning("NewsAPI key not configured.")
        return []
        
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": page_size,
        "apiKey": settings.news_api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        articles = data.get("articles", [])
        
        results = []
        for art in articles:
            pub_date_str = art.get("publishedAt", "")[:10]  # get YYYY-MM-DD
            try:
                pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d").date()
            except ValueError:
                pub_date = date.today()
                
            results.append({
                "date": pub_date,
                "headline": art.get("title", ""),
                "source_name": art.get("source", {}).get("name", "NewsAPI"),
                "url": art.get("url", ""),
                "category": "economics"
            })
        return results
    except Exception as e:
        logger.error(f"Error fetching from NewsAPI: {e}")
        return []

def fetch_guardian(query="gold price", from_date=None, to_date=None) -> list:
    """
    Fetch news from The Guardian API.
    """
    if not settings.guardian_api_key:
        logger.warning("Guardian API key not configured.")
        return []
        
    url = "https://content.guardianapis.com/search"
    params = {
        "q": query,
        "api-key": settings.guardian_api_key,
        "page-size": 50,
        "order-by": "newest",
        "show-fields": "headline,trailText"
    }
    
    if from_date:
        params["from-date"] = from_date  # Format: YYYY-MM-DD
    if to_date:
        params["to-date"] = to_date
        
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        articles = data.get("response", {}).get("results", [])
        
        results = []
        for art in articles:
            pub_date_str = art.get("webPublicationDate", "")[:10]
            try:
                pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d").date()
            except ValueError:
                pub_date = date.today()
                
            results.append({
                "date": pub_date,
                "headline": art.get("fields", {}).get("headline", art.get("webTitle", "")),
                "source_name": "The Guardian",
                "url": art.get("webUrl", ""),
                "category": art.get("sectionName", "news")
            })
        return results
    except Exception as e:
        logger.error(f"Error fetching from The Guardian: {e}")
        return []

def fetch_google_news_rss(query="gold price") -> list:
    """
    Fetch news from Google News RSS feed.
    """
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    
    try:
        feed = feedparser.parse(url)
        results = []
        for entry in feed.entries:
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub_date = date(*entry.published_parsed[:3])
            else:
                pub_date = date.today()
                
            title = entry.get("title", "")
            
            # Extract source from title suffix (e.g. "Gold rises - Reuters")
            source_name = "Google News"
            if " - " in title:
                parts = title.split(" - ")
                source_name = parts[-1].strip()
                title = " - ".join(parts[:-1]).strip()
                
            results.append({
                "date": pub_date,
                "headline": title,
                "source_name": source_name,
                "url": entry.get("link", ""),
                "category": "economics"
            })
        return results
    except Exception as e:
        logger.error(f"Error fetching from Google News RSS: {e}")
        return []

def fetch_nyt_archive(year: int, month: int) -> list:
    """
    Fetch NYT Archive news for a specific month (for building historical sentiment/context).
    """
    if not settings.nyt_api_key:
        logger.warning("NYT API key not configured.")
        return []
        
    url = f"https://api.nytimes.com/svc/archive/v1/{year}/{month}.json"
    params = {
        "api-key": settings.nyt_api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        docs = data.get("response", {}).get("docs", [])
        
        # Keywords to filter articles relevant to gold and economy
        keywords = {"gold", "federal reserve", "inflation", "interest rate", "war", "crisis", "economy", "recession"}
        
        results = []
        for doc in docs:
            headline = doc.get("headline", {}).get("main", "")
            lead_paragraph = doc.get("lead_paragraph", "") or ""
            
            combined_text = (headline + " " + lead_paragraph).lower()
            if not any(kw in combined_text for kw in keywords):
                continue
                
            pub_date_str = doc.get("pub_date", "")[:10]
            try:
                pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d").date()
            except ValueError:
                pub_date = date.today()
                
            results.append({
                "date": pub_date,
                "headline": headline,
                "source_name": "The New York Times",
                "url": doc.get("web_url", ""),
                "category": doc.get("section_name", "news")
            })
            
        return results
    except Exception as e:
        logger.error(f"Error fetching from NYT Archive ({year}/{month}): {e}")
        return []

def fetch_all_current_news() -> list:
    """
    Fetch recent headlines from NewsAPI, Guardian, and Google News RSS.
    Deduplicates headlines.
    """
    logger.info("Fetching recent news headlines...")
    
    news_items = []
    news_items.extend(fetch_google_news_rss("gold price OR gold market"))
    news_items.extend(fetch_newsapi("gold price OR gold market OR gold commodity"))
    news_items.extend(fetch_guardian("gold price"))
    
    # Deduplicate by lowercase headline
    seen_headlines = set()
    deduped = []
    
    for item in news_items:
        headline_clean = item["headline"].strip().lower()
        if not headline_clean or headline_clean in seen_headlines:
            continue
        seen_headlines.add(headline_clean)
        deduped.append(item)
        
    deduped.sort(key=lambda x: x["date"], reverse=True)
    logger.info(f"Fetched and deduped {len(deduped)} news articles.")
    return deduped

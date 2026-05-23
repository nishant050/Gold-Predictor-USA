from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sqlalchemy.orm import Session
from app.models.schemas import NewsSentiment
from datetime import datetime, date, timedelta
import pandas as pd
import logging

logger = logging.getLogger(__name__)

GOLD_LEXICON = {
    "safe haven": 2.0, "safe-haven": 2.0, "geopolitical risk": 1.5,
    "inflation": 1.0, "rate cut": 1.5, "rate hike": -1.5,
    "dovish": 1.5, "hawkish": -1.5, "quantitative easing": 1.5,
    "recession": 1.0, "crisis": 1.5, "war": 1.5, "sanctions": 1.0,
    "tariff": 0.8, "uncertainty": 1.0, "strong dollar": -1.5,
    "weak dollar": 1.5, "fed cut": 1.5, "fed raise": -1.0,
    "bullion": 0.5, "gold rally": 2.0, "gold slump": -2.0,
    "gold surge": 2.0, "gold drop": -2.0, "demand": 0.8,
    "central bank buying": 1.5, "de-dollarization": 1.5,
    "easing": 1.2, "tightening": -1.2, "stimulus": 1.5, "deficit": 0.8,
    "surplus": -0.5, "devaluation": 1.5, "appreciation": -1.0,
    "haven": 1.5, "refuge": 1.5, "shelter": 1.0,
    "mining": 0.3, "reserve": 0.5, "accumulation": 0.8,
    "selloff": -1.5, "correction": -0.8, "plunge": -2.0, "soar": 2.0,
    "record high": 1.5, "all-time high": 1.5, "support level": 0.5,
    "resistance level": -0.5, "breakout": 1.0, "breakdown": -1.0,
    "default": 1.5, "bankruptcy": 1.0, "bailout": 1.0,
    "escalation": 1.0, "ceasefire": -0.5, "peace": -0.8,
    "missile": 1.0, "nuclear": 1.5, "invasion": 1.5,
    "downgrade": 1.0, "upgrade": -0.5,
    "weaker": 0.8, "stronger": -0.8, "volatility": 0.5
}

RELEVANCE_KEYWORDS = [
    "gold", "bullion", "precious metal", "fed", "federal reserve", 
    "interest rate", "inflation", "dollar", "cpi", "safe haven", 
    "dxy", "rate cut", "rate hike", "treasury", "commodity", 
    "recession", "economic crisis", "geopolitics", "central bank", "silver"
]

def analyze_sentiment(headline: str) -> dict:
    """
    Analyze sentiment of a headline using VADER extended with a gold-specific lexicon.
    """
    analyzer = SentimentIntensityAnalyzer()
    analyzer.lexicon.update(GOLD_LEXICON)
    scores = analyzer.polarity_scores(headline)
    
    compound = scores['compound']
    if compound >= 0.05:
        label = 'positive'
    elif compound <= -0.05:
        label = 'negative'
    else:
        label = 'neutral'
        
    return {
        "sentiment_score": compound,
        "sentiment_label": label
    }

def calculate_relevance(headline: str) -> float:
    """
    Calculate how relevant the headline is to gold/economics (0.0 to 1.0) using match count scaling.
    """
    text = headline.lower()
    matches = sum(1 for kw in RELEVANCE_KEYWORDS if kw in text)
    return min(1.0, matches * 0.2 + 0.1)

def score_and_store_news(db: Session, news_items: list) -> dict:
    """
    Analyze sentiment and relevance of news items and store them in the database.
    Deduplicates against existing database headlines.
    """
    inserted = 0
    skipped = 0
    total_score = 0.0
    
    # Query existing headlines in the last 30 days to avoid duplicates
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)
    existing_headlines = {
        row[0].strip().lower() 
        for row in db.query(NewsSentiment.headline).filter(NewsSentiment.date >= thirty_days_ago).all()
    }
    
    for item in news_items:
        headline = item["headline"].strip()
        headline_lower = headline.lower()
        
        if headline_lower in existing_headlines:
            skipped += 1
            continue
            
        sentiment = analyze_sentiment(headline)
        relevance = calculate_relevance(headline)
        
        # Parse date
        item_date = item["date"]
        if isinstance(item_date, str):
            item_date = datetime.strptime(item_date[:10], "%Y-%m-%d").date()
            
        news_sentiment = NewsSentiment(
            date=item_date,
            headline=headline,
            source_name=item["source_name"],
            url=item.get("url"),
            sentiment_score=sentiment["sentiment_score"],
            sentiment_label=sentiment["sentiment_label"],
            relevance_score=relevance,
            category=item.get("category")
        )
        db.add(news_sentiment)
        existing_headlines.add(headline_lower)
        inserted += 1
        total_score += sentiment["sentiment_score"]
        
    db.commit()
    
    avg_sentiment = (total_score / inserted) if inserted > 0 else 0.0
    logger.info(f"Processed news items: {inserted} inserted, {skipped} skipped. Avg sentiment: {avg_sentiment:.2f}")
    
    return {
        "processed": inserted,
        "skipped": skipped,
        "avg_sentiment": avg_sentiment
    }

def compute_daily_aggregate_sentiment(db: Session, target_date: date) -> dict:
    """
    Calculate relevance-weighted daily aggregate sentiment score for a given date.
    """
    rows = db.query(NewsSentiment).filter(NewsSentiment.date == target_date).all()
    
    if not rows:
        return {
            "date": target_date,
            "avg_sentiment": 0.0,
            "article_count": 0,
            "bullish_pct": 0.0,
            "bearish_pct": 0.0
        }
        
    total_weight = 0.0
    weighted_sentiment_sum = 0.0
    bullish_count = 0
    bearish_count = 0
    
    for row in rows:
        weight = row.relevance_score or 1.0
        total_weight += weight
        weighted_sentiment_sum += row.sentiment_score * weight
        
        if row.sentiment_score >= 0.05:
            bullish_count += 1
        elif row.sentiment_score <= -0.05:
            bearish_count += 1
            
    avg_sentiment = (weighted_sentiment_sum / total_weight) if total_weight > 0 else 0.0
    total_articles = len(rows)
    
    return {
        "date": target_date,
        "avg_sentiment": round(avg_sentiment, 4),
        "article_count": total_articles,
        "bullish_pct": round((bullish_count / total_articles) * 100, 2),
        "bearish_pct": round((bearish_count / total_articles) * 100, 2)
    }

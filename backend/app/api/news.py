from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import date, timedelta
from app.database import get_db
from app.models.schemas import NewsSentiment
from app.services.sentiment_service import compute_daily_aggregate_sentiment

router = APIRouter()

@router.get("/latest")
def get_latest_news(
    limit: int = Query(20),
    db: Session = Depends(get_db)
):
    """Returns the most recent news headlines processed with VADER sentiment."""
    news = db.query(NewsSentiment).order_by(desc(NewsSentiment.date), desc(NewsSentiment.id)).limit(limit).all()
    
    return [
        {
            "id": n.id,
            "date": n.date.isoformat(),
            "headline": n.headline,
            "source_name": n.source_name,
            "url": n.url,
            "sentiment_score": round(n.sentiment_score, 3),
            "sentiment_label": n.sentiment_label,
            "relevance_score": round(n.relevance_score, 2) if n.relevance_score else 0.5,
            "category": n.category
        }
        for n in news
    ]

@router.get("/sentiment-trend")
def get_sentiment_trend(
    days: int = Query(30),
    db: Session = Depends(get_db)
):
    """
    Returns daily aggregated sentiment scores for the last N days.
    Provides time-series data for frontend news gauge & sentiment chart.
    """
    from sqlalchemy import func, case
    today = date.today()
    cutoff = today - timedelta(days=days)
    
    daily_stats = db.query(
        NewsSentiment.date,
        func.avg(NewsSentiment.sentiment_score).label("avg_sentiment"),
        func.count(NewsSentiment.id).label("article_count"),
        func.sum(case((NewsSentiment.sentiment_score >= 0.05, 1), else_=0)).label("bullish_count"),
        func.sum(case((NewsSentiment.sentiment_score <= -0.05, 1), else_=0)).label("bearish_count")
    ).filter(
        NewsSentiment.date >= cutoff
    ).group_by(NewsSentiment.date).order_by(NewsSentiment.date).all()
    
    trend = []
    for row in daily_stats:
        d = row[0]
        cnt = row[2]
        if cnt > 0:
            trend.append({
                "date": d.isoformat() if hasattr(d, "isoformat") else str(d),
                "avg_sentiment": round(float(row[1]), 4),
                "article_count": cnt,
                "bullish_pct": round((row[3] / cnt) * 100, 2),
                "bearish_pct": round((row[4] / cnt) * 100, 2)
            })
            
    return trend

@router.get("/impact")
def get_sentiment_impact(db: Session = Depends(get_db)):
    """
    Returns paired data matching daily average sentiment vs the next day's 
    gold price percentage change. Used on the frontend to visualize correlation.
    """
    from app.models.schemas import GoldPrice
    from sqlalchemy import func
    import bisect
    
    # Fetch all USD prices to do in-memory pairing (much faster than N loop queries)
    prices = db.query(GoldPrice.date, GoldPrice.close).filter(GoldPrice.currency == "USD").order_by(GoldPrice.date).all()
    if not prices:
        return []
        
    price_dates = [p[0] for p in prices]
    price_closes = [p[1] for p in prices]
    
    # Get daily aggregated sentiment
    daily_sent = db.query(
        NewsSentiment.date,
        func.avg(NewsSentiment.sentiment_score).label("avg_sent")
    ).group_by(NewsSentiment.date).order_by(NewsSentiment.date).all()
    
    results = []
    for row in daily_sent:
        sent_date = row[0]
        avg_sent = row[1]
        
        # Binary search for same-day index (on or before sent_date)
        idx = bisect.bisect_right(price_dates, sent_date)
        same_day_idx = idx - 1
        next_day_idx = idx
        
        if 0 <= same_day_idx < len(price_dates) and 0 <= next_day_idx < len(price_dates):
            same_close = price_closes[same_day_idx]
            next_close = price_closes[next_day_idx]
            
            if same_close > 0:
                pct_change = ((next_close - same_close) / same_close) * 100
                results.append({
                    "date": sent_date.isoformat() if hasattr(sent_date, "isoformat") else str(sent_date),
                    "sentiment": round(float(avg_sent), 3),
                    "price_change_pct": round(pct_change, 3)
                })
                
    return results

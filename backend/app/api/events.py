from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import date, timedelta
import json
from app.database import get_db
from app.models.schemas import HistoricalEvent, GoldPrice

router = APIRouter()

@router.get("/")
def get_events(
    event_type: str = Query(None),
    impact_level: int = Query(None),
    start_date: date = Query(None),
    end_date: date = Query(None),
    db: Session = Depends(get_db)
):
    """
    Returns historical events list, filtered by type, impact, and date range.
    """
    query = db.query(HistoricalEvent)
    
    if event_type:
        query = query.filter(HistoricalEvent.event_type == event_type)
    if impact_level:
        query = query.filter(HistoricalEvent.impact_level == impact_level)
    if start_date:
        query = query.filter(HistoricalEvent.event_date >= start_date)
    if end_date:
        query = query.filter(HistoricalEvent.event_date <= end_date)
        
    events = query.order_by(desc(HistoricalEvent.event_date)).all()
    
    results = []
    for ev in events:
        results.append({
            "id": ev.id,
            "event_date": ev.event_date.isoformat(),
            "event_type": ev.event_type,
            "title": ev.title,
            "description": ev.description,
            "impact_level": ev.impact_level,
            "impact_level": ev.impact_level,
            "gold_price_at_event": round(ev.gold_price_at_event * 3.538, 2) if ev.gold_price_at_event else None,
            "gold_price_change_7d": round(ev.gold_price_change_7d, 2) if ev.gold_price_change_7d is not None else None,
            "gold_price_change_90d": round(ev.gold_price_change_90d, 2) if ev.gold_price_change_90d is not None else None,
            "tags": json.loads(ev.tags) if ev.tags else [],
            "source": ev.source
        })
    return results

@router.get("/timeline")
def get_timeline(db: Session = Depends(get_db)):
    """Returns chronologically ordered events metadata for frontend timeline visualizer."""
    events = db.query(HistoricalEvent).order_by(desc(HistoricalEvent.event_date)).all()
    
    # Assign styling color values depending on category type
    color_map = {
        "war": "#ef4444",              # Red / Geopolitical
        "monetary_policy": "#eab308",  # Yellow / Monetary
        "economic_crisis": "#f97316",  # Orange / Financial Crisis
        "pandemic": "#a855f7",         # Purple / Health Crisis
        "trade": "#06b6d4",            # Cyan / Trade & Sanctions
        "inflation": "#3b82f6",        # Blue / Inflation
        "election": "#10b981",         # Emerald / Politics
        "market_crash": "#ec4899"      # Pink / Equity Crash
    }
    
    timeline = []
    for ev in events:
        change_30d = "N/A"
        if ev.gold_price_change_30d is not None:
            prefix = "+" if ev.gold_price_change_30d > 0 else ""
            change_30d = f"{prefix}{ev.gold_price_change_30d:.1f}%"
            
        timeline.append({
            "id": ev.id,
            "date": ev.event_date.isoformat(),
            "title": ev.title,
            "type": ev.event_type,
            "type": ev.event_type,
            "impact_level": ev.impact_level,
            "gold_price": round(ev.gold_price_at_event * 3.538, 2) if ev.gold_price_at_event else None,
            "gold_change_30d": change_30d,
        })
    return timeline

@router.get("/impact-analysis")
def get_impact_analysis(db: Session = Depends(get_db)):
    """
    Returns average gold price shifts (7d, 30d, 90d) grouped by event categories,
    showing statistical impact analysis.
    """
    types_query = db.query(HistoricalEvent.event_type).distinct().all()
    types = [t[0] for t in types_query]
    
    analysis = {}
    for t in types:
        stats = db.query(
            func.count(HistoricalEvent.id),
            func.avg(HistoricalEvent.gold_price_change_7d),
            func.avg(HistoricalEvent.gold_price_change_30d),
            func.avg(HistoricalEvent.gold_price_change_90d)
        ).filter(
            HistoricalEvent.event_type == t
        ).first()
        
        analysis[t] = {
            "count": stats[0],
            "avg_7d_change": round(stats[1], 2) if stats[1] is not None else 0.0,
            "avg_30d_change": round(stats[2], 2) if stats[2] is not None else 0.0,
            "avg_90d_change": round(stats[3], 2) if stats[3] is not None else 0.0
        }
    return {"by_type": analysis}

@router.get("/{event_id}")
def get_event_detail(event_id: int, db: Session = Depends(get_db)):
    """
    Returns details of a single event, plus historical daily price trends in a
    60-day window centered on the event date (30 days before, 30 days after).
    """
    ev = db.query(HistoricalEvent).filter(HistoricalEvent.id == event_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
        
    # Get 30d window around event
    start_date = ev.event_date - timedelta(days=30)
    end_date = ev.event_date + timedelta(days=30)
    
    price_history = db.query(GoldPrice).filter(
        GoldPrice.currency == "INR",
        GoldPrice.date >= start_date,
        GoldPrice.date <= end_date
    ).order_by(GoldPrice.date).all()
    
    return {
        "event": {
            "id": ev.id,
            "event_date": ev.event_date.isoformat(),
            "event_type": ev.event_type,
            "title": ev.title,
            "description": ev.description,
            "impact_level": ev.impact_level,
            "gold_price_at_event": round(ev.gold_price_at_event * 3.538, 2) if ev.gold_price_at_event else None,
            "gold_price_change_7d": round(ev.gold_price_change_7d, 2) if ev.gold_price_change_7d is not None else None,
            "gold_price_change_30d": round(ev.gold_price_change_30d, 2) if ev.gold_price_change_30d is not None else None,
            "gold_price_change_90d": round(ev.gold_price_change_90d, 2) if ev.gold_price_change_90d is not None else None,
            "tags": json.loads(ev.tags) if ev.tags else [],
            "source": ev.source
        },
        "price_history": [
            {"date": p.date.isoformat(), "price": round(p.close * 121.88, 2)}
            for p in price_history
        ]
    }

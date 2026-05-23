import json
import logging
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd
import numpy as np

from app.models.schemas import GoldPrice, EconomicIndicator, HistoricalEvent, NewsSentiment

logger = logging.getLogger(__name__)

# --- Tool Functions ---

def get_price_history(db: Session, start_date: str, end_date: str, currency: str = "USD") -> str:
    prices = db.query(GoldPrice).filter(
        GoldPrice.currency == currency,
        GoldPrice.date >= start_date,
        GoldPrice.date <= end_date
    ).order_by(GoldPrice.date).all()
    
    if not prices:
        return f"No price data found between {start_date} and {end_date}."
        
    data = [{"date": str(p.date), "close": p.close} for p in prices]
    return f"Found {len(data)} trading days. Data: {json.dumps(data)}"

def get_economic_indicator(db: Session, indicator_name: str, start_date: str, end_date: str) -> str:
    indicators = db.query(EconomicIndicator).filter(
        EconomicIndicator.indicator_name == indicator_name,
        EconomicIndicator.date >= start_date,
        EconomicIndicator.date <= end_date
    ).order_by(EconomicIndicator.date).all()
    
    if not indicators:
        return f"No data found for indicator '{indicator_name}' between {start_date} and {end_date}."
        
    data = [{"date": str(ind.date), "value": ind.value} for ind in indicators]
    return f"Indicator {indicator_name} data: {json.dumps(data)}"

def search_news(db: Session, query: str, start_date: str, end_date: str, limit: int = 10) -> str:
    q = query.lower()
    # Simple substring search for simplicity
    news = db.query(NewsSentiment).filter(
        NewsSentiment.date >= start_date,
        NewsSentiment.date <= end_date,
        func.lower(NewsSentiment.headline).contains(q)
    ).order_by(NewsSentiment.date.desc()).limit(limit).all()
    
    if not news:
        return f"No news found matching '{query}' between {start_date} and {end_date}."
        
    data = [{"date": str(n.date), "headline": n.headline, "sentiment": n.sentiment_score} for n in news]
    return f"Found {len(data)} matching articles: {json.dumps(data)}"

def search_historical_events(db: Session, event_type: str = None, min_impact: int = 1, start_date: str = None, end_date: str = None) -> str:
    query = db.query(HistoricalEvent).filter(HistoricalEvent.impact_level >= min_impact)
    if event_type:
        query = query.filter(HistoricalEvent.event_type == event_type)
    if start_date:
        query = query.filter(HistoricalEvent.event_date >= start_date)
    if end_date:
        query = query.filter(HistoricalEvent.event_date <= end_date)
        
    events = query.order_by(HistoricalEvent.event_date.desc()).limit(15).all()
    
    if not events:
        return "No historical events found matching those criteria."
        
    data = [{
        "date": str(e.event_date), 
        "title": e.title, 
        "type": e.event_type, 
        "impact": e.impact_level, 
        "change_7d": e.gold_price_change_7d
    } for e in events]
    return f"Found events: {json.dumps(data)}"

def get_event_detail(db: Session, event_id: int) -> str:
    event = db.query(HistoricalEvent).filter(HistoricalEvent.id == event_id).first()
    if not event:
        return "Event not found."
        
    data = {
        "title": event.title,
        "date": str(event.event_date),
        "description": event.description,
        "type": event.event_type,
        "impact": event.impact_level,
        "gold_change_7d_pct": event.gold_price_change_7d,
        "gold_change_30d_pct": event.gold_price_change_30d,
        "gold_change_90d_pct": event.gold_price_change_90d
    }
    return json.dumps(data)

def get_cross_asset_ratios(db: Session, start_date: str, end_date: str) -> str:
    # Get Gold, Silver, SP500, Oil
    prices = db.query(GoldPrice.date, GoldPrice.close).filter(
        GoldPrice.currency == "USD", GoldPrice.date >= start_date, GoldPrice.date <= end_date
    ).all()
    
    if not prices:
        return "No data for ratios."
        
    df_gold = pd.DataFrame(prices, columns=["date", "gold"]).set_index("date")
    
    inds = db.query(EconomicIndicator).filter(
        EconomicIndicator.indicator_name.in_(["SILVER", "SP500", "OIL_WTI"]),
        EconomicIndicator.date >= start_date,
        EconomicIndicator.date <= end_date
    ).all()
    
    df_ind = pd.DataFrame([{"date": i.date, "name": i.indicator_name, "value": i.value} for i in inds])
    if df_ind.empty:
        return "Not enough indicator data for cross-asset ratios."
        
    df_pivot = df_ind.pivot(index="date", columns="name", values="value")
    df_all = df_gold.join(df_pivot).ffill().dropna()
    
    if df_all.empty:
        return "Insufficient overlap for cross-asset computation."
        
    res = []
    for date_idx, row in df_all.iterrows():
        res.append({
            "date": str(date_idx),
            "gold_silver_ratio": round(row["gold"] / row["SILVER"], 2) if row.get("SILVER") else None,
            "gold_oil_ratio": round(row["gold"] / row["OIL_WTI"], 2) if row.get("OIL_WTI") else None,
            "gold_sp500_ratio": round(row["gold"] / row["SP500"], 4) if row.get("SP500") else None
        })
    return json.dumps(res[-10:]) # Return last 10 days to save tokens

# Dispatch dictionary
TOOL_FUNCTIONS = {
    "get_price_history": get_price_history,
    "get_economic_indicator": get_economic_indicator,
    "search_news": search_news,
    "search_historical_events": search_historical_events,
    "get_event_detail": get_event_detail,
    "get_cross_asset_ratios": get_cross_asset_ratios
}

# --- Tool Schemas (OpenAI format) ---
LLM_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_price_history",
            "description": "Fetch gold closing prices (in USD) for a specific date range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "YYYY-MM-DD"}
                },
                "required": ["start_date", "end_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_economic_indicator",
            "description": "Fetch historical data for a specific economic indicator (e.g., DXY, FED_RATE, CPI, VIX, M2, TREASURY_10Y, REAL_RATE).",
            "parameters": {
                "type": "object",
                "properties": {
                    "indicator_name": {"type": "string", "description": "Name of indicator like DXY, FED_RATE"},
                    "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "YYYY-MM-DD"}
                },
                "required": ["indicator_name", "start_date", "end_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_news",
            "description": "Search for news headlines in the database matching a keyword over a date range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "limit": {"type": "integer", "description": "Max results"}
                },
                "required": ["query", "start_date", "end_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_historical_events",
            "description": "Search historical events by type, impact level, and date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_type": {"type": "string", "description": "Optional event type: war, economic_crisis, monetary_policy, etc."},
                    "min_impact": {"type": "integer", "description": "Minimum impact level 1 to 5"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_event_detail",
            "description": "Get detailed description and exact gold price reactions for a specific historical event ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {"type": "integer", "description": "ID of the event (obtained from search_historical_events)"}
                },
                "required": ["event_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_cross_asset_ratios",
            "description": "Get ratios of gold to silver, oil, and SP500 for the end of a given date range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"}
                },
                "required": ["start_date", "end_date"]
            }
        }
    }
]

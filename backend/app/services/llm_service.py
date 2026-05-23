import httpx
import json
import logging
import asyncio
from datetime import datetime, date, timedelta
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.config import settings
from app.models.schemas import GoldPrice, EconomicIndicator, HistoricalEvent, NewsSentiment, LLMAnalysis, Prediction
from app.services.sentiment_service import compute_daily_aggregate_sentiment
from app.utils.api_key_manager import get_active_key, mark_key_exhausted
from app.services.llm_agent import run_agentic_loop, get_configured_openrouter_model

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert gold market analyst with deep knowledge of 20+ years of gold price history. 
Your job is to analyze current world events and economic conditions, find similar historical 
periods/events, and predict how gold prices will move over the next 7 days.

You must always structure your response in the following JSON format:
{
  "current_situation_summary": "Brief summary of current key events/conditions affecting gold",
  "similar_historical_events": [
    {
      "event": "Description of the historical event",
      "date": "YYYY-MM-DD",
      "similarity_reason": "Why this is similar to the current situation",
      "gold_price_at_time": 1234.56,
      "gold_price_change_7d_pct": 5.2,
      "key_context": "What were the economic conditions then (rates, inflation, dollar)"
    }
  ],
  "analysis": "Detailed reasoning connecting historical patterns to current situation",
  "prediction": {
    "direction": "up|down|flat",
    "predicted_change_percent": 3.5,
    "predicted_price_7d": 3456.78,
    "confidence": "low|medium|high",
    "key_drivers": ["driver1", "driver2"],
    "risks_to_prediction": ["risk1", "risk2"]
  },
  "daily_trajectory": "Brief description of expected path (e.g., 'initial spike then gradual decline')"
}

Be specific. Reference actual historical dates, actual gold prices, and actual percentage moves.
Your analysis should be grounded in facts, not speculation. Return ONLY valid JSON, do not wrap in markdown or add extra text."""

def get_latest_gold_price(db: Session, currency="USD") -> float:
    row = db.query(GoldPrice).filter(GoldPrice.currency == currency).order_by(desc(GoldPrice.date)).first()
    return row.close if row else 0.0

def get_recent_headlines(db: Session, days=7) -> list:
    cutoff = date.today() - timedelta(days=days)
    rows = db.query(NewsSentiment).filter(NewsSentiment.date >= cutoff).order_by(desc(NewsSentiment.date)).all()
    return [{"date": r.date.isoformat(), "headline": r.headline, "sentiment": r.sentiment_score} for r in rows]

def get_current_indicators(db: Session) -> dict:
    indicators = ["DXY", "FED_RATE", "CPI", "TREASURY_10Y", "OIL_WTI", "SP500", "VIX", "M2", "SILVER", "REAL_RATE"]
    results = {}
    for ind in indicators:
        row = db.query(EconomicIndicator).filter(EconomicIndicator.indicator_name == ind).order_by(desc(EconomicIndicator.date)).first()
        results[ind] = row.value if row else None
    return results

def get_sentiment_summary(db: Session, days=7) -> float:
    total_sentiment = 0.0
    valid_days = 0
    today = date.today()
    for i in range(days):
        target_date = today - timedelta(days=i)
        agg = compute_daily_aggregate_sentiment(db, target_date)
        if agg["article_count"] > 0:
            total_sentiment += agg["avg_sentiment"]
            valid_days += 1
    return (total_sentiment / valid_days) if valid_days > 0 else 0.0



def build_analysis_prompt(current_price, recent_news, indicators, avg_sentiment) -> str:
    news_lines = [f"- {n['date']}: {n['headline']} (sentiment: {n['sentiment']:+.2f})" for n in recent_news[:15]]
    news_formatted = "\n".join(news_lines) if news_lines else "No recent headlines available."
    
    ind_lines = [f"- {k}: {v}" for k, v in indicators.items() if v is not None]
    ind_formatted = "\n".join(ind_lines) if ind_lines else "No indicator data available."
    
    prompt = f"""CURRENT GOLD PRICE (USD): ${current_price:,.2f} (as of {date.today().isoformat()})

CURRENT ECONOMIC & COMMODITY INDICATORS:
{ind_formatted}

AVERAGE RECENT NEWS SENTIMENT (last 7 days): {avg_sentiment:+.2f}

RECENT NEWS HEADLINES:
{news_formatted}"""
    return prompt


async def run_llm_gold_analysis(db: Session) -> dict:
    """Run a full LLM-based gold price historical analogy analysis via agentic loop."""
    logger.info("Initializing Agentic LLM gold analysis run...")
    
    current_gold_price = get_latest_gold_price(db, "USD")
    recent_news = get_recent_headlines(db, days=7)
    indicators = get_current_indicators(db)
    avg_sentiment = get_sentiment_summary(db, days=7)
    
    briefing_text = build_analysis_prompt(
        current_price=current_gold_price,
        recent_news=recent_news,
        indicators=indicators,
        avg_sentiment=avg_sentiment
    )
    
    openrouter_model = get_configured_openrouter_model(db)
    logger.info(f"Starting Agentic Loop with OpenRouter ({openrouter_model})...")
    raw_response = await run_agentic_loop(
        db=db, 
        system_prompt=SYSTEM_PROMPT, 
        briefing_text=briefing_text,
        max_tool_calls=settings.llm_max_tool_calls
    )
    
    # Parse JSON
    # Strip potential markdown backticks around JSON
    clean_response = raw_response.strip()
    if clean_response.startswith("```json"):
        clean_response = clean_response[7:]
    if clean_response.endswith("```"):
        clean_response = clean_response[:-3]
    clean_response = clean_response.strip()
    
    try:
        analysis = json.loads(clean_response)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse LLM final response: {clean_response}")
        raise ValueError("LLM did not return a valid JSON object.")
    
    # Store in database
    llm_analysis = LLMAnalysis(
        analysis_date=date.today(),
        current_events_summary=analysis["current_situation_summary"],
        similar_historical_events=json.dumps(analysis["similar_historical_events"]),
        historical_outcomes=json.dumps([e.get("gold_price_change_7d_pct", e.get("gold_price_change_30d_pct", 0.0)) for e in analysis["similar_historical_events"]]),
        reasoning=analysis["analysis"],
        predicted_direction=analysis["prediction"]["direction"],
        predicted_change_percent=analysis["prediction"]["predicted_change_percent"],
        predicted_price_7d=analysis["prediction"].get("predicted_price_7d", analysis["prediction"].get("predicted_price_30d", 0.0)),
        confidence_level=analysis["prediction"]["confidence"],
        model_used=openrouter_model,
        raw_response=raw_response
    )
    db.add(llm_analysis)
    
    # Compute 7-day daily predictions via geometric interpolation
    target_pct = float(analysis["prediction"]["predicted_change_percent"])
    # Adjust sign based on direction
    direction = analysis["prediction"]["direction"].lower()
    if direction == "down" and target_pct > 0:
        target_pct = -target_pct
    elif direction == "up" and target_pct < 0:
        target_pct = -target_pct
        
    daily_rate = (1 + target_pct / 100) ** (1 / 7) - 1
    
    # Clear any existing LLM predictions for upcoming dates made today
    today_date = date.today()
    db.query(Prediction).filter(
        Prediction.prediction_date == today_date,
        Prediction.prediction_method == "llm"
    ).delete()
    
    for day in range(1, 8):
        target_date = today_date + timedelta(days=day)
        pred_price = current_gold_price * ((1 + daily_rate) ** day)
        
        # Approximate confidence bands based on target confidence level
        # low = wide bands, high = narrow bands
        vol_factor = {"low": 0.05, "medium": 0.03, "high": 0.015}[analysis["prediction"]["confidence"].lower()]
        std_dev = pred_price * (vol_factor * (day / 7) ** 0.5)
        
        db_pred = Prediction(
            prediction_date=today_date,
            target_date=target_date,
            predicted_price=round(pred_price, 2),
            confidence_low_80=round(pred_price - 1.28 * std_dev, 2),
            confidence_high_80=round(pred_price + 1.28 * std_dev, 2),
            confidence_low_95=round(pred_price - 1.96 * std_dev, 2),
            confidence_high_95=round(pred_price + 1.96 * std_dev, 2),
            model_version=f"llm_{openrouter_model}",
            prediction_method="llm",
            features_used=json.dumps({
                "sentiment": avg_sentiment,
                "dxy": indicators.get("DXY"),
                "fed_rate": indicators.get("FED_RATE"),
                "cpi": indicators.get("CPI")
            })
        )
        db.add(db_pred)
        
    db.commit()
    logger.info("LLM Analysis and interpolated predictions stored in database successfully.")
    return analysis

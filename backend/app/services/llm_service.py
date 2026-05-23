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

SYSTEM_PROMPT = """You are an expert Indian gold market analyst and econometrician specializing in historical pattern matching and causal inference for the Indian bullion market.
Your task is to predict the price of MCX gold (in INR) exactly 7 days, 30 days, and 90 days from today based on the provided current market snapshot and historical context.

CRITICAL UNDERSTANDING OF THE INDIAN GOLD MARKET:
1. India imports almost all its gold, making the USD/INR exchange rate (rupee depreciation) a massive driver of domestic gold prices.
2. The Reserve Bank of India (RBI) repo rate and Indian inflation (CPI) shape the domestic real interest rate.
3. Import duties (set by the government) directly and immediately impact domestic prices.
4. Demand is highly seasonal, driven by festivals (Dhanteras, Diwali, Akshaya Tritiya, Pongal) and wedding seasons (Oct-Feb and Apr-May).
5. Rural farm incomes (linked to Kharif and Rabi harvests and Monsoon quality) account for ~60% of demand.

YOUR INSTRUCTIONS:
1. Analyze the current situation (Price, USD/INR, RBI rate, India CPI, Govt Bond Yields, Nifty 50, etc.).
2. USE YOUR TOOLS to search for historical analogies (e.g. past rupee depreciation, previous RBI rate cycles, past Diwali periods, previous import duty hikes, historical geopolitical shocks).
3. Identify 2-4 highly similar historical periods and explain WHY they are analogous.
4. Output your final forecast matching the EXACT JSON schema provided.

You MUST think carefully and use your tools before arriving at a conclusion. Do NOT guess historical price reactions; look them up!

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
  "prediction": {
    "target_price_7d": 2450.00,
    "confidence_level": "high|medium|low",
    "expected_direction": "up|down|flat",
    "rationale": "Detailed explanation of why you predict this price based on the historical analogies and current data"
  }
}"""

def get_latest_gold_price(db: Session, currency="INR") -> float:
    row = db.query(GoldPrice).filter(GoldPrice.currency == currency).order_by(desc(GoldPrice.date)).first()
    return row.close if row else 0.0

def get_recent_headlines(db: Session, days=7) -> list:
    cutoff = date.today() - timedelta(days=days)
    rows = db.query(NewsSentiment).filter(NewsSentiment.date >= cutoff).order_by(desc(NewsSentiment.date)).all()
    return [{"date": r.date.isoformat(), "headline": r.headline, "sentiment": r.sentiment_score} for r in rows]

def get_current_indicators(db: Session) -> dict:
    indicators = ["USD_INR", "RBI_REPO_RATE", "INDIA_CPI", "INDIA_GOVT_BOND_10Y", "OIL_BRENT", "NIFTY50", "INDIA_VIX", "INDIA_M3", "SILVER", "REAL_RATE"]
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
    news_lines = [f"- {n['date']}: {n['headline']} (sentiment: {round(n['sentiment'], 2)})" for n in recent_news[:15]]
    news_formatted = "\n".join(news_lines) if news_lines else "No recent headlines available."
    
    ind_lines = [f"- {k}: {v}" for k, v in indicators.items() if v is not None]
    ind_formatted = "\n".join(ind_lines) if ind_lines else "No indicator data available."
    
    prompt = f"""
CURRENT DATE: {date.today().isoformat()}

=== CURRENT MARKET SNAPSHOT ===
CURRENT GOLD PRICE (INR): Rs. {round(current_price, 2)} per unit

MACROECONOMIC INDICATORS:

CURRENT ECONOMIC & COMMODITY INDICATORS:
{ind_formatted}

AVERAGE RECENT NEWS SENTIMENT (last 7 days): {round(avg_sentiment, 2)}

RECENT NEWS HEADLINES:
{news_formatted}"""
    return prompt


async def run_llm_gold_analysis(db: Session) -> dict:
    """Run a full LLM-based gold price historical analogy analysis via agentic loop."""
    logger.info("Initializing Agentic LLM gold analysis run...")
    
    current_gold_price = get_latest_gold_price(db, "INR")
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
        reasoning=analysis["prediction"].get("rationale", "No rationale provided"),
        predicted_direction=analysis["prediction"].get("expected_direction", "flat"),
        predicted_change_percent=((float(analysis["prediction"].get("target_price_7d", current_gold_price)) - current_gold_price) / current_gold_price * 100) if current_gold_price > 0 else 0.0,
        predicted_price_7d=float(analysis["prediction"].get("target_price_7d", current_gold_price)),
        confidence_level=analysis["prediction"].get("confidence_level", "medium"),
        model_used=openrouter_model,
        raw_response=raw_response
    )
    db.add(llm_analysis)
    
    # Compute 7-day daily predictions via geometric interpolation
    target_price = float(analysis["prediction"].get("target_price_7d", current_gold_price))
    target_pct = ((target_price - current_gold_price) / current_gold_price * 100) if current_gold_price > 0 else 0.0
    
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
        vol_factor = {"low": 0.05, "medium": 0.03, "high": 0.015}[analysis["prediction"].get("confidence_level", "medium").lower()]
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
                "usd_inr": indicators.get("USD_INR"),
                "rbi_repo": indicators.get("RBI_REPO_RATE"),
                "cpi": indicators.get("INDIA_CPI")
            })
        )
        db.add(db_pred)
        
    db.commit()
    logger.info("LLM Analysis and interpolated predictions stored in database successfully.")
    return analysis

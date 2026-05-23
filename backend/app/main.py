from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import init_db
from app.api import prices, predictions, events, indicators, news, settings

from datetime import datetime, timedelta
import logging
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.database import SessionLocal
from app.services import yfinance_service, fred_service, data_ingestion, prediction_service
from app.api.predictions import run_llm_forecasting_pipeline
from app.utils.log_capture import setup_llm_log_capture

logger = logging.getLogger("goldsight_scheduler")

def update_gold_prices_job():
    db = SessionLocal()
    try:
        logger.info("Scheduler Triggered: Update Gold Prices")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        yfinance_service.fetch_gold_prices(db, start_date=start_date)
        yfinance_service.fetch_gold_prices_inr(db, start_date=start_date)
    except Exception as e:
        logger.error(f"Scheduler Error (update_gold_prices_job): {e}")
    finally:
        db.close()

def update_economic_indicators_job():
    db = SessionLocal()
    try:
        logger.info("Scheduler Triggered: Update Economic Indicators")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        yfinance_service.fetch_related_commodities(db, start_date=start_date)
        fred_service.fetch_all_indicators(db, start_date=start_date)
        fred_service.compute_real_interest_rate(db)
    except Exception as e:
        logger.error(f"Scheduler Error (update_economic_indicators_job): {e}")
    finally:
        db.close()

def update_news_job():
    db = SessionLocal()
    try:
        logger.info("Scheduler Triggered: Fetch & Score News")
        data_ingestion.run_daily_news_update(db)
    except Exception as e:
        logger.error(f"Scheduler Error (update_news_job): {e}")
    finally:
        db.close()

def run_predictions_job():
    db = SessionLocal()
    try:
        logger.info("Scheduler Triggered: Run ML Predictions")
        prediction_service.run_ml_predictions(db)
    except Exception as e:
        logger.error(f"Scheduler Error (run_predictions_job): {e}")
    finally:
        db.close()

def run_llm_predictions_job():
    db = SessionLocal()
    try:
        logger.info("Scheduler Triggered: Run LLM Predictions")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_llm_forecasting_pipeline(db))
        loop.close()
    except Exception as e:
        logger.error(f"Scheduler Error (run_llm_predictions_job): {e}")
    finally:
        db.close()

def backfill_actuals_job():
    db = SessionLocal()
    try:
        logger.info("Scheduler Triggered: Backfill Actual Prices")
        prediction_service.backfill_actuals(db)
    except Exception as e:
        logger.error(f"Scheduler Error (backfill_actuals_job): {e}")
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database (creates tables if they don't exist)
    init_db()
    
    # Initialize the log capture for the LLM console
    setup_llm_log_capture()
    
    # Configure and start background scheduler
    scheduler = BackgroundScheduler()
    
    # Schedule Gold Prices update (Daily at 6:30 PM IST / 13:00 UTC)
    scheduler.add_job(update_gold_prices_job, CronTrigger(hour=13, minute=0, timezone="UTC"))
    
    # Schedule Economic Indicators update (Daily at 7:00 PM IST / 13:30 UTC)
    scheduler.add_job(update_economic_indicators_job, CronTrigger(hour=13, minute=30, timezone="UTC"))
    
    # Schedule Backfill Actual Prices (Daily at 7:00 PM IST / 13:30 UTC)
    scheduler.add_job(backfill_actuals_job, CronTrigger(hour=13, minute=30, timezone="UTC"))
    
    # Schedule News Updates (Every 4 hours)
    scheduler.add_job(update_news_job, CronTrigger(hour="*/4", timezone="UTC"))
    
    # Schedule ML Predictions daily run (Daily at 8:00 PM IST / 14:30 UTC)
    scheduler.add_job(run_predictions_job, CronTrigger(hour=14, minute=30, timezone="UTC"))
    
    # Schedule LLM Predictions daily run (Daily at 8:30 PM IST / 15:00 UTC)
    scheduler.add_job(run_llm_predictions_job, CronTrigger(hour=15, minute=0, timezone="UTC"))
    
    scheduler.start()
    logger.info("Background Scheduler started successfully.")
    
    yield
    
    scheduler.shutdown()
    logger.info("Background Scheduler shut down.")

app = FastAPI(
    title="GoldSight API",
    description="Backend API for Gold Price Tracker & Predictor web application.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1):\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(prices.router, prefix="/api/prices", tags=["prices"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["predictions"])
app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(indicators.router, prefix="/api/indicators", tags=["indicators"])
app.include_router(news.router, prefix="/api/news", tags=["news"])
app.include_router(settings.router, prefix="/api", tags=["settings"])

@app.get("/api/health", tags=["health"])
def health_check():
    return {"status": "ok", "message": "GoldSight API is running."}

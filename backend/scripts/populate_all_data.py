import logging
import sys
import os

# Add parent directory to path so app can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, init_db
from app.services.yfinance_service import fetch_gold_prices, fetch_gold_prices_inr, fetch_related_commodities
from app.services.fred_service import fetch_all_indicators, compute_real_interest_rate
from app.models.schemas import GoldPrice, EconomicIndicator

# Set up logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("populate_all_data")

def main():
    logger.info("Initializing database...")
    init_db()
    
    db = SessionLocal()
    try:
        logger.info("=== Starting Data Ingestion Script (yfinance + FRED) ===")
        
        # 1. Fetch gold prices USD (20+ years)
        usd_rows = fetch_gold_prices(db, start_date="1996-01-01", currency="USD")
        logger.info(f"Gold prices USD processed: {usd_rows} new rows added.")
        
        # 2. Fetch gold prices INR (20+ years)
        inr_rows = fetch_gold_prices(db, start_date="1996-01-01", currency="INR")
        logger.info(f"Gold prices INR processed: {inr_rows} new rows added.")
        
        # 3. Fetch related commodities from yfinance
        yf_ind_rows = fetch_related_commodities(db, start_date="1996-01-01")
        logger.info(f"yfinance economic indicators processed: {yf_ind_rows} new rows added.")
        
        # 4. Fetch FRED indicators
        fred_rows = fetch_all_indicators(db, start_date="1996-01-01")
        logger.info(f"FRED economic indicators processed: {fred_rows} new rows added.")
        
        # 5. Compute derived indicators (real interest rate)
        real_rate_rows = compute_real_interest_rate(db)
        logger.info(f"REAL_RATE economic indicators computed: {real_rate_rows} new rows added.")
        
        # 6. Print summary
        total_gold_usd = db.query(GoldPrice).filter(GoldPrice.currency == "USD").count()
        total_gold_inr = db.query(GoldPrice).filter(GoldPrice.currency == "INR").count()
        total_indicators = db.query(EconomicIndicator).count()
        
        logger.info("=== Ingestion Summary ===")
        logger.info(f"Total Gold Prices (USD) in DB: {total_gold_usd}")
        logger.info(f"Total Gold Prices (INR) in DB: {total_gold_inr}")
        logger.info(f"Total Economic Indicators in DB: {total_indicators}")
        logger.info("=========================")
        
    except Exception as e:
        logger.exception(f"An error occurred during data population: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()

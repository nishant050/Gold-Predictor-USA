import logging
import sys
import os
import asyncio

# Add parent directory to path so app can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, init_db
from app.services.llm_service import run_llm_gold_analysis

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("generate_llm_predictions")

async def main():
    logger.info("Initializing DB and generating LLM predictions...")
    init_db()
    
    db = SessionLocal()
    try:
        analysis = await run_llm_gold_analysis(db)
        logger.info("=== LLM Analogy Result ===")
        logger.info(f"Summary: {analysis['current_situation_summary']}")
        logger.info(f"Direction: {analysis['prediction']['direction']}")
        logger.info(f"Predicted 7d change: {analysis['prediction']['predicted_change_percent']}%")
        logger.info(f"Predicted price 7d (USD): ${analysis['prediction'].get('predicted_price_7d', analysis['prediction'].get('predicted_price_30d', 0)):,.2f}")
        logger.info(f"Confidence: {analysis['prediction']['confidence']}")
        logger.info("==========================")
    except Exception as e:
        logger.exception(f"Error during LLM prediction generation: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())

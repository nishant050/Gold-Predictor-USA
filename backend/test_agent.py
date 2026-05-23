import asyncio
import logging
import sys

from app.database import SessionLocal
from app.services.llm_service import run_llm_gold_analysis

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

async def test_agent():
    db = SessionLocal()
    try:
        logging.info("Starting Agentic LLM run...")
        result = await run_llm_gold_analysis(db)
        logging.info("Result:")
        logging.info(result)
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_agent())

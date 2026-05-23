import asyncio
import logging
import sys

from app.database import SessionLocal
from app.models.schemas import AppSetting
from app.services.llm_service import run_llm_gold_analysis

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

async def test_settings():
    db = SessionLocal()
    try:
        # Save a custom model to the database
        custom_model = "anthropic/claude-3.5-sonnet"
        setting = db.query(AppSetting).filter(AppSetting.setting_key == "openrouter_model").first()
        if not setting:
            setting = AppSetting(setting_key="openrouter_model", setting_value=custom_model)
            db.add(setting)
        else:
            setting.setting_value = custom_model
        db.commit()
        
        logging.info(f"Set model to: {custom_model}. Running analysis...")
        
        # Run agentic loop (this will fail quickly if key doesn't support the model, but we just want to see the logger output)
        try:
            result = await run_llm_gold_analysis(db)
            logging.info("Result:")
            logging.info(result)
        except Exception as e:
            logging.info(f"Failed (expected if API key doesn't support this model or hits rate limit): {e}")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_settings())

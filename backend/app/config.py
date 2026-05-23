import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    fred_api_key: str
    nyt_api_key: str
    nyt_api_secret: str
    guardian_api_key: str
    news_api_key: str
    gold_api_key: str
    openrouter_api_key: str
    openrouter_model: str = "poolside/laguna-m.1:free"
    currencies: str = "USD,INR"
    prediction_days: int = 30
    llm_max_tool_calls: int = 15

    # Look for .env file in the backend directory
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

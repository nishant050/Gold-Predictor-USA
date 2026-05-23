from sqlalchemy import Column, Integer, Float, String, Date, DateTime, Text, UniqueConstraint, Index
from app.database import Base

class GoldPrice(Base):
    __tablename__ = "gold_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, index=True, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=True)
    currency = Column(String(10), default="USD", nullable=False)
    source = Column(String(50), nullable=False)

    __table_args__ = (
        UniqueConstraint("date", "currency", name="uq_date_currency"),
    )


class EconomicIndicator(Base):
    __tablename__ = "economic_indicators"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, index=True, nullable=False)
    indicator_name = Column(String(50), index=True, nullable=False)
    value = Column(Float, nullable=False)
    source = Column(String(50), nullable=False)

    __table_args__ = (
        UniqueConstraint("date", "indicator_name", name="uq_date_indicator"),
    )


class HistoricalEvent(Base):
    __tablename__ = "historical_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_date = Column(Date, index=True, nullable=False)
    event_end_date = Column(Date, nullable=True)
    event_type = Column(String(50), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    impact_level = Column(Integer, nullable=False)  # Scale 1-5
    gold_price_at_event = Column(Float, nullable=True)
    gold_price_change_7d = Column(Float, nullable=True)
    gold_price_change_30d = Column(Float, nullable=True)
    gold_price_change_90d = Column(Float, nullable=True)
    tags = Column(Text, nullable=True)  # JSON array string
    source = Column(String(100), nullable=False)


class NewsSentiment(Base):
    __tablename__ = "news_sentiment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, index=True, nullable=False)
    headline = Column(Text, nullable=False)
    source_name = Column(String(100), nullable=False)
    url = Column(Text, nullable=True)
    sentiment_score = Column(Float, nullable=False)  # -1.0 to 1.0
    sentiment_label = Column(String(20), nullable=False)  # 'positive', 'negative', 'neutral'
    relevance_score = Column(Float, nullable=True)  # 0-1
    category = Column(String(50), nullable=True)


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prediction_date = Column(Date, index=True, nullable=False)  # when prediction was made
    target_date = Column(Date, nullable=False)  # date being predicted
    predicted_price = Column(Float, nullable=False)
    confidence_low_80 = Column(Float, nullable=True)
    confidence_high_80 = Column(Float, nullable=True)
    confidence_low_95 = Column(Float, nullable=True)
    confidence_high_95 = Column(Float, nullable=True)
    actual_price = Column(Float, nullable=True)  # filled later
    model_version = Column(String(50), nullable=False)
    prediction_method = Column(String(20), nullable=False)  # 'ml' or 'llm'
    features_used = Column(Text, nullable=True)  # JSON

    __table_args__ = (
        Index("ix_predictions_method_date", "prediction_method", "prediction_date"),
    )


class LLMAnalysis(Base):
    __tablename__ = "llm_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_date = Column(Date, index=True, nullable=False)
    current_events_summary = Column(Text, nullable=False)  # what news/events the LLM saw
    similar_historical_events = Column(Text, nullable=False)  # JSON array of similar events found
    historical_outcomes = Column(Text, nullable=False)  # what happened to gold in those cases
    reasoning = Column(Text, nullable=False)  # LLM's reasoning chain
    predicted_direction = Column(String(10), nullable=False)  # 'up', 'down', 'flat'
    predicted_change_percent = Column(Float, nullable=False)  # predicted % change
    predicted_price_7d = Column(Float, nullable=False)
    confidence_level = Column(String(20), nullable=False)  # 'low', 'medium', 'high'
    model_used = Column(String(100), nullable=False)
    raw_response = Column(Text, nullable=False)  # full LLM response for debugging


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(String(20), nullable=False)
    model_type = Column(String(50), nullable=False)  # 'xgboost', 'lstm', 'ensemble'
    trained_date = Column(DateTime, nullable=False)
    training_mape = Column(Float, nullable=False)
    validation_mape = Column(Float, nullable=False)
    test_mape = Column(Float, nullable=True)
    directional_accuracy = Column(Float, nullable=True)
    features = Column(Text, nullable=False)  # JSON list
    hyperparameters = Column(Text, nullable=False)  # JSON dict
    model_path = Column(String(500), nullable=False)


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(50), index=True, nullable=False) # 'goldapi', 'fred', 'openrouter', 'newsapi', 'guardian', 'nyt'
    key_value = Column(String(200), nullable=False)
    is_active = Column(Integer, default=1, nullable=False) # 1 active, 0 exhausted
    exhausted_until = Column(DateTime, nullable=True) # auto-resets after this
    is_primary = Column(Integer, default=0, nullable=False) # 1 if this is the default key

class AppSetting(Base):
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    setting_key = Column(String(100), unique=True, index=True, nullable=False)
    setting_value = Column(String(500), nullable=False)

import logging
from datetime import date, timedelta
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.models.schemas import Prediction, GoldPrice, ModelVersion
from app.ml.feature_engineering import fetch_raw_data, build_features
from app.ml.xgboost_model import forecast_ml_models
from app.ml.arima_model import train_and_forecast_arima
from app.ml.ensemble import blend_predictions

logger = logging.getLogger(__name__)

def run_ml_predictions(db: Session) -> int:
    """
    Generate ML ensemble predictions for next 30 days and save them in the DB.
    """
    logger.info("Starting ML prediction run...")
    try:
        # Fetch latest USD exchange rate or calculate it
        latest_inr = db.query(GoldPrice).filter(GoldPrice.currency == "INR").order_by(desc(GoldPrice.date)).first()
        latest_usd = db.query(GoldPrice).filter(GoldPrice.currency == "USD").order_by(desc(GoldPrice.date)).first()
        if latest_inr and latest_usd and latest_usd.close != 0:
            rate = latest_inr.close / latest_usd.close
        else:
            rate = 83.5
            
        df_raw = fetch_raw_data(db, currency="USD")
        df_features = build_features(df_raw)
        
        latest_date = df_features.index.max()
        latest_row = df_features.loc[latest_date]
        current_price = float(latest_row["close"])
        
        ml_preds = forecast_ml_models(latest_row.to_dict(), current_price, steps=30)
        arima_res = train_and_forecast_arima(df_features["close"], steps=30)
        blended_preds = blend_predictions(arima_res["predictions"], ml_preds)
        
        today_date = date.today()
        # Remove existing ML predictions for today
        db.query(Prediction).filter(
            Prediction.prediction_date == today_date,
            Prediction.prediction_method == "ml"
        ).delete()
        
        for p in blended_preds:
            target_date = today_date + timedelta(days=p["step"])
            
            # Save USD prediction
            db.add(Prediction(
                prediction_date=today_date,
                target_date=target_date,
                predicted_price=p["predicted_price"],
                confidence_low_80=p["confidence_low_80"],
                confidence_high_80=p["confidence_high_80"],
                confidence_low_95=p["confidence_low_95"],
                confidence_high_95=p["confidence_high_95"],
                model_version="ensemble_v1",
                prediction_method="ml",
                features_used="{}"
            ))
            
            # Save INR prediction
            db.add(Prediction(
                prediction_date=today_date,
                target_date=target_date,
                predicted_price=round(p["predicted_price"] * rate, 2),
                confidence_low_80=round(p["confidence_low_80"] * rate, 2),
                confidence_high_80=round(p["confidence_high_80"] * rate, 2),
                confidence_low_95=round(p["confidence_low_95"] * rate, 2),
                confidence_high_95=round(p["confidence_high_95"] * rate, 2),
                model_version="ensemble_v1_inr",
                prediction_method="ml",
                features_used="{}"
            ))
            
        db.commit()
        logger.info("Successfully generated and stored ML ensemble predictions.")
        return len(blended_preds)
    except Exception as e:
        logger.error(f"Error in run_ml_predictions: {e}")
        db.rollback()
        raise e

def backfill_actuals(db: Session) -> int:
    """
    Query predictions where actual_price is null and target_date <= today.
    For each, lookup actual gold price from gold_prices table.
    Update actual_price field.
    """
    logger.info("Backfilling actual gold prices for past predictions...")
    today = date.today()
    unfilled_preds = db.query(Prediction).filter(
        Prediction.actual_price.is_(None),
        Prediction.target_date <= today
    ).all()
    
    if not unfilled_preds:
        logger.info("No predictions to backfill.")
        return 0
        
    backfilled_count = 0
    target_dates = [p.target_date for p in unfilled_preds]
    min_date = min(target_dates)
    max_date = max(target_dates)
    
    # Query gold prices for USD and INR
    gold_usd = db.query(GoldPrice).filter(
        GoldPrice.currency == "USD",
        GoldPrice.date >= min_date,
        GoldPrice.date <= max_date
    ).all()
    
    gold_inr = db.query(GoldPrice).filter(
        GoldPrice.currency == "INR",
        GoldPrice.date >= min_date,
        GoldPrice.date <= max_date
    ).all()
    
    prices_usd = {p.date: p.close for p in gold_usd}
    prices_inr = {p.date: p.close for p in gold_inr}
    
    for pred in unfilled_preds:
        currency = "INR" if "inr" in pred.model_version.lower() else "USD"
        prices_dict = prices_inr if currency == "INR" else prices_usd
        
        actual_price = prices_dict.get(pred.target_date)
        if actual_price is None:
            # Check if there is an exact match in the DB on or before the target date
            nearest_price = db.query(GoldPrice).filter(
                GoldPrice.currency == currency,
                GoldPrice.date <= pred.target_date
            ).order_by(desc(GoldPrice.date)).first()
            if nearest_price:
                actual_price = nearest_price.close
                
        if actual_price is not None:
            pred.actual_price = actual_price
            backfilled_count += 1
            
    db.commit()
    logger.info(f"Backfilled actual prices for {backfilled_count} prediction rows.")
    return backfilled_count

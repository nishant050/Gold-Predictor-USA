import logging
import sys
import os
import json
from datetime import datetime, date, timedelta

# Add parent directory to path so app can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, init_db
from app.models.schemas import Prediction, GoldPrice
from app.ml.feature_engineering import fetch_raw_data, build_features
from app.ml.xgboost_model import forecast_ml_models
from app.ml.arima_model import load_and_forecast_arima
from app.ml.ensemble import blend_predictions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("generate_predictions")

def main():
    logger.info("Initializing DB and starting ML prediction generation...")
    init_db()
    
    db = SessionLocal()
    try:
        # 1. Fetch raw data
        logger.info("Fetching raw price/indicator series...")
        df_raw, df_events = fetch_raw_data(db, currency="INR")
        
        # 2. Build features
        df_features = build_features(df_raw, df_events)
        
        # 2. Extract latest values for prediction
        latest_date = df_features.index.max()
        latest_row = df_features.loc[latest_date]
        current_price = float(latest_row["close"])
        
        logger.info(f"Generating predictions from latest date: {latest_date.date()} at price ${current_price:,.2f}")
        
        # Convert row to dictionary for ML forecasting
        latest_features_dict = latest_row.to_dict()
        
        # 3. Forecast using ML models (XGBoost/RF)
        logger.info("Forecasting with ML regression ensemble...")
        ml_preds = forecast_ml_models(latest_features_dict, current_price, steps=7)
        
        # 4. Forecast using ARIMA model
        logger.info("Forecasting with ARIMA model...")
        arima_res = load_and_forecast_arima(df_features["close"], steps=7)
        arima_preds = arima_res["predictions"]
        
        # 5. Blend Predictions
        logger.info("Blending forecasts and computing confidence intervals...")
        blended_preds = blend_predictions(arima_preds, ml_preds, current_price, w_arima=0.4, w_ml=0.6)
        
        # 6. Save blended predictions to database
        logger.info("Saving predictions to database...")
        
        today_date = date.today()
        # Delete old predictions made today
        db.query(Prediction).filter(
            Prediction.prediction_date == today_date,
            Prediction.prediction_method == "ml"
        ).delete()
        
        # We also need to predict INR prices by multiplying USD prediction by the latest USD/INR exchange rate!
        # Let's find the latest USD_INR exchange rate
        latest_inr = db.query(GoldPrice).filter(GoldPrice.currency == "INR").order_by(GoldPrice.date.desc()).first()
        latest_usd = db.query(GoldPrice).filter(GoldPrice.currency == "USD").order_by(GoldPrice.date.desc()).first()
        
        usd_inr_rate = 83.5  # fallback
        if latest_inr and latest_usd:
            usd_inr_rate = latest_inr.close / latest_usd.close
            
        logger.info(f"USD to INR Conversion Rate: {usd_inr_rate:.4f}")
        
        for p in blended_preds:
            target_date = today_date + timedelta(days=p["step"])
            
            # Save INR prediction (Native)
            inr_pred = Prediction(
                prediction_date=today_date,
                target_date=target_date,
                predicted_price=round(p["predicted_price"], 2),
                confidence_low_80=round(p["confidence_low_80"], 2),
                confidence_high_80=round(p["confidence_high_80"], 2),
                confidence_low_95=round(p["confidence_low_95"], 2),
                confidence_high_95=round(p["confidence_high_95"], 2),
                model_version="ensemble_v1_inr",
                prediction_method="ml",
                features_used=json.dumps({
                    "current_price": current_price,
                    "date": latest_date.date().isoformat()
                })
            )
            db.add(inr_pred)
            
            # Save USD prediction (Converted)
            usd_pred = Prediction(
                prediction_date=today_date,
                target_date=target_date,
                predicted_price=round(p["predicted_price"] / usd_inr_rate, 2),
                confidence_low_80=round(p["confidence_low_80"] / usd_inr_rate, 2),
                confidence_high_80=round(p["confidence_high_80"] / usd_inr_rate, 2),
                confidence_low_95=round(p["confidence_low_95"] / usd_inr_rate, 2),
                confidence_high_95=round(p["confidence_high_95"] / usd_inr_rate, 2),
                model_version="ensemble_v1",
                prediction_method="ml",
                features_used=json.dumps({
                    "current_price": current_price / usd_inr_rate,
                    "usd_inr_rate": usd_inr_rate,
                    "date": latest_date.date().isoformat()
                })
            )
            db.add(usd_pred)
            
        db.commit()
        logger.info(f"Successfully generated and saved 7-day ML forecasts for USD and INR.")
        logger.info("====================================")
        
    except Exception as e:
        logger.exception(f"Error during ML prediction generation: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()

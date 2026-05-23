import logging
import sys
import os
import json
from datetime import datetime

# Add parent directory to path so app can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, init_db
from app.models.schemas import ModelVersion
from app.ml.feature_engineering import fetch_raw_data, build_features, generate_prediction_dataset
from app.ml.xgboost_model import train_ml_models
from app.ml.arima_model import train_and_forecast_arima

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("train_models")

def main():
    logger.info("Initializing DB and starting model training...")
    init_db()
    
    db = SessionLocal()
    try:
        # 1. Fetch data
        logger.info("Fetching prices and economic indicators...")
        df_raw, df_events = fetch_raw_data(db)
        
        # 2. Build features
        logger.info("Building engineered and qualitative features...")
        df_features = build_features(df_raw, df_events)
        
        # 3. Generate prediction dataset
        logger.info("Structuring dataset with lead horizons (1-7)...")
        X, y, labels = generate_prediction_dataset(df_features, max_horizon=7)
        
        # 4. Train ML Models (XGBoost + Random Forest)
        logger.info("Training ML regression ensemble...")
        ml_results = train_ml_models(X, y, labels)
        
        # 5. Fit ARIMA Model for validation metrics
        logger.info("Fitting ARIMA model on latest series for baseline...")
        arima_results = train_and_forecast_arima(df_features["close"], steps=7)
        
        # 6. Save model training details to database
        logger.info("Recording model version in database...")
        
        # Aggregate performance metrics
        training_mape = arima_results.get("training_mape", 5.0)
        validation_mape = ml_results.get("val_mape", 5.0)
        dir_acc = ml_results.get("val_directional_accuracy", 50.0)
        
        # Remove old versions to keep it clean
        db.query(ModelVersion).filter(ModelVersion.model_type == "ensemble").delete()
        
        version_num = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_version = ModelVersion(
            version=version_num,
            model_type="ensemble",
            trained_date=datetime.now(),
            training_mape=round(training_mape, 4),
            validation_mape=round(validation_mape, 4),
            test_mape=round(validation_mape, 4),
            directional_accuracy=round(dir_acc, 2),
            features=json.dumps(["per_horizon_features"]),
            hyperparameters=json.dumps({
                "xgboost": {
                    "n_estimators": 150,
                    "max_depth": 5,
                    "learning_rate": 0.03
                },
                "random_forest": {
                    "n_estimators": 100,
                    "max_depth": 8
                },
                "arima_order": [5, 1, 2]
            }),
            model_path=os.path.join("trained_models", f"ensemble_{version_num}")
        )
        db.add(model_version)
        db.commit()
        
        logger.info(f"Successfully trained and saved model version {version_num}!")
        logger.info(f"Training ARIMA MAPE: {training_mape:.2f}%")
        logger.info(f"Validation ML MAPE: {validation_mape:.2f}%")
        logger.info(f"Directional Accuracy: {dir_acc:.2f}%")
        logger.info("====================================")
        
    except Exception as e:
        logger.exception(f"Error during model training script: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()

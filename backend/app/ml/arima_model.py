from statsmodels.tsa.arima.model import ARIMA, ARIMAResults
import pandas as pd
import numpy as np
import logging
import os

logger = logging.getLogger(__name__)

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "trained_models")

def save_arima_model(model_fit):
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)
    model_fit.save(os.path.join(MODELS_DIR, "arima_model.zip"))

def train_and_forecast_arima(series: pd.Series, steps: int = 7, order=(5, 1, 2)) -> dict:
    """
    Fit an ARIMA model on the historical series, save it to disk, and forecast 'steps' ahead.
    Returns a dictionary with predictions and confidence intervals.
    """
    logger.info(f"Fitting ARIMA{order} model on {len(series)} values...")
    
    try:
        model = ARIMA(series, order=order)
        model_fit = model.fit()
        
        # Save fitted model
        save_arima_model(model_fit)
        
        # Forecast
        forecast_res = model_fit.get_forecast(steps=steps)
        forecast_mean = forecast_res.summary_frame()["mean"].values
        forecast_ci_80 = forecast_res.summary_frame(alpha=0.20)  # 80% CI
        forecast_ci_95 = forecast_res.summary_frame(alpha=0.05)  # 95% CI
        
        # Clean predictions
        predictions = []
        for i in range(steps):
            pred_val = float(forecast_mean[i])
            ci_80_lower = float(forecast_ci_80.iloc[i]["mean_ci_lower"])
            ci_80_upper = float(forecast_ci_80.iloc[i]["mean_ci_upper"])
            ci_95_lower = float(forecast_ci_95.iloc[i]["mean_ci_lower"])
            ci_95_upper = float(forecast_ci_95.iloc[i]["mean_ci_upper"])
            
            # Bound below by 0
            predictions.append({
                "step": i + 1,
                "predicted_price": round(max(0.0, pred_val), 2),
                "confidence_low_80": round(max(0.0, ci_80_lower), 2),
                "confidence_high_80": round(max(0.0, ci_80_upper), 2),
                "confidence_low_95": round(max(0.0, ci_95_lower), 2),
                "confidence_high_95": round(max(0.0, ci_95_upper), 2)
            })
            
        # Compute MAPE on training data as validation metric
        in_sample = model_fit.predict()
        # Drop the first d values
        actuals = series.values[order[1]:]
        preds = in_sample.values[order[1]:]
        mape = float(np.mean(np.abs((actuals - preds) / actuals)) * 100)
        
        logger.info(f"ARIMA model fitted and saved successfully. Training MAPE: {mape:.2f}%")
        
        return {
            "predictions": predictions,
            "training_mape": mape,
            "model_summary": str(model_fit.summary())
        }
        
    except Exception as e:
        logger.exception(f"Error training/forecasting ARIMA: {e}")
        # Fallback: Simple drift/naive model
        last_val = float(series.iloc[-1])
        predictions = []
        for i in range(steps):
            predictions.append({
                "step": i + 1,
                "predicted_price": last_val,
                "confidence_low_80": last_val * 0.95,
                "confidence_high_80": last_val * 1.05,
                "confidence_low_95": last_val * 0.90,
                "confidence_high_95": last_val * 1.10
            })
        return {
            "predictions": predictions,
            "training_mape": 5.0,
            "error": str(e)
        }

def load_and_forecast_arima(series: pd.Series, steps: int = 7) -> dict:
    """
    Load pre-trained ARIMA model, apply to latest series (without refitting), and forecast.
    """
    try:
        model_path = os.path.join(MODELS_DIR, "arima_model.zip")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"ARIMA model file not found at {model_path}")
            
        model_fit = ARIMAResults.load(model_path)
        # Apply model to latest series to update filters/states
        updated_fit = model_fit.apply(series)
        
        # Forecast
        forecast_res = updated_fit.get_forecast(steps=steps)
        forecast_mean = forecast_res.summary_frame()["mean"].values
        forecast_ci_80 = forecast_res.summary_frame(alpha=0.20)
        forecast_ci_95 = forecast_res.summary_frame(alpha=0.05)
        
        predictions = []
        for i in range(steps):
            pred_val = float(forecast_mean[i])
            ci_80_lower = float(forecast_ci_80.iloc[i]["mean_ci_lower"])
            ci_80_upper = float(forecast_ci_80.iloc[i]["mean_ci_upper"])
            ci_95_lower = float(forecast_ci_95.iloc[i]["mean_ci_lower"])
            ci_95_upper = float(forecast_ci_95.iloc[i]["mean_ci_upper"])
            
            predictions.append({
                "step": i + 1,
                "predicted_price": round(max(0.0, pred_val), 2),
                "confidence_low_80": round(max(0.0, ci_80_lower), 2),
                "confidence_high_80": round(max(0.0, ci_80_upper), 2),
                "confidence_low_95": round(max(0.0, ci_95_lower), 2),
                "confidence_high_95": round(max(0.0, ci_95_upper), 2)
            })
            
        return {
            "predictions": predictions,
            "success": True
        }
    except Exception as e:
        logger.exception(f"Error loading/forecasting ARIMA: {e}")
        # Fallback: Simple drift/naive model
        last_val = float(series.iloc[-1])
        predictions = []
        for i in range(steps):
            predictions.append({
                "step": i + 1,
                "predicted_price": last_val,
                "confidence_low_80": last_val * 0.95,
                "confidence_high_80": last_val * 1.05,
                "confidence_low_95": last_val * 0.90,
                "confidence_high_95": last_val * 1.10
            })
        return {
            "predictions": predictions,
            "success": False,
            "error": str(e)
        }

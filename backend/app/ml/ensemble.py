import numpy as np
import logging

logger = logging.getLogger(__name__)

def blend_predictions(
    arima_preds: list,
    ml_preds: list,
    current_price: float,
    w_arima: float = 0.4,
    w_ml: float = 0.6
) -> list:
    """
    Blends ARIMA and ML model predictions and computes combined confidence intervals.
    """
    logger.info("Blending ARIMA and ML model forecasts...")
    
    blended = []
    
    # Ensure they have the same length
    length = min(len(arima_preds), len(ml_preds))
    
    for i in range(length):
        ap = arima_preds[i]
        mp = ml_preds[i]
        
        # Weighted price
        blended_price = w_arima * ap["predicted_price"] + w_ml * mp["predicted_price"]
        
        # Estimate ARIMA standard deviation
        # 80% CI z-score is ~1.282, so CI width = 2 * 1.282 * std => std = width / 2.564
        arima_price_std = (ap["confidence_high_80"] - ap["confidence_low_80"]) / 2.564
        
        # Get ML price standard deviation (from Random Forest tree variance)
        ml_price_std = mp.get("price_std", 0.0)
        
        # Fallback to ARIMA std if ML std is not computed or 0
        if ml_price_std <= 0.0:
            ml_price_std = arima_price_std
            
        # Combine standard deviations (weighted average)
        # We also add a small horizon expansion factor for step (widen for longer horizons)
        step = ap["step"]
        horizon_factor = 1.0 + (step / 7) * 0.1  # Fixed: max_horizon is 7 now
        
        blended_std = (w_arima * arima_price_std + w_ml * ml_price_std) * horizon_factor
        
        # Direction-aware blending override
        ml_direction = mp.get("predicted_direction", 0)
        ml_direction_prob = mp.get("direction_prob", 0.0)
        
        # If classifier is highly confident (>60%), ensure the blended price reflects that direction
        # We only override if the regressor contradicts the classifier
        if ml_direction == 1 and ml_direction_prob > 0.60:
            if blended_price <= current_price:
                # Force an upward move (minimum +0.1%)
                blended_price = current_price * 1.001
        elif ml_direction == -1 and ml_direction_prob > 0.60:
            if blended_price >= current_price:
                # Force a downward move (minimum -0.1%)
                blended_price = current_price * 0.999
        elif ml_direction == 0 and ml_direction_prob > 0.60:
            # Force flat
            if abs((blended_price - current_price) / current_price) > 0.001:
                blended_price = current_price
                
        # Calculate confidence intervals based on blended standard deviation
        conf_low_80 = blended_price - 1.282 * blended_std
        conf_high_80 = blended_price + 1.282 * blended_std
        conf_low_95 = blended_price - 1.960 * blended_std
        conf_high_95 = blended_price + 1.960 * blended_std
        
        blended.append({
            "step": step,
            "predicted_price": round(max(0.0, blended_price), 2),
            "confidence_low_80": round(max(0.0, conf_low_80), 2),
            "confidence_high_80": round(max(0.0, conf_high_80), 2),
            "confidence_low_95": round(max(0.0, conf_low_95), 2),
            "confidence_high_95": round(max(0.0, conf_high_95), 2)
        })
        
    logger.info("Forecasting blending complete.")
    return blended

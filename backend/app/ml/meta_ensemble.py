import os
import pickle
import numpy as np
import pandas as pd
import logging
from sklearn.linear_model import LogisticRegression

logger = logging.getLogger(__name__)

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "trained_models")
META_MODEL_PATH = os.path.join(MODELS_DIR, "meta_model.pkl")

def train_meta_ensemble(ml_history: list, llm_history: list):
    """
    Trains a stacking layer to learn when to trust ML vs LLM.
    Requires historical data where we have BOTH ML and LLM predictions for the same dates.
    
    Expected format for each row:
    {
       "ml_predicted_direction": 1,
       "ml_direction_prob": 0.65,
       "llm_predicted_direction": -1,
       "llm_confidence_score": 0.8,
       "vix_level": 25.4,
       "regime_war": 1,
       "actual_direction": -1
    }
    """
    # Wait until we have enough historical LLM predictions to train this
    if len(ml_history) < 60:
        logger.info("Not enough LLM history to train meta-ensemble (< 60 samples). Skipping.")
        return
        
    df = pd.DataFrame(ml_history)  # join with llm_history logic here
    
    X = df[["ml_predicted_direction", "ml_direction_prob", 
            "llm_predicted_direction", "llm_confidence_score", 
            "vix_level", "regime_war"]]
    y = df["actual_direction"]
    
    meta_model = LogisticRegression()
    meta_model.fit(X, y)
    
    with open(META_MODEL_PATH, "wb") as f:
        pickle.dump(meta_model, f)
        
    logger.info("Meta-ensemble trained and saved.")

def get_meta_blend(ml_pred: dict, llm_pred: dict, current_features: dict) -> dict:
    """
    Uses the trained meta-model to decide the final blended prediction.
    If no meta-model exists, relies on the direction-aware ML heuristic.
    """
    if not os.path.exists(META_MODEL_PATH) or not llm_pred:
        # Fallback to ML heuristic
        return ml_pred
        
    try:
        with open(META_MODEL_PATH, "rb") as f:
            meta_model = pickle.load(f)
            
        # Extract features for meta-model
        X_infer = pd.DataFrame([{
            "ml_predicted_direction": ml_pred.get("predicted_direction", 0),
            "ml_direction_prob": ml_pred.get("direction_prob", 0.5),
            "llm_predicted_direction": 1 if llm_pred.get("predicted_direction") == "up" else (-1 if llm_pred.get("predicted_direction") == "down" else 0),
            "llm_confidence_score": {"low": 0.33, "medium": 0.66, "high": 0.99}.get(llm_pred.get("confidence_level", "medium")),
            "vix_level": current_features.get("VIX", 20.0),
            "regime_war": current_features.get("regime_war", 0)
        }])
        
        final_dir = meta_model.predict(X_infer)[0]
        final_prob = np.max(meta_model.predict_proba(X_infer)[0])
        
        # Override the ML prediction with meta-model's choice
        ml_pred["predicted_direction"] = int(final_dir)
        ml_pred["direction_prob"] = float(final_prob)
        return ml_pred
        
    except Exception as e:
        logger.error(f"Failed to use meta-ensemble: {e}")
        return ml_pred

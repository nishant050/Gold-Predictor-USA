import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import accuracy_score
import pandas as pd
import numpy as np
import pickle
import json
import os
import logging
from collections import Counter
from app.ml.backtester import PurgedTimeSeriesSplit, create_train_test_split

logger = logging.getLogger(__name__)

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "trained_models")

def train_ml_models(X: pd.DataFrame, y: np.ndarray, labels: np.ndarray) -> dict:
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)
        
    cols_to_drop = ["_date_idx", "_close_t", "horizon"]
    
    # --- Final Train / Held-Out Test Split ---
    logger.info("Creating Train / Held-Out Test split (Test >= 2024)...")
    X_train_full, y_train_full, lbl_train_full, X_test_full, y_test_full, lbl_test_full = create_train_test_split(
        X, y, labels, test_start_date="2024-01-01"
    )
    
    xgb_models = {}
    rf_models = {}
    xgb_clfs = {}
    metadata = {}
    
    total_val_mape = 0.0
    total_dir_acc = 0.0
    
    # We will train separate models for each horizon (1 to 7)
    for h in range(1, 8):
        logger.info(f"--- Training models for Horizon {h} ---")
        
        # Filter for current horizon
        h_train_mask = X_train_full["horizon"] == h
        X_h_train = X_train_full[h_train_mask]
        y_h_train = y_train_full[h_train_mask]
        lbl_h_train = lbl_train_full[h_train_mask]
        
        h_test_mask = X_test_full["horizon"] == h
        X_h_test = X_test_full[h_test_mask]
        y_h_test = y_test_full[h_test_mask]
        lbl_h_test = lbl_test_full[h_test_mask]
        
        X_tr = X_h_train.drop(columns=cols_to_drop)
        X_te = X_h_test.drop(columns=cols_to_drop)
        feature_names = list(X_tr.columns)
        
        # 1. Feature Pruning Pass
        xgb_reg_init = xgb.XGBRegressor(n_estimators=80, max_depth=3, learning_rate=0.05, n_jobs=-1, random_state=42)
        xgb_reg_init.fit(X_tr, y_h_train)
        
        rf_reg_init = RandomForestRegressor(n_estimators=50, max_depth=4, n_jobs=-1, random_state=42)
        rf_reg_init.fit(X_tr, y_h_train)
        
        xgb_clf_init = xgb.XGBClassifier(n_estimators=80, max_depth=3, learning_rate=0.05, n_jobs=-1, random_state=42)
        xgb_clf_init.fit(X_tr, lbl_h_train + 1)
        
        avg_imp = (xgb_reg_init.feature_importances_ + rf_reg_init.feature_importances_ + xgb_clf_init.feature_importances_) / 3
        
        # Drop bottom 30% features
        num_to_drop = int(len(feature_names) * 0.3)
        drop_indices = np.argsort(avg_imp)[:num_to_drop]
        features_to_keep = [feature_names[i] for i in range(len(feature_names)) if i not in drop_indices]
        
        X_tr_pruned = X_tr[features_to_keep]
        X_te_pruned = X_te[features_to_keep]
        
        # ============================================================
        # FIX 3: Exponential Recency Weighting
        # ============================================================
        train_dates = pd.to_datetime(X_h_train["_date_idx"])
        years_ago = (pd.Timestamp("2024-01-01") - train_dates).dt.days / 365.25
        years_ago = years_ago.clip(lower=0)  # safety
        
        decay_rate = 0.12
        sample_weights = np.exp(-decay_rate * years_ago.values)
        sample_weights = sample_weights / sample_weights.mean()
        
        # 2. Final Training
        xgb_model = xgb.XGBRegressor(
            n_estimators=500, max_depth=3, learning_rate=0.02,
            subsample=0.7, colsample_bytree=0.6, 
            min_child_weight=10, gamma=0.1,
            reg_alpha=2.0, reg_lambda=10.0,
            random_state=42, n_jobs=-1,
            early_stopping_rounds=30
        )
        split_idx = int(len(X_tr_pruned) * 0.85)
        X_tr_fit = X_tr_pruned.iloc[:split_idx]
        y_tr_fit = y_h_train[:split_idx]
        X_tr_eval = X_tr_pruned.iloc[split_idx:]
        y_tr_eval = y_h_train[split_idx:]
        xgb_model.fit(
            X_tr_fit, y_tr_fit,
            eval_set=[(X_tr_eval, y_tr_eval)],
            verbose=False,
            sample_weight=sample_weights[:split_idx]
        )
        
        rf_model = RandomForestRegressor(
            n_estimators=200, max_depth=4, min_samples_split=20, min_samples_leaf=10,
            max_features=0.5,
            random_state=42, n_jobs=-1
        )
        rf_model.fit(X_tr_pruned, y_h_train, sample_weight=sample_weights)
        
        xgb_clf = xgb.XGBClassifier(
            n_estimators=500, max_depth=3, learning_rate=0.02,
            subsample=0.7, colsample_bytree=0.6,
            min_child_weight=10, gamma=0.1,
            reg_alpha=2.0, reg_lambda=10.0,
            random_state=42, n_jobs=-1,
            early_stopping_rounds=30
        )
        xgb_clf.fit(
            X_tr_fit, lbl_h_train[:split_idx] + 1,
            eval_set=[(X_tr_eval, lbl_h_train[split_idx:] + 1)],
            verbose=False,
            sample_weight=sample_weights[:split_idx]
        )
        
        # 3. Evaluation on Held-Out Test Set
        xgb_pred = xgb_model.predict(X_te_pruned)
        rf_pred = rf_model.predict(X_te_pruned)
        
        xgb_mae = np.mean(np.abs(y_h_test - xgb_pred))
        rf_mae = np.mean(np.abs(y_h_test - rf_pred))
        
        total_inv_mae = (1/max(xgb_mae, 1e-5)) + (1/max(rf_mae, 1e-5))
        w_xgb = (1/max(xgb_mae, 1e-5)) / total_inv_mae
        w_rf = (1/max(rf_mae, 1e-5)) / total_inv_mae
        
        ensemble_pred = w_xgb * xgb_pred + w_rf * rf_pred
        
        close_te = X_h_test["_close_t"].values
        actual_prices = close_te * (1 + y_h_test / 100)
        pred_prices = close_te * (1 + ensemble_pred / 100)
        mape = float(np.mean(np.abs(actual_prices - pred_prices) / np.maximum(actual_prices, 1e-5)) * 100)
        
        clf_pred = xgb_clf.predict(X_te_pruned) - 1
        
        meaningful_mask = (lbl_h_test != 0)
        if meaningful_mask.sum() > 0:
            dir_acc = float(accuracy_score(lbl_h_test[meaningful_mask], clf_pred[meaningful_mask]) * 100)
        else:
            dir_acc = 0.0
            
        # Baseline comparison
        up_count = (lbl_h_test[meaningful_mask] == 1).sum()
        down_count = (lbl_h_test[meaningful_mask] == -1).sum()
        baseline = max(up_count, down_count) / meaningful_mask.sum() * 100 if meaningful_mask.sum() > 0 else 0
        
        logger.info(f"Horizon {h} Results - MAPE: {mape:.2f}%, DirAcc: {dir_acc:.2f}% (Baseline: {baseline:.2f}%)")
        
        total_val_mape += mape
        total_dir_acc += dir_acc
        
        xgb_models[h] = xgb_model
        rf_models[h] = rf_model
        xgb_clfs[h] = xgb_clf
        metadata[h] = {"w_xgb": float(w_xgb), "w_rf": float(w_rf), "features": features_to_keep}
        
    avg_mape = total_val_mape / 7
    avg_dir_acc = total_dir_acc / 7
    logger.info(f"=== Overall Test Performance: MAPE {avg_mape:.2f}%, DirAcc {avg_dir_acc:.2f}% ===")
    
    # Save everything
    with open(os.path.join(MODELS_DIR, "xgb_models_ph.pkl"), "wb") as f:
        pickle.dump(xgb_models, f)
    with open(os.path.join(MODELS_DIR, "rf_models_ph.pkl"), "wb") as f:
        pickle.dump(rf_models, f)
    with open(os.path.join(MODELS_DIR, "xgb_clfs_ph.pkl"), "wb") as f:
        pickle.dump(xgb_clfs, f)
    with open(os.path.join(MODELS_DIR, "ml_metadata_ph.json"), "w") as f:
        json.dump(metadata, f)
        
    return {
        "val_mape": avg_mape,
        "val_directional_accuracy": avg_dir_acc
    }

def forecast_ml_models(latest_features_dict: dict, current_price: float, steps: int = 7) -> list:
    try:
        with open(os.path.join(MODELS_DIR, "xgb_models_ph.pkl"), "rb") as f:
            xgb_models = pickle.load(f)
        with open(os.path.join(MODELS_DIR, "rf_models_ph.pkl"), "rb") as f:
            rf_models = pickle.load(f)
        with open(os.path.join(MODELS_DIR, "xgb_clfs_ph.pkl"), "rb") as f:
            xgb_clfs = pickle.load(f)
        with open(os.path.join(MODELS_DIR, "ml_metadata_ph.json"), "r") as f:
            metadata = json.load(f)
            
        # Convert JSON string keys to ints
        metadata = {int(k): v for k, v in metadata.items()}
    except FileNotFoundError as e:
        logger.error(f"Trained models not found: {e}")
        return [{"step": h, "predicted_price": current_price, "predicted_return": 0.0, "predicted_direction": 0, "direction_prob": 0.0} for h in range(1, steps + 1)]
        
    predictions = []
    
    for h in range(1, steps + 1):
        if h not in xgb_models:
            continue
            
        h_meta = metadata[h]
        feature_names = h_meta["features"]
        
        row_x = latest_features_dict.copy()
        ordered_row = [row_x.get(col, 0.0) for col in feature_names]
        X_pred = pd.DataFrame([ordered_row], columns=feature_names)
        
        xgb_pred = xgb_models[h].predict(X_pred)[0]
        rf_pred = rf_models[h].predict(X_pred)[0]
        
        w_xgb = h_meta.get("w_xgb", 0.5)
        w_rf = h_meta.get("w_rf", 0.5)
        ensemble_pred = w_xgb * xgb_pred + w_rf * rf_pred
        
        clf = xgb_clfs[h]
        clf_pred = clf.predict(X_pred)[0] - 1
        clf_probs = clf.predict_proba(X_pred)[0]
        prob_idx = clf_pred + 1
        direction_prob = float(clf_probs[prob_idx])
        
        try:
            X_pred_arr = X_pred.values if hasattr(X_pred, "values") else np.array(X_pred)
            tree_preds = np.array([tree.predict(X_pred_arr) for tree in rf_models[h].estimators_])
            rf_return_std = float(tree_preds.std(axis=0)[0])
        except Exception as e:
            rf_return_std = 0.0
            
        pred_price = current_price * (1 + ensemble_pred / 100)
        rf_price_std = current_price * (rf_return_std / 100)
        
        predictions.append({
            "step": h,
            "predicted_return": float(ensemble_pred),
            "predicted_price": round(max(0.0, pred_price), 2),
            "price_std": float(rf_price_std),
            "predicted_direction": int(clf_pred),
            "direction_prob": float(direction_prob)
        })
        
    return predictions

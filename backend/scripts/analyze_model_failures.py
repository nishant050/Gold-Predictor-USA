import os
import sys
import pickle
import json
import logging
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, init_db
from app.ml.feature_engineering import fetch_raw_data, build_features, generate_prediction_dataset
from app.ml.backtester import create_train_test_split

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "trained_models")
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")

def main():
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)

    logger.info("Initializing DB and fetching data...")
    init_db()
    db = SessionLocal()
    
    try:
        df_raw, df_events = fetch_raw_data(db)
        df_features = build_features(df_raw, df_events)
        X, y, labels = generate_prediction_dataset(df_features, max_horizon=7)
        
        # Load test set (from 2024 onwards)
        X_tr, y_tr, lbl_tr, X_te, y_te, lbl_te = create_train_test_split(
            X, y, labels, test_start_date="2024-01-01"
        )
        
        logger.info("Loading trained models...")
        with open(os.path.join(MODELS_DIR, "xgb_clfs_ph.pkl"), "rb") as f:
            xgb_clfs = pickle.load(f)
        with open(os.path.join(MODELS_DIR, "ml_metadata_ph.json"), "r") as f:
            metadata = json.load(f)
            
        metadata = {int(k): v for k, v in metadata.items()}
        
        # Focus on Horizon 7 for deep analysis
        h = 7
        if h not in xgb_clfs:
            logger.error("Horizon 7 model not found!")
            return
            
        clf = xgb_clfs[h]
        features = metadata[h]["features"]
        
        h_tr_mask = X_tr["horizon"] == h
        X_h_tr = X_tr[h_tr_mask][features]
        lbl_h_tr = lbl_tr[h_tr_mask]
        
        h_te_mask = X_te["horizon"] == h
        X_h_te = X_te[h_te_mask]
        lbl_h_te = lbl_te[h_te_mask]
        
        X_pred = X_h_te[features]
        
        # Predict on Test Set
        preds = clf.predict(X_pred) - 1
        
        # Build analysis dataframe
        analysis_df = X_h_te.copy()
        analysis_df["actual_label"] = lbl_h_te
        analysis_df["pred_label"] = preds
        analysis_df["correct"] = (analysis_df["actual_label"] == analysis_df["pred_label"]).astype(int)
        
        y_h_te = y_te[h_te_mask]
        analysis_df["actual_return"] = y_h_te
        
        # Filter for meaningful days
        meaningful_mask = analysis_df["actual_label"] != 0
        eval_df = analysis_df[meaningful_mask].copy()
        
        if len(eval_df) == 0:
            logger.error("No meaningful test examples found.")
            return
            
        eval_df["date"] = pd.to_datetime(eval_df["_date_idx"])
        eval_df["year"] = eval_df["date"].dt.year
        eval_df["month"] = eval_df["date"].dt.month
        
        # Generate Markdown Report
        report_lines = []
        report_lines.append("# Deep Failure Mode Analysis Report")
        report_lines.append(f"Generated at: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # 1. Temporal Analysis
        report_lines.append("## 1. Temporal Failure Analysis (Horizon 7)")
        report_lines.append("Monthly directional accuracy for the test set (2024-2026):")
        report_lines.append("")
        report_lines.append("| Year-Month | Accuracy | Correct / Total | Baseline (Always UP) |")
        report_lines.append("|---|---|---|---|")
        
        for (y_val, m_val), group in eval_df.groupby(["year", "month"]):
            acc = group["correct"].mean() * 100
            total = len(group)
            correct = group["correct"].sum()
            up_baseline = (group["actual_label"] == 1).mean() * 100
            report_lines.append(f"| {y_val}-{m_val:02d} | {acc:.1f}% | {correct} / {total} | {up_baseline:.1f}% |")
            
        report_lines.append("")
        
        # 2. Regime Conditional Accuracy
        report_lines.append("## 2. Regime-Conditional Accuracy")
        report_lines.append("| Regime | Accuracy | Correct / Total |")
        report_lines.append("|---|---|---|")
        
        # VIX Regimes
        if "VIX_zscore" in eval_df.columns:
            high_vix = eval_df[eval_df["VIX_zscore"] > 1.0]
            if len(high_vix) > 0:
                report_lines.append(f"| High VIX (>1 std) | {high_vix['correct'].mean()*100:.1f}% | {high_vix['correct'].sum()} / {len(high_vix)} |")
            low_vix = eval_df[eval_df["VIX_zscore"] < -1.0]
            if len(low_vix) > 0:
                report_lines.append(f"| Low VIX (<-1 std) | {low_vix['correct'].mean()*100:.1f}% | {low_vix['correct'].sum()} / {len(low_vix)} |")
                
        # Fed Rate Regimes
        if "FED_RATE_zscore" in eval_df.columns:
            high_rates = eval_df[eval_df["FED_RATE_zscore"] > 1.0]
            if len(high_rates) > 0:
                report_lines.append(f"| High Fed Rate (>1 std) | {high_rates['correct'].mean()*100:.1f}% | {high_rates['correct'].sum()} / {len(high_rates)} |")
                
        # Active vs Quiet Regimes
        if "active_regime_count" in eval_df.columns:
            active = eval_df[eval_df["active_regime_count"] > 0]
            quiet = eval_df[eval_df["active_regime_count"] == 0]
            if len(active) > 0:
                report_lines.append(f"| Active Event Regime | {active['correct'].mean()*100:.1f}% | {active['correct'].sum()} / {len(active)} |")
            if len(quiet) > 0:
                report_lines.append(f"| Quiet Regime | {quiet['correct'].mean()*100:.1f}% | {quiet['correct'].sum()} / {len(quiet)} |")
                
        report_lines.append("")
        
        # 3. Biggest Misses
        report_lines.append("## 3. Biggest Misses Analysis")
        report_lines.append("Days where the model predicted DOWN but the market went strongly UP, or vice versa.")
        
        wrong_df = eval_df[eval_df["correct"] == 0].copy()
        wrong_df["miss_magnitude"] = wrong_df["actual_return"].abs()
        
        top_misses = wrong_df.sort_values("miss_magnitude", ascending=False).head(20)
        
        for i, (_, row) in enumerate(top_misses.iterrows(), 1):
            date_str = pd.to_datetime(row['_date_idx']).strftime('%Y-%m-%d')
            pred_dir = "UP" if row['pred_label'] == 1 else "DOWN"
            act_dir = "UP" if row['actual_label'] == 1 else "DOWN"
            report_lines.append(f"### {i}. {date_str} (Actual: {act_dir} {row['actual_return']:.2f}%, Predicted: {pred_dir})")
            report_lines.append(f"- **VIX (Z)**: {row.get('VIX_zscore', 0):.2f}")
            report_lines.append(f"- **FED_RATE (Z)**: {row.get('FED_RATE_zscore', 0):.2f}")
            report_lines.append(f"- **Active Regimes**: {row.get('active_regime_count', 0)}")
            report_lines.append("")

        # 4. Feature Drift
        report_lines.append("## 4. Feature Drift Detection")
        report_lines.append("Comparing Train (2006-2023) vs Test (2024-2026) means:")
        report_lines.append("| Feature | Train Mean | Test Mean | % Change |")
        report_lines.append("|---|---|---|---|")
        
        for feat in ["FED_RATE_zscore", "VIX_zscore", "TIPS_BREAKEVEN_10Y_zscore", "close", "DXY_zscore", "active_regime_count"]:
            if feat in X_tr.columns and feat in X_te.columns:
                tr_mean = X_tr[feat].mean()
                te_mean = X_te[feat].mean()
                pct_change = ((te_mean - tr_mean) / tr_mean * 100) if tr_mean != 0 else 0
                if abs(pct_change) > 20:
                    report_lines.append(f"| {feat} | {tr_mean:.2f} | {te_mean:.2f} | **{pct_change:+.1f}%** |")
                    
        report_lines.append("")
        
        # 5. Overfitting Check
        report_lines.append("## 5. Overfitting Check (Horizon 7)")
        tr_meaningful = lbl_h_tr != 0
        if tr_meaningful.sum() > 0:
            tr_preds = clf.predict(X_h_tr) - 1
            tr_acc = (tr_preds[tr_meaningful] == lbl_h_tr[tr_meaningful]).mean() * 100
            te_acc = eval_df["correct"].mean() * 100
            report_lines.append(f"- **Train Accuracy**: {tr_acc:.1f}%")
            report_lines.append(f"- **Test Accuracy**: {te_acc:.1f}%")
            report_lines.append(f"- **Gap**: {tr_acc - te_acc:.1f}%")
            if (tr_acc - te_acc) > 10:
                report_lines.append("\n**WARNING**: Model is overfitting (gap > 10%).")
                
        # Write report
        report_path = os.path.join(REPORTS_DIR, "failure_analysis.md")
        with open(report_path, "w") as f:
            f.write("\n".join(report_lines))
            
        logger.info(f"Report written to {report_path}")

    except Exception as e:
        logger.exception("Error in analysis:")
    finally:
        db.close()

if __name__ == "__main__":
    main()

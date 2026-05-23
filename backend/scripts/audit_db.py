import sqlite3
conn = sqlite3.connect('data/gold_tracker.db')
c = conn.cursor()

# Tables
tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("=== TABLES ===")
for t in tables:
    count = c.execute(f"SELECT COUNT(*) FROM [{t[0]}]").fetchone()[0]
    print(f"  {t[0]}: {count} rows")

# Gold prices
print("\n=== GOLD PRICES ===")
for cur in ['USD', 'INR']:
    row = c.execute(f"SELECT MIN(date), MAX(date), COUNT(*) FROM gold_prices WHERE currency='{cur}'").fetchone()
    print(f"  {cur}: {row[2]} rows, {row[0]} to {row[1]}")

# Indicators
print("\n=== ECONOMIC INDICATORS ===")
rows = c.execute("SELECT indicator_name, COUNT(*), MIN(date), MAX(date) FROM economic_indicators GROUP BY indicator_name").fetchall()
for r in rows:
    print(f"  {r[0]}: {r[1]} rows, {r[2]} to {r[3]}")

# Predictions
print("\n=== PREDICTIONS ===")
rows = c.execute("SELECT prediction_method, model_version, COUNT(*), MIN(target_date), MAX(target_date) FROM predictions GROUP BY prediction_method, model_version").fetchall()
for r in rows:
    print(f"  {r[0]}/{r[1]}: {r[2]} preds, {r[3]} to {r[4]}")

# Events
print("\n=== HISTORICAL EVENTS ===")
rows = c.execute("SELECT event_type, COUNT(*) as cnt, SUM(CASE WHEN gold_price_change_30d IS NOT NULL THEN 1 ELSE 0 END) as with_data FROM historical_events GROUP BY event_type").fetchall()
for r in rows:
    pct = (r[2]/r[1]*100) if r[1] > 0 else 0
    print(f"  {r[0]}: {r[1]} events, {pct:.0f}% have price correlation data")

# News
print("\n=== NEWS SENTIMENT ===")
total = c.execute("SELECT COUNT(*) FROM news_sentiment").fetchone()[0]
with_rel = c.execute("SELECT COUNT(*) FROM news_sentiment WHERE relevance_score IS NOT NULL").fetchone()[0]
dates = c.execute("SELECT MIN(date), MAX(date) FROM news_sentiment").fetchone()
print(f"  Total: {total}, With relevance: {with_rel}, Range: {dates}")

# LLM
print("\n=== LLM ANALYSES ===")
cnt = c.execute("SELECT COUNT(*) FROM llm_analyses").fetchone()[0]
latest = c.execute("SELECT analysis_date, predicted_direction, predicted_change_percent, confidence_level FROM llm_analyses ORDER BY analysis_date DESC LIMIT 1").fetchone()
print(f"  Count: {cnt}, Latest: {latest}")

# Models
print("\n=== MODEL VERSIONS ===")
rows = c.execute("SELECT version, model_type, training_mape, validation_mape, directional_accuracy FROM model_versions").fetchall()
for r in rows:
    print(f"  v{r[0]} ({r[1]}): train_mape={r[2]}%, val_mape={r[3]}%, dir_acc={r[4]}%")

# Check for nulls in predictions
print("\n=== PREDICTION QUALITY ===")
null_prices = c.execute("SELECT COUNT(*) FROM predictions WHERE predicted_price IS NULL").fetchone()[0]
null_ci = c.execute("SELECT COUNT(*) FROM predictions WHERE confidence_low_80 IS NULL").fetchone()[0]
print(f"  Null predicted_price: {null_prices}")
print(f"  Null confidence_low_80: {null_ci}")
sample = c.execute("SELECT target_date, predicted_price, confidence_low_80, confidence_high_80 FROM predictions WHERE prediction_method='ml' AND model_version='ensemble_v1' ORDER BY target_date LIMIT 5").fetchall()
print("  Sample ML USD predictions:")
for s in sample:
    print(f"    {s[0]}: ${s[1]:.2f} (80% CI: ${s[2]:.2f} - ${s[3]:.2f})")

conn.close()

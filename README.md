# GoldSight — AI Gold Price Tracker & Predictor

GoldSight is a comprehensive gold price tracking and prediction web application. It integrates 20+ years of gold prices and macroeconomic indicators, correlates major historical events with price changes, pulls and scores daily news sentiment, and produces parallel 30-day price forecasts using both a Machine Learning (ML) ensemble and a Large Language Model (LLM) historical analogy engine.

## Key Features

1. **Dual Predictions**: Plotted side-by-side on the dashboard are forecasts from:
   - **ML Ensemble**: Blended ARIMA + XGBoost + Random Forest models trained on historical technical metrics and economic indicators.
   - **LLM Analogy Engine**: Contextualized analysis that compares today's news and economic climate to historical matches to project returns.
2. **Interactive Charting**: Plotly-based dynamic charts overlaying historical prices with predictive ranges, indicator comparisons, and event triggers.
3. **Macroeconomic Indicators**: Tracks variables like USD Index (DXY), 10-Year Treasury Yields, Silver, Crude Oil (WTI), S&P 500, VIX, Interest Rates, Money Supply (M2), and computed Real Interest Rates.
4. **Historical Event Timeline**: Interactive timeline of ~150+ major events (wars, policy changes, financial crises) showing gold price changes at 7d, 30d, and 90d intervals.
5. **Real-time News Sentiment**: Daily aggregation and sentiment scoring of news coverage related to gold, mapping market mood changes over time.
6. **Automated Background Scheduler**: Built-in APScheduler triggers daily price and indicator updates, news scans, and forecasting cycles.

---

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+

### Setup Instructions

#### 1. Setup Backend
```bash
cd backend
# Install dependencies
pip install -r requirements.txt

# Configure Environment
# Rename/edit the .env file with your API keys:
# FRED, NYT, Guardian, NewsAPI, OpenRouter
```

#### 2. Seed Data & Train Models
```bash
# Populate 20+ years of gold prices, commodity values, and FRED indicators
python -m scripts.populate_all_data

# Seed historical event catalog and calculate price impacts
python -m scripts.seed_historical_events

# Train the ML Regressor models (XGBoost + Random Forest)
python -m scripts.train_models

# Run initial forecasts
python -m scripts.generate_predictions
```

#### 3. Run Servers
Start the backend API server:
```bash
python -m uvicorn app.main:app --port 8000 --reload
```
Start the frontend development server:
```bash
cd ../frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## Tech Stack
- **Frontend**: Next.js (App Router), Plotly.js / react-plotly.js, Vanilla CSS, Framer Motion
- **Backend**: FastAPI, SQLAlchemy, SQLite, APScheduler
- **Machine Learning**: XGBoost, Scikit-Learn (Random Forest), Statsmodels (ARIMA), Pandas, TA (Technical Analysis library)
- **APIs**: FRED, Yahoo Finance, New York Times, Guardian, NewsAPI, OpenRouter (poolside/laguna-m.1:free)

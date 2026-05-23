import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from app.models.schemas import GoldPrice, EconomicIndicator, NewsSentiment, HistoricalEvent
import ta
import logging

logger = logging.getLogger(__name__)

def fetch_raw_data(db: Session, currency: str = "USD") -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Fetch all gold prices and economic indicators from the database,
    align them into a single daily DataFrame, and also return the raw historical events.
    """
    # 1. Fetch Gold Prices
    prices = db.query(GoldPrice).filter(GoldPrice.currency == currency).order_by(GoldPrice.date).all()
    if not prices:
        raise ValueError(f"No gold prices found in database for currency {currency}.")
        
    df_prices = pd.DataFrame([{
        "date": p.date,
        "open": p.open,
        "high": p.high,
        "low": p.low,
        "close": p.close,
        "volume": p.volume
    } for p in prices])
    df_prices["date"] = pd.to_datetime(df_prices["date"])
    df_prices = df_prices.set_index("date")
    
    # 2. Fetch Economic Indicators
    indicators = db.query(EconomicIndicator).order_by(EconomicIndicator.date).all()
    
    # Group indicators by name
    ind_groups = {}
    for ind in indicators:
        if ind.indicator_name not in ind_groups:
            ind_groups[ind.indicator_name] = []
        ind_groups[ind.indicator_name].append({"date": ind.date, "value": ind.value})
        
    df_indicators = []
    for name, data in ind_groups.items():
        df_ind = pd.DataFrame(data)
        df_ind["date"] = pd.to_datetime(df_ind["date"])
        df_ind = df_ind.rename(columns={"value": name}).set_index("date")
        df_indicators.append(df_ind)
        
    # 3. Fetch News Sentiment (Aggregated daily)
    sentiment_rows = db.query(
        NewsSentiment.date,
        NewsSentiment.sentiment_score,
        NewsSentiment.relevance_score
    ).all()
    
    if sentiment_rows:
        df_sent = pd.DataFrame(sentiment_rows, columns=["date", "sentiment_score", "relevance_score"])
        df_sent["date"] = pd.to_datetime(df_sent["date"])
        # Compute relevance-weighted daily sentiment
        df_sent["weighted_sentiment"] = df_sent["sentiment_score"] * df_sent["relevance_score"].fillna(1.0)
        daily_sent = df_sent.groupby("date").agg(
            sentiment_avg=("sentiment_score", "mean"),
            sentiment_weighted=("weighted_sentiment", "mean"),
            article_count=("sentiment_score", "count")
        )
    else:
        # Placeholder if no sentiment data
        daily_sent = pd.DataFrame(columns=["sentiment_avg", "sentiment_weighted", "article_count"])
        daily_sent.index.name = "date"
        
    # Combine all into a single daily DataFrame
    # Start with a complete date range from earliest gold price to latest gold price
    date_range = pd.date_range(start=df_prices.index.min(), end=df_prices.index.max(), freq="D")
    df_combined = pd.DataFrame(index=date_range)
    df_combined.index.name = "date"
    
    # Join gold prices
    df_combined = df_combined.join(df_prices, how="left")
    
    # Join each indicator
    for df_ind in df_indicators:
        df_combined = df_combined.join(df_ind, how="left")
        
    # Join sentiment
    df_combined = df_combined.join(daily_sent, how="left")
    
    # Forward-fill missing values (since markets are closed on weekends/holidays, and macro data is monthly)
    # For volume/article_count fill NaN with 0
    if "volume" in df_combined.columns:
        df_combined["volume"] = df_combined["volume"].fillna(0)
    if "article_count" in df_combined.columns:
        df_combined["article_count"] = df_combined["article_count"].fillna(0)
        
    # Fill sentiment with 0 (neutral) if no articles
    if "sentiment_avg" in df_combined.columns:
        df_combined["sentiment_avg"] = df_combined["sentiment_avg"].fillna(0)
    if "sentiment_weighted" in df_combined.columns:
        df_combined["sentiment_weighted"] = df_combined["sentiment_weighted"].fillna(0)
    else:
        df_combined["sentiment_avg"] = 0.0
        df_combined["sentiment_weighted"] = 0.0
        
    # Forward fill the rest (prices and indicators)
    cols_to_ffill = [c for c in df_combined.columns if c not in ["volume", "article_count"]]
    df_combined[cols_to_ffill] = df_combined[cols_to_ffill].ffill()
    
    # Fetch Historical Events
    events = db.query(HistoricalEvent).order_by(HistoricalEvent.event_date).all()
    if events:
        df_events = pd.DataFrame([{
            "date": e.event_date,
            "type": e.event_type,
            "impact": e.impact_level,
            "change_7d": e.gold_price_change_7d
        } for e in events])
        df_events["date"] = pd.to_datetime(df_events["date"])
    else:
        df_events = pd.DataFrame(columns=["date", "type", "impact", "change_7d"])
    
    return df_combined, df_events

def build_features(df: pd.DataFrame, df_events: pd.DataFrame = None) -> pd.DataFrame:
    """
    Build technical indicators and macro/sentiment lagged features.
    """
    df = df.copy()
    
    # 1. Technical Indicators on Gold Price (using close price)
    # Simple Moving Averages
    df["sma_5"] = ta.trend.sma_indicator(df["close"], window=5)
    df["sma_10"] = ta.trend.sma_indicator(df["close"], window=10)
    df["sma_30"] = ta.trend.sma_indicator(df["close"], window=30)
    df["sma_90"] = ta.trend.sma_indicator(df["close"], window=90)
    df["sma_200"] = ta.trend.sma_indicator(df["close"], window=200)
    
    # Exponential Moving Averages
    df["ema_12"] = ta.trend.ema_indicator(df["close"], window=12)
    df["ema_26"] = ta.trend.ema_indicator(df["close"], window=26)
    
    # MACD
    df["macd"] = ta.trend.macd(df["close"])
    df["macd_diff"] = ta.trend.macd_diff(df["close"])
    
    # RSI (Relative Strength Index)
    df["rsi"] = ta.momentum.rsi(df["close"], window=14)
    
    # Bollinger Bands
    df["bb_high"] = ta.volatility.bollinger_hband(df["close"], window=20)
    df["bb_low"] = ta.volatility.bollinger_lband(df["close"], window=20)
    df["bb_width"] = (df["bb_high"] - df["bb_low"]) / df["close"]
    
    # ATR (Average True Range)
    df["atr"] = ta.volatility.average_true_range(df["high"], df["low"], df["close"], window=14)
    
    # Momentum / Returns
    df["return_1d"] = df["close"].pct_change(1)
    df["return_5d"] = df["close"].pct_change(5)
    df["return_30d"] = df["close"].pct_change(30)
    df["return_90d"] = df["close"].pct_change(90)
    
    # Normalize price-level technical indicators to percentages
    price_dependent = ["sma_5", "sma_10", "sma_30", "sma_90", "sma_200", 
                       "ema_12", "ema_26", "bb_high", "bb_low"]
    for col in price_dependent:
        if col in df.columns:
            df[col] = (df[col] / df["close"] - 1) * 100  # Convert to % deviation from close
            
    # Normalize absolute difference/range technical indicators to percentages of close
    diff_dependent = ["macd", "macd_diff", "atr"]
    for col in diff_dependent:
        if col in df.columns:
            df[col] = (df[col] / df["close"]) * 100  # Convert to % of close

    # Volatility of returns
    df["volatility_10d"] = df["return_1d"].rolling(10).std() * 100
    df["volatility_30d"] = df["return_1d"].rolling(30).std() * 100
    
    # Days since last change of FED_RATE
    if "FED_RATE" in df.columns:
        fed_diff = df["FED_RATE"].diff() != 0
        all_indices = np.arange(len(df))
        last_change_idx = pd.Series(all_indices).where(fed_diff.values).ffill().fillna(0).astype(int)
        df["days_since_fed_change"] = (df.index - df.index[last_change_idx]).days
    
    # 2. Macro Indicators momentum / changes
    macro_cols = ["DXY", "FED_RATE", "CPI", "TREASURY_10Y", "OIL_WTI", "SP500", "VIX", "M2", "SILVER", "REAL_RATE", "USD_INR"]
    for col in macro_cols:
        if col in df.columns:
            # 30-day change of the indicator
            df[f"{col}_diff_30d"] = df[col].diff(30)
            # 5-day change of the indicator
            df[f"{col}_diff_5d"] = df[col].diff(5)
            
    # New Features
    if "SILVER" in df.columns:
        df["gold_silver_ratio"] = df["close"] / df["SILVER"].replace(0, np.nan)
    if "OIL_WTI" in df.columns:
        df["gold_oil_ratio"] = df["close"] / df["OIL_WTI"].replace(0, np.nan)
    if "TREASURY_10Y" in df.columns and "FED_RATE" in df.columns:
        df["yield_curve_slope"] = df["TREASURY_10Y"] - df["FED_RATE"]
    if "DXY" in df.columns:
        df["dxy_momentum_5d"] = df["DXY"].pct_change(5) * 100
        
    # Calendar Features
    df["day_of_week"] = df.index.dayofweek
    df["month_of_year"] = df.index.month
    df["week_of_month"] = (df.index.day - 1) // 7 + 1
    df["is_month_end"] = df.index.is_month_end.astype(int)
    df["is_quarter_end"] = df.index.is_quarter_end.astype(int)
    df["is_january"] = (df.index.month == 1).astype(int)
    
    if "DXY" in df.columns:
        df["cross_asset_divergence"] = df["return_5d"] * 100 + df["DXY"].pct_change(5) * 100
        if "VIX" in df.columns:
            df["dxy_x_vix"] = (df["DXY"].pct_change(5) * 100) * df["VIX"]
            
    if "FED_RATE" in df.columns and "CPI" in df.columns:
        df["rate_x_inflation"] = df["FED_RATE"].diff(5) * df["CPI"].diff(30)
        
    df["vol_normalized_return_5d"] = (df["return_5d"] * 100) / df["atr"].replace(0, np.nan)
    
    # Gold-to-Bitcoin ratio (when gold underperforms BTC, capital flows matter)
    if "BITCOIN" in df.columns and "close" in df.columns:
        df["gold_btc_ratio"] = df["close"] / df["BITCOIN"].replace(0, np.nan)
        df["gold_btc_ratio_change_30d"] = df["gold_btc_ratio"].pct_change(30)

    # Gold Miners divergence (miners leading/lagging gold)
    if "GOLD_MINERS" in df.columns:
        df["miners_divergence"] = df["close"].pct_change(5) - df["GOLD_MINERS"].pct_change(5)

    # TIPS momentum (rising inflation expectations)
    if "TIPS_BREAKEVEN_10Y" in df.columns:
        df["tips_momentum_5d"] = df["TIPS_BREAKEVEN_10Y"].diff(5)
        df["tips_momentum_30d"] = df["TIPS_BREAKEVEN_10Y"].diff(30)

    # Monetary base growth rate
    if "MONETARY_BASE" in df.columns:
        df["monetary_base_growth_90d"] = df["MONETARY_BASE"].pct_change(90) * 100

    # ============================================================
    # FIX 1: Rolling Z-Score Normalization for Macro Indicators
    # ============================================================
    # Instead of feeding raw levels (which drift over decades),
    # normalize each macro indicator to a rolling z-score.
    # This tells the model "how unusual is the current value
    # compared to the last year" — making it regime-invariant.
    #
    # Formula: z = (value - rolling_mean_252d) / rolling_std_252d
    # We keep the z-score version and DROP the raw level.
    # The _diff_5d and _diff_30d columns computed above are fine
    # because they are already relative changes, not raw levels.
    # ============================================================

    zscore_cols = ["FED_RATE", "CPI", "DXY", "TREASURY_10Y", "VIX", "M2",
                   "REAL_RATE", "USD_INR", "TIPS_BREAKEVEN_10Y",
                   "LONG_TERM_REAL_RATE", "MONETARY_BASE", "OIL_WTI_FRED",
                   "TIPS_ETF", "GOLD_MINERS", "USD_BULL_ETF", "BITCOIN",
                   "OIL_WTI", "SP500", "SILVER"]

    raw_cols_to_drop = []

    for col in zscore_cols:
        if col in df.columns:
            rolling_mean = df[col].rolling(window=252, min_periods=60).mean()
            rolling_std = df[col].rolling(window=252, min_periods=60).std()
            # Avoid division by zero: if std is 0, z-score is 0
            df[f"{col}_zscore"] = (df[col] - rolling_mean) / rolling_std.replace(0, np.nan)
            df[f"{col}_zscore"] = df[f"{col}_zscore"].fillna(0)
            raw_cols_to_drop.append(col)

    # Drop the raw level columns — we only keep z-scores + diffs
    # Exception: VIX raw is used in quiet_regime logic below, so drop it AFTER that section
    cols_safe_to_drop = [c for c in raw_cols_to_drop if c != "VIX"]
    df = df.drop(columns=[c for c in cols_safe_to_drop if c in df.columns])
            
    # 3. Sentiment rolling averages and momentum
    df["sentiment_roll_7d"] = df["sentiment_avg"].rolling(window=7).mean()
    df["sentiment_roll_30d"] = df["sentiment_avg"].rolling(window=30).mean()
    df["sentiment_acceleration"] = df["sentiment_roll_7d"] - df["sentiment_roll_30d"]
    df["sentiment_volatility_7d"] = df["sentiment_avg"].rolling(window=7).std().fillna(0)
    
    # 4. Qualitative Event Features
    if df_events is not None and not df_events.empty:
        # Sort events by date
        df_events = df_events.sort_values("date")
        
        # Initialize columns
        df["days_since_last_event"] = 9999
        df["active_event_impact"] = 0.0
        
        event_types = ["war", "economic_crisis", "monetary_policy", "pandemic", "trade", "election", "market_crash"]
        for etype in event_types:
            df[f"days_since_last_{etype}"] = 9999
            df[f"regime_{etype}"] = 0
            
        # Analogy features
        df["analogy_avg_7d_change"] = 0.0
        df["analogy_max_impact"] = 0.0
        df["analogy_direction_consensus"] = 0
        
        # We need to iterate chronologically to avoid future leakage
        # For each date in df, find past events
        event_dates = df_events["date"].values
        event_types_arr = df_events["type"].values
        event_impacts = df_events["impact"].values
        event_changes = df_events["change_7d"].values
        
        df_dates = df.index.values
        
        # Optimize by tracking the last seen index
        last_event_idx = -1
        
        # Track last seen per type
        last_seen = {etype: pd.NaT for etype in event_types}
        last_seen_any = pd.NaT
        active_impact = 0.0
        
        for i, current_date in enumerate(df_dates):
            # Advance last_event_idx to the most recent event strictly BEFORE current_date
            while last_event_idx + 1 < len(event_dates) and event_dates[last_event_idx + 1] < current_date:
                last_event_idx += 1
                ev_date = event_dates[last_event_idx]
                ev_type = event_types_arr[last_event_idx]
                ev_impact = event_impacts[last_event_idx]
                
                last_seen_any = ev_date
                if ev_type in last_seen:
                    last_seen[ev_type] = ev_date
                
                active_impact = ev_impact
                
            # Compute proximity
            if pd.notna(last_seen_any):
                days_diff = (current_date - last_seen_any).astype('timedelta64[D]').astype(int)
                df.iat[i, df.columns.get_loc("days_since_last_event")] = days_diff
                
                # Decay impact linearly over 30 days
                if days_diff <= 30:
                    df.iat[i, df.columns.get_loc("active_event_impact")] = active_impact * (1.0 - days_diff / 30.0)
                    
            for etype in event_types:
                if pd.notna(last_seen[etype]):
                    days_diff = (current_date - last_seen[etype]).astype('timedelta64[D]').astype(int)
                    df.iat[i, df.columns.get_loc(f"days_since_last_{etype}")] = days_diff
                    # Regime is active if within 30 days
                    if days_diff <= 30:
                        df.iat[i, df.columns.get_loc(f"regime_{etype}")] = 1
                        
            # Analogy Computation (Simple version: just use recent 3 events of the same dominant regime if active)
            # A full historical Euclidean distance search per day is too slow for pandas iteration.
            # We will approximate: If in a regime, look at the last 3 events of that type.
            # If no active regime, use last 3 events overall.
            if last_event_idx >= 0:
                # Get up to 3 most recent events
                start_idx = max(0, last_event_idx - 2)
                recent_changes = [c for c in event_changes[start_idx:last_event_idx+1] if pd.notna(c)]
                recent_impacts = [imp for imp in event_impacts[start_idx:last_event_idx+1] if pd.notna(imp)]
                
                if recent_changes:
                    df.iat[i, df.columns.get_loc("analogy_avg_7d_change")] = np.mean(recent_changes)
                    pos_count = sum(1 for c in recent_changes if c > 0)
                    neg_count = sum(1 for c in recent_changes if c < 0)
                    if pos_count > neg_count:
                        df.iat[i, df.columns.get_loc("analogy_direction_consensus")] = 1
                    elif neg_count > pos_count:
                        df.iat[i, df.columns.get_loc("analogy_direction_consensus")] = -1
                
                if recent_impacts:
                    df.iat[i, df.columns.get_loc("analogy_max_impact")] = np.max(recent_impacts)
    
    # 5. Regime Count & Quiet Regime
    regime_cols = [c for c in df.columns if c.startswith("regime_")]
    if regime_cols:
        df["active_regime_count"] = df[regime_cols].sum(axis=1)
    else:
        df["active_regime_count"] = 0
        
    df["quiet_regime"] = 0
    if "days_since_last_event" in df.columns and "VIX" in df.columns and "atr" in df.columns:
        atr_median_252 = df["atr"].rolling(252).median()
        quiet_mask = (
            (df["days_since_last_event"] > 60) &
            (df["VIX"] < 20) &
            (df["atr"] < atr_median_252)
        )
        df.loc[quiet_mask, "quiet_regime"] = 1

    # Now drop the raw VIX column (we kept it for quiet_regime logic above)
    if "VIX" in df.columns and "VIX_zscore" in df.columns:
        df = df.drop(columns=["VIX"])
    
    # Drop rows with NaN (due to indicators windows like sma_200)
    df = df.dropna()
    
    return df

def generate_prediction_dataset(df_features: pd.DataFrame, max_horizon: int = 7):
    """
    Prepare dataset for training a single model with horizon as a feature.
    For each date, we generate 30 rows, one for each horizon (1 to 30 days ahead).
    Returns X (features) and y (target close price).
    """
    X_list = []
    y_list = []
    label_list = []
    
    # Features to exclude from direct input but keep for index
    exclude_cols = ["open", "high", "low", "volume", "close"]
    feature_cols = [c for c in df_features.columns if c not in exclude_cols]
    
    # Use positional indexing since we only want trading days
    for i in range(len(df_features) - max_horizon):
        date = df_features.index[i]
        row_features = df_features.iloc[i][feature_cols].to_dict()
        close_t = df_features.iloc[i]["close"]
        # Adaptive threshold was too aggressive and created a massive FLAT class.
        # Reverting to a small fixed threshold so the model focuses on UP/DOWN direction.
        FLAT_THRESHOLD = 0.1
        
        for horizon in range(1, max_horizon + 1):
            # Target is the value 'horizon' trading days ahead
            target_idx = i + horizon
            close_target = df_features.iloc[target_idx]["close"]
            pct_return = (close_target - close_t) / close_t * 100
            
            # Label generation
            if abs(pct_return) < FLAT_THRESHOLD:
                label = 0
            elif pct_return > 0:
                label = 1
            else:
                label = -1
                
            row_x = row_features.copy()
            row_x["horizon"] = horizon
            row_x["_date_idx"] = date  # keep track of date for temporal splitting
            row_x["_close_t"] = close_t  # keep track of close price for validation metrics
            
            X_list.append(row_x)
            y_list.append(pct_return)
            label_list.append(label)
                
    X_df = pd.DataFrame(X_list)
    y_arr = np.array(y_list)
    labels_arr = np.array(label_list)
    
    return X_df, y_arr, labels_arr

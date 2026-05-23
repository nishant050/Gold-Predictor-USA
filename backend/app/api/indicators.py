from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import date
import pandas as pd
import numpy as np
from app.database import get_db
from app.models.schemas import EconomicIndicator, GoldPrice

router = APIRouter()

INDICATORS = ["DXY", "FED_RATE", "CPI", "TREASURY_10Y", "OIL_WTI", "SP500", "VIX", "M2", "SILVER", "REAL_RATE"]

import time
_correlation_cache = {"data": None, "timestamp": 0}
CACHE_TTL = 3600  # 1 hour

@router.get("/latest")
def get_latest_indicators(db: Session = Depends(get_db)):
    """Returns the most recent value and timestamp for all economic indicators."""
    latest_vals = {}
    for ind in INDICATORS:
        row = db.query(EconomicIndicator).filter(
            EconomicIndicator.indicator_name == ind
        ).order_by(desc(EconomicIndicator.date)).first()
        
        if row:
            latest_vals[ind] = {
                "value": round(row.value, 2) if ind not in ["M2"] else round(row.value, 1),
                "date": row.date.isoformat()
            }
        else:
            latest_vals[ind] = {"value": 0.0, "date": "N/A"}
            
    return latest_vals

@router.get("/historical")
def get_historical_indicator(
    indicator_name: str = Query("DXY"),
    start_date: date = Query(None),
    end_date: date = Query(None),
    db: Session = Depends(get_db)
):
    """Returns historical daily records for a specific indicator."""
    if indicator_name not in INDICATORS:
        raise HTTPException(status_code=400, detail=f"Indicator must be one of: {', '.join(INDICATORS)}")
        
    query = db.query(EconomicIndicator).filter(EconomicIndicator.indicator_name == indicator_name)
    if start_date:
        query = query.filter(EconomicIndicator.date >= start_date)
    if end_date:
        query = query.filter(EconomicIndicator.date <= end_date)
        
    rows = query.order_by(EconomicIndicator.date).all()
    
    return [
        {"date": r.date.isoformat(), "value": round(r.value, 4)}
        for r in rows
    ]

@router.get("/correlation")
def get_correlations(db: Session = Depends(get_db)):
    """
    Computes and returns the Pearson correlation coefficient between each 
    macroeconomic indicator and gold USD close price across the entire database.
    """
    global _correlation_cache
    now = time.time()
    if _correlation_cache["data"] and (now - _correlation_cache["timestamp"]) < CACHE_TTL:
        return _correlation_cache["data"]
        
    # 1. Fetch Gold Prices
    gold_prices = db.query(GoldPrice.date, GoldPrice.close).filter(
        GoldPrice.currency == "USD"
    ).all()
    if not gold_prices:
        return {ind: 0.0 for ind in INDICATORS}
        
    df_gold = pd.DataFrame(gold_prices, columns=["date", "gold_close"]).set_index("date")
    
    correlations = {}
    for ind in INDICATORS:
        # Fetch indicator
        ind_vals = db.query(EconomicIndicator.date, EconomicIndicator.value).filter(
            EconomicIndicator.indicator_name == ind
        ).all()
        
        if not ind_vals:
            correlations[ind] = 0.0
            continue
            
        df_ind = pd.DataFrame(ind_vals, columns=["date", "ind_value"]).set_index("date")
        
        # Align on Date (inner join) and compute Pearson correlation
        df_joined = df_gold.join(df_ind, how="inner").dropna()
        
        if len(df_joined) > 5:
            corr = df_joined["gold_close"].corr(df_joined["ind_value"])
            correlations[ind] = round(float(corr), 3) if not np.isnan(corr) else 0.0
        else:
            correlations[ind] = 0.0
            
    _correlation_cache = {"data": correlations, "timestamp": now}
    return correlations

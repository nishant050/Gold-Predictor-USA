from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import date, timedelta
from app.database import get_db
from app.models.schemas import GoldPrice, EconomicIndicator

router = APIRouter()

def get_nearest_gold_price(db: Session, target_date: date, currency: str = "INR") -> GoldPrice:
    """Finds the nearest gold price record on or before target_date."""
    return db.query(GoldPrice).filter(
        GoldPrice.currency == currency,
        GoldPrice.date <= target_date
    ).order_by(desc(GoldPrice.date)).first()

@router.get("/current")
def get_current_price(db: Session = Depends(get_db)):
    """
    Returns the latest gold prices in USD/INR along with 24h, 7d, and 30d performance metrics,
    plus the latest values for related market indices/commodities.
    """
    # Latest USD Price
    latest_usd = db.query(GoldPrice).filter(GoldPrice.currency == "USD").order_by(desc(GoldPrice.date)).first()
    if not latest_usd:
        raise HTTPException(status_code=404, detail="No gold price data found.")
        
    latest_inr = db.query(GoldPrice).filter(GoldPrice.currency == "INR").order_by(desc(GoldPrice.date)).first()
    
    # Calculate performance metrics relative to historical dates
    price_today_usd = latest_usd.close
    
    # USD historical changes
    prev_day = db.query(GoldPrice).filter(
        GoldPrice.currency == "USD",
        GoldPrice.date < latest_usd.date
    ).order_by(desc(GoldPrice.date)).first()
    
    prev_7d = get_nearest_gold_price(db, latest_usd.date - timedelta(days=7), currency="USD")
    prev_30d = get_nearest_gold_price(db, latest_usd.date - timedelta(days=30), currency="USD")
    
    change_24h = price_today_usd - prev_day.close if prev_day else 0.0
    change_24h_pct = (change_24h / prev_day.close * 100) if prev_day else 0.0
    change_7d_pct = ((price_today_usd - prev_7d.close) / prev_7d.close * 100) if prev_7d else 0.0
    change_30d_pct = ((price_today_usd - prev_30d.close) / prev_30d.close * 100) if prev_30d else 0.0
    
    # Scale GOLDBEES ETF (₹130 for 0.01g) to actual 24K Retail Spot Price per 1 Gram (~₹15,900)
    INR_RETAIL_MULTIPLIER = 121.88
    
    # Compute INR changes if exists
    price_today_inr = latest_inr.close if latest_inr else 0.0
    prev_day_inr = db.query(GoldPrice).filter(
        GoldPrice.currency == "INR",
        GoldPrice.date < (latest_inr.date if latest_inr else latest_usd.date)
    ).order_by(desc(GoldPrice.date)).first()
    
    prev_7d_inr = get_nearest_gold_price(db, (latest_inr.date if latest_inr else latest_usd.date) - timedelta(days=7), currency="INR")
    prev_30d_inr = get_nearest_gold_price(db, (latest_inr.date if latest_inr else latest_usd.date) - timedelta(days=30), currency="INR")
    
    change_24h_inr = price_today_inr - prev_day_inr.close if prev_day_inr else 0.0
    change_24h_pct_inr = (change_24h_inr / prev_day_inr.close * 100) if prev_day_inr else 0.0
    change_7d_pct_inr = ((price_today_inr - prev_7d_inr.close) / prev_7d_inr.close * 100) if prev_7d_inr else 0.0
    change_30d_pct_inr = ((price_today_inr - prev_30d_inr.close) / prev_30d_inr.close * 100) if prev_30d_inr else 0.0
    related = {}
    indicators_list = ["SILVER", "DXY", "OIL_WTI", "SP500", "VIX"]
    cutoff_date = latest_usd.date - timedelta(days=45)
    indicator_records = db.query(EconomicIndicator).filter(
        EconomicIndicator.indicator_name.in_(indicators_list),
        EconomicIndicator.date >= cutoff_date
    ).order_by(EconomicIndicator.indicator_name, desc(EconomicIndicator.date)).all()
    
    for ind in indicators_list:
        ind_recs = [r for r in indicator_records if r.indicator_name == ind]
        latest_val = ind_recs[0] if len(ind_recs) > 0 else None
        prev_val = ind_recs[1] if len(ind_recs) > 1 else None
        
        change_pct = 0.0
        if latest_val and prev_val and prev_val.value != 0:
            change_pct = ((latest_val.value - prev_val.value) / prev_val.value) * 100
            
        related[ind.lower()] = {
            "value": latest_val.value if latest_val else 0.0,
            "change_pct": round(change_pct, 2) if latest_val else 0.0
        }
        
    return {
        "usd": {
            "price": round(price_today_usd, 2),
            "change_24h": round(change_24h, 2),
            "change_24h_pct": round(change_24h_pct, 2),
            "change_7d_pct": round(change_7d_pct, 2),
            "change_30d_pct": round(change_30d_pct, 2)
        },
        "inr": {
            "price": round(price_today_inr * INR_RETAIL_MULTIPLIER, 2) if latest_inr else 0.0,
            "change_24h": round(change_24h_inr * INR_RETAIL_MULTIPLIER, 2) if latest_inr and prev_day_inr else 0.0,
            "change_24h_pct": round(change_24h_pct_inr, 2) if latest_inr and prev_day_inr else 0.0,
            "change_7d_pct": round(change_7d_pct_inr, 2) if latest_inr and prev_7d_inr else 0.0,
            "change_30d_pct": round(change_30d_pct_inr, 2) if latest_inr and prev_30d_inr else 0.0
        },
        "related": related,
        "last_updated": latest_usd.date.isoformat()
    }

@router.get("/historical")
def get_historical_prices(
    start_date: date = Query(None),
    end_date: date = Query(None),
    currency: str = Query("INR"),
    limit: int = Query(None, le=10000),
    db: Session = Depends(get_db)
):
    """Returns a list of daily gold prices with filtering option (Optimized under Fix 2.6)."""
    query = db.query(GoldPrice).filter(GoldPrice.currency == currency)
    if start_date:
        query = query.filter(GoldPrice.date >= start_date)
    if end_date:
        query = query.filter(GoldPrice.date <= end_date)
    
    query = query.order_by(desc(GoldPrice.date))
    
    if limit:
        query = query.limit(limit)
        
    results = query.all()
    
    # Scale GOLDBEES ETF (₹130 for 0.01g) to actual 24K Retail Spot Price per 1 Gram (~₹15,900)
    INR_RETAIL_MULTIPLIER = 121.88
    
    if currency == "INR":
        for r in results:
            r.open = round(r.open * INR_RETAIL_MULTIPLIER, 2)
            r.high = round(r.high * INR_RETAIL_MULTIPLIER, 2)
            r.low = round(r.low * INR_RETAIL_MULTIPLIER, 2)
            r.close = round(r.close * INR_RETAIL_MULTIPLIER, 2)
            
    return results

@router.get("/chart-data")
def get_chart_data(
    period: str = Query("1Y"),
    currency: str = Query("INR"),
    db: Session = Depends(get_db)
):
    """
    Returns time-series coordinates structured for frontend Plotly charting.
    Supported periods: 1M, 6M, 1Y, 5Y, ALL
    """
    query = db.query(GoldPrice).filter(GoldPrice.currency == currency)
    
    # Calculate start date based on period
    today = date.today()
    if period == "1M":
        start = today - timedelta(days=30)
        query = query.filter(GoldPrice.date >= start)
    elif period == "6M":
        start = today - timedelta(days=180)
        query = query.filter(GoldPrice.date >= start)
    elif period == "1Y":
        start = today - timedelta(days=365)
        query = query.filter(GoldPrice.date >= start)
    elif period == "5Y":
        start = today - timedelta(days=365 * 5)
        query = query.filter(GoldPrice.date >= start)
    # ALL is unfiltered
    
    prices = query.order_by(GoldPrice.date).all()
    
    if not prices:
        return {"dates": [], "open": [], "high": [], "low": [], "close": [], "volume": []}
        
    INR_RETAIL_MULTIPLIER = 121.88
    multiplier = INR_RETAIL_MULTIPLIER if currency == "INR" else 1.0
        
    return {
        "dates": [p.date.isoformat() for p in prices],
        "open": [round(p.open * multiplier, 2) for p in prices],
        "high": [round(p.high * multiplier, 2) for p in prices],
        "low": [round(p.low * multiplier, 2) for p in prices],
        "close": [round(p.close * multiplier, 2) for p in prices],
        "volume": [p.volume for p in prices]
    }

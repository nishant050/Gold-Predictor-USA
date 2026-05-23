import pandas as pd
import yfinance as yf
from datetime import datetime, date
from sqlalchemy.orm import Session
from app.models.schemas import GoldPrice, EconomicIndicator
import logging

logger = logging.getLogger(__name__)

def fetch_gold_prices(db: Session, start_date: str = "1996-01-01", end_date: str = None) -> int:
    """
    Fetch historical gold prices in USD from yfinance and store them in the database.
    Returns the number of rows inserted.
    """
    logger.info(f"Fetching gold prices (USD) from {start_date} to {end_date or 'present'}...")
    df = yf.download("GC=F", start=start_date, end=end_date)
    if df.empty:
        logger.warning("No gold price data returned from yfinance.")
        return 0

    # Handle MultiIndex columns if any
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()
    
    # Query existing dates to prevent duplicates
    existing_dates = {
        row[0] for row in db.query(GoldPrice.date).filter(GoldPrice.currency == "USD").all()
    }
    
    inserted = 0
    for _, row in df.iterrows():
        # Get date object
        row_date = row['Date']
        if isinstance(row_date, pd.Timestamp):
            row_date = row_date.to_pydatetime().date()
        elif isinstance(row_date, str):
            row_date = datetime.strptime(row_date, "%Y-%m-%d").date()
            
        if row_date in existing_dates:
            continue
            
        close_val = row['Close']
        if pd.isna(close_val):
            continue
            
        # Extract scalar values (handles pandas Series if multiple columns are present)
        try:
            op = float(row['Open'])
            hi = float(row['High'])
            lo = float(row['Low'])
            cl = float(close_val)
            vol = float(row['Volume']) if not pd.isna(row['Volume']) else None
        except (TypeError, ValueError) as e:
            # In case columns are series
            logger.warning(f"Error parsing row values at date {row_date}: {e}")
            continue
            
        gold_price = GoldPrice(
            date=row_date,
            open=op,
            high=hi,
            low=lo,
            close=cl,
            volume=vol,
            currency="USD",
            source="yfinance"
        )
        db.add(gold_price)
        inserted += 1
        
    db.commit()
    logger.info(f"Successfully inserted {inserted} gold prices (USD) rows.")
    return inserted

def fetch_gold_prices_inr(db: Session, start_date: str = "1996-01-01") -> int:
    """
    Fetch gold price in USD and USD/INR rate to compute and store gold price in INR.
    Returns the number of rows inserted.
    """
    logger.info(f"Computing historical gold prices in INR from {start_date}...")
    
    # Fetch gold in USD and USD/INR exchange rate
    gold_df = yf.download("GC=F", start=start_date)
    inr_df = yf.download("INR=X", start=start_date)
    
    if gold_df.empty or inr_df.empty:
        logger.warning("Could not download gold or exchange rate data for INR computation.")
        return 0
        
    # Handle MultiIndex columns
    if isinstance(gold_df.columns, pd.MultiIndex):
        gold_df.columns = gold_df.columns.get_level_values(0)
    if isinstance(inr_df.columns, pd.MultiIndex):
        inr_df.columns = inr_df.columns.get_level_values(0)
        
    gold_close = gold_df[['Close']].rename(columns={'Close': 'gold_usd'})
    inr_close = inr_df[['Close']].rename(columns={'Close': 'usd_inr'})
    
    # Join on Date
    combined = gold_close.join(inr_close, how='inner').dropna()
    combined = combined.reset_index()
    
    existing_dates = {
        row[0] for row in db.query(GoldPrice.date).filter(GoldPrice.currency == "INR").all()
    }
    
    inserted = 0
    for _, row in combined.iterrows():
        row_date = row['Date']
        if isinstance(row_date, pd.Timestamp):
            row_date = row_date.to_pydatetime().date()
            
        if row_date in existing_dates:
            continue
            
        gold_usd = float(row['gold_usd'])
        usd_inr = float(row['usd_inr'])
        gold_inr = gold_usd * usd_inr
        
        # Get details from original gold row
        orig_row = gold_df.loc[row['Date']]
        
        try:
            op = float(orig_row['Open']) * usd_inr
            hi = float(orig_row['High']) * usd_inr
            lo = float(orig_row['Low']) * usd_inr
            vol = float(orig_row['Volume']) if not pd.isna(orig_row['Volume']) else None
        except (TypeError, ValueError):
            op = hi = lo = gold_inr
            vol = None
        
        inr_price = GoldPrice(
            date=row_date,
            open=op,
            high=hi,
            low=lo,
            close=gold_inr,
            volume=vol,
            currency="INR",
            source="yfinance_computed"
        )
        db.add(inr_price)
        inserted += 1
        
    db.commit()
    logger.info(f"Successfully inserted {inserted} gold prices (INR) rows.")
    return inserted

def fetch_related_commodities(db: Session, start_date: str = "1996-01-01") -> int:
    """
    Fetch related commodities / indicators from yfinance and store in economic_indicators.
    """
    tickers = {
        "SI=F": "SILVER",
        "CL=F": "OIL_WTI",
        "^GSPC": "SP500",
        "^VIX": "VIX",
        "DX-Y.NYB": "DXY",
        "INR=X": "USD_INR",
        "TIP": "TIPS_ETF",
        "GDX": "GOLD_MINERS",
        "UUP": "USD_BULL_ETF",
        "BTC-USD": "BITCOIN"
    }
    
    total_inserted = 0
    for ticker, indicator in tickers.items():
        logger.info(f"Fetching indicator {indicator} ({ticker}) from {start_date}...")
        df = yf.download(ticker, start=start_date)
        if df.empty:
            logger.warning(f"No data returned for ticker {ticker}")
            continue
            
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df = df.reset_index()
        
        existing_dates = {
            row[0] for row in db.query(EconomicIndicator.date).filter(EconomicIndicator.indicator_name == indicator).all()
        }
        
        inserted = 0
        for _, row in df.iterrows():
            row_date = row['Date']
            if isinstance(row_date, pd.Timestamp):
                row_date = row_date.to_pydatetime().date()
                
            if row_date in existing_dates:
                continue
                
            close_val = row['Close']
            if pd.isna(close_val):
                continue
                
            ind = EconomicIndicator(
                date=row_date,
                indicator_name=indicator,
                value=float(close_val),
                source="yfinance"
            )
            db.add(ind)
            inserted += 1
            
        db.commit()
        logger.info(f"Inserted {inserted} rows for indicator {indicator}.")
        total_inserted += inserted
        
    return total_inserted

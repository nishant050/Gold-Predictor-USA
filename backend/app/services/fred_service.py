from fredapi import Fred
import pandas as pd
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from app.models.schemas import EconomicIndicator
from app.config import settings
from app.utils.api_key_manager import get_active_key, mark_key_exhausted
import time
import logging

logger = logging.getLogger(__name__)

def fetch_all_indicators(db: Session, start_date: str = "1996-01-01") -> int:
    """
    Fetch specified FRED series and store as daily economic indicators in the database.
    """
    max_retries = 3
    
    series_mapping = {
        "INTDSRINM193N": ("RBI_REPO_RATE", True),
        "INDIRLTLT01STM": ("INDIA_GOVT_BOND_10Y", True),
        "INDCPIALLMINMEI": ("INDIA_CPI", True),
        "MYAGM3INM189N": ("INDIA_M3", True)
    }
    
    total_inserted = 0
    
    for series_id, (indicator_name, ffill) in series_mapping.items():
        logger.info(f"Fetching indicator {indicator_name} ({series_id}) from FRED...")
        
        try:
            retry_count = 0
            success = False
            series = None
            
            while retry_count < max_retries and not success:
                api_key = get_active_key(db, "fred")
                if not api_key:
                    logger.error("No active FRED API key available.")
                    break
                    
                fred = Fred(api_key=api_key)
                try:
                    series = fred.get_series(series_id, observation_start=start_date)
                    success = True
                except Exception as e:
                    error_str = str(e).lower()
                    if "429" in error_str or "rate limit" in error_str or "quota" in error_str:
                        logger.warning(f"FRED API key exhausted: {e}")
                        mark_key_exhausted(db, "fred", api_key)
                        retry_count += 1
                        time.sleep(1)
                    else:
                        logger.error(f"Error fetching FRED series {series_id}: {e}")
                        break
                        
            if not success or series is None or series.empty:
                logger.warning(f"No data returned for FRED series {series_id}")
                continue
                
            df = pd.DataFrame(series, columns=["value"])
            df.index.name = "date"
            
            # Drop NaN values
            df = df.dropna()
            
            if ffill:
                # Reindex to daily and forward fill to create daily rows
                start_dt = df.index.min()
                end_dt = datetime.today()
                daily_index = pd.date_range(start=start_dt, end=end_dt, freq="D")
                
                df = df.reindex(daily_index)
                df["value"] = df["value"].ffill()
                df.index.name = "date"
                df = df.dropna()
                
            df = df.reset_index()
            
            # Query existing dates
            existing_dates = {
                row[0] for row in db.query(EconomicIndicator.date).filter(EconomicIndicator.indicator_name == indicator_name).all()
            }
            
            inserted = 0
            for _, row in df.iterrows():
                row_date = row['date']
                if isinstance(row_date, pd.Timestamp):
                    row_date = row_date.to_pydatetime().date()
                elif isinstance(row_date, str):
                    row_date = datetime.strptime(row_date, "%Y-%m-%d").date()
                    
                if row_date in existing_dates:
                    continue
                    
                ind = EconomicIndicator(
                    date=row_date,
                    indicator_name=indicator_name,
                    value=float(row['value']),
                    source="FRED"
                )
                db.add(ind)
                inserted += 1
                
                # Commit in chunks
                if inserted % 500 == 0:
                    db.commit()
                    
            db.commit()
            logger.info(f"Inserted {inserted} rows for {indicator_name}.")
            total_inserted += inserted
            
        except Exception as e:
            logger.error(f"Error fetching/processing FRED series {series_id}: {e}")
            
    return total_inserted


def compute_real_interest_rate(db: Session) -> int:
    """
    Calculate Real Rate = RBI_REPO_RATE - CPI_YoY_change
    CPI YoY: (CPI_today - CPI_12months_ago) / CPI_12months_ago * 100
    Store as REAL_RATE in economic_indicators.
    """
    logger.info("Computing real interest rates...")
    
    # Query all RBI_REPO_RATE and INDIA_CPI daily values
    rate_records = db.query(EconomicIndicator.date, EconomicIndicator.value).filter(
        EconomicIndicator.indicator_name == "RBI_REPO_RATE"
    ).order_by(EconomicIndicator.date).all()
    
    cpi_records = db.query(EconomicIndicator.date, EconomicIndicator.value).filter(
        EconomicIndicator.indicator_name == "INDIA_CPI"
    ).order_by(EconomicIndicator.date).all()
    
    if not rate_records or not cpi_records:
        logger.warning("Missing RBI_REPO_RATE or INDIA_CPI data to compute REAL_RATE.")
        return 0
        
    rate_df = pd.DataFrame(rate_records, columns=["date", "repo_rate"]).set_index("date")
    cpi_df = pd.DataFrame(cpi_records, columns=["date", "cpi"]).set_index("date")
    
    # Since our CPI series is daily (forward-filled), shifting by 365 corresponds to roughly 365 days ago.
    cpi_df["cpi_prev_year"] = cpi_df["cpi"].shift(365)
    cpi_df["cpi_yoy"] = ((cpi_df["cpi"] - cpi_df["cpi_prev_year"]) / cpi_df["cpi_prev_year"]) * 100
    cpi_df = cpi_df.dropna()
    
    # Join RBI_REPO_RATE and INDIA_CPI YoY
    combined = rate_df.join(cpi_df[["cpi_yoy"]], how="inner").dropna()
    combined["real_rate"] = combined["repo_rate"] - combined["cpi_yoy"]
    combined = combined.reset_index()
    
    existing_dates = {
        row[0] for row in db.query(EconomicIndicator.date).filter(EconomicIndicator.indicator_name == "REAL_RATE").all()
    }
    
    inserted = 0
    for _, row in combined.iterrows():
        row_date = row['date']
        if isinstance(row_date, pd.Timestamp):
            row_date = row_date.to_pydatetime().date()
        elif isinstance(row_date, str):
            row_date = datetime.strptime(row_date, "%Y-%m-%d").date()
            
        if row_date in existing_dates:
            continue
            
        real_rate_val = float(row['real_rate'])
        ind = EconomicIndicator(
            date=row_date,
            indicator_name="REAL_RATE",
            value=real_rate_val,
            source="computed"
        )
        db.add(ind)
        inserted += 1
        
        if inserted % 500 == 0:
            db.commit()
            
    db.commit()
    logger.info(f"Successfully computed and inserted {inserted} REAL_RATE rows.")
    return inserted

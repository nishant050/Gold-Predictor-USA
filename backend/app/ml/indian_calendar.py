import pandas as pd
import numpy as np
from datetime import timedelta

# Lookup table for Diwali dates (2000 - 2030)
# Most other Hindu festivals can be approximated relative to Diwali.
DIWALI_DATES = {
    2000: '2000-10-26', 2001: '2001-11-14', 2002: '2002-11-04', 2003: '2003-10-25',
    2004: '2004-11-12', 2005: '2005-11-01', 2006: '2006-10-21', 2007: '2007-11-09',
    2008: '2008-10-28', 2009: '2009-10-17', 2010: '2010-11-05', 2011: '2011-10-26',
    2012: '2012-11-13', 2013: '2013-11-03', 2014: '2014-10-23', 2015: '2015-11-11',
    2016: '2016-10-30', 2017: '2017-10-19', 2018: '2018-11-07', 2019: '2019-10-27',
    2020: '2020-11-14', 2021: '2021-11-04', 2022: '2022-10-24', 2023: '2023-11-12',
    2024: '2024-10-31', 2025: '2025-10-20', 2026: '2026-11-08', 2027: '2027-10-29',
    2028: '2028-10-17', 2029: '2029-11-05', 2030: '2030-10-26'
}

# Lookup table for Akshaya Tritiya (2000 - 2030)
AKSHAYA_TRITIYA_DATES = {
    2000: '2000-05-06', 2001: '2001-04-26', 2002: '2002-05-15', 2003: '2003-05-04',
    2004: '2004-04-22', 2005: '2005-05-11', 2006: '2006-04-30', 2007: '2007-04-20',
    2008: '2008-05-08', 2009: '2009-04-27', 2010: '2010-05-16', 2011: '2011-05-06',
    2012: '2012-04-24', 2013: '2013-05-13', 2014: '2014-05-02', 2015: '2015-04-21',
    2016: '2016-05-09', 2017: '2017-04-28', 2018: '2018-04-18', 2019: '2019-05-07',
    2020: '2020-04-26', 2021: '2021-05-14', 2022: '2022-05-03', 2023: '2023-04-22',
    2024: '2024-05-10', 2025: '2025-04-30', 2026: '2026-04-19', 2027: '2027-05-08',
    2028: '2028-04-27', 2029: '2029-05-15', 2030: '2030-05-04'
}

def add_indian_seasonal_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds Indian seasonal, cultural, and macroeconomic features to a time-series DataFrame.
    The DataFrame must have a DateTimeIndex.
    """
    if df.empty:
        return df

    df = df.copy()
    dates = df.index

    # 1. Base Date Features
    df['month_of_year'] = dates.month
    df['quarter'] = dates.quarter
    
    # 2. Quarters & Seasons
    df['is_festive_quarter'] = df['quarter'] == 4
    df['is_quiet_season'] = df['month_of_year'].isin([6, 7, 8]).astype(int)
    
    # 3. Wedding Seasons
    # Winter wedding season: Nov, Dec, Jan, Feb
    df['is_wedding_season_winter'] = df['month_of_year'].isin([11, 12, 1, 2]).astype(int)
    # Spring wedding season: Apr, May
    df['is_wedding_season_spring'] = df['month_of_year'].isin([4, 5]).astype(int)
    
    # 4. Harvest Seasons
    df['is_kharif_harvest'] = df['month_of_year'].isin([10, 11]).astype(int)
    df['is_rabi_harvest'] = df['month_of_year'].isin([3, 4]).astype(int)
    df['is_sowing_season'] = df['month_of_year'].isin([6, 7]).astype(int)
    df['is_monsoon'] = df['month_of_year'].isin([6, 7, 8, 9]).astype(int)
    
    # 5. Government & Tax Cycles
    df['is_budget_month'] = (df['month_of_year'] == 2).astype(int)
    df['is_fy_end'] = (df['month_of_year'] == 3).astype(int)
    
    # 6. Fixed Date Festivals
    df['is_makar_sankranti'] = ((dates.month == 1) & (dates.day == 14)).astype(int)
    
    # 7. Lunar/Movable Festivals (using lookup tables)
    # Initialize festival features
    df['is_diwali_window'] = 0
    df['is_dhanteras_window'] = 0
    df['is_akshaya_tritiya_window'] = 0
    df['is_navratri'] = 0
    df['is_dussehra'] = 0
    df['is_pitru_paksha'] = 0
    df['days_to_dhanteras'] = 365 # Default large value
    df['days_to_akshaya_tritiya'] = 365

    # Process year by year for movable festivals
    years = dates.year.unique()
    for year in years:
        if year in DIWALI_DATES:
            diwali_date = pd.to_datetime(DIWALI_DATES[year])
            dhanteras_date = diwali_date - pd.Timedelta(days=2)
            dussehra_date = diwali_date - pd.Timedelta(days=20)
            navratri_start = dussehra_date - pd.Timedelta(days=9)
            pitru_paksha_start = navratri_start - pd.Timedelta(days=16)
            
            # Windows (-7 to +2 days for major buying festivals)
            diwali_mask = (dates >= diwali_date - pd.Timedelta(days=7)) & (dates <= diwali_date + pd.Timedelta(days=2))
            df.loc[diwali_mask, 'is_diwali_window'] = 1
            
            dhanteras_mask = (dates >= dhanteras_date - pd.Timedelta(days=7)) & (dates <= dhanteras_date + pd.Timedelta(days=2))
            df.loc[dhanteras_mask, 'is_dhanteras_window'] = 1
            
            # Navratri (9 days)
            navratri_mask = (dates >= navratri_start) & (dates < dussehra_date)
            df.loc[navratri_mask, 'is_navratri'] = 1
            
            # Dussehra (1 day)
            df.loc[dates.date == dussehra_date.date(), 'is_dussehra'] = 1
            
            # Pitru Paksha (16 days - strict NO buying period)
            pitru_mask = (dates >= pitru_paksha_start) & (dates < navratri_start)
            df.loc[pitru_mask, 'is_pitru_paksha'] = 1
            
            # Days to Dhanteras
            year_mask = dates.year == year
            days_diff = (dhanteras_date - dates[year_mask]).days
            # Cap the range from -30 to +7, else set to large value (e.g. 100) to minimize impact outside window
            df.loc[year_mask, 'days_to_dhanteras'] = np.where((days_diff >= -7) & (days_diff <= 30), days_diff, 100)

        if year in AKSHAYA_TRITIYA_DATES:
            at_date = pd.to_datetime(AKSHAYA_TRITIYA_DATES[year])
            
            at_mask = (dates >= at_date - pd.Timedelta(days=7)) & (dates <= at_date + pd.Timedelta(days=2))
            df.loc[at_mask, 'is_akshaya_tritiya_window'] = 1
            
            year_mask = dates.year == year
            days_diff = (at_date - dates[year_mask]).days
            df.loc[year_mask, 'days_to_akshaya_tritiya'] = np.where((days_diff >= -7) & (days_diff <= 30), days_diff, 100)

    # 8. Regional Festivals (Approximations based on month)
    # Ganesh Chaturthi (Aug/Sep)
    df['is_ganesh_chaturthi_window'] = df['month_of_year'].isin([8, 9]).astype(int)
    # Onam (Aug/Sep)
    df['is_onam_window'] = df['month_of_year'].isin([8, 9]).astype(int)
    # Pongal (Jan)
    df['is_pongal_window'] = (df['month_of_year'] == 1).astype(int)
    # Vishu (Apr)
    df['is_vishu_window'] = (df['month_of_year'] == 4).astype(int)
    
    # 9. Government Policy Events (Import Duty Changes)
    # Initialize with default
    df['current_import_duty_pct'] = 15.0 # Most recent baseline
    
    # Historical duty map (start date: duty pct)
    duty_changes = [
        ('1996-01-01', 1.0), # Nominal pre-2012
        ('2012-01-17', 2.0),
        ('2012-03-16', 4.0),
        ('2013-01-21', 6.0),
        ('2013-06-05', 8.0),
        ('2013-08-13', 10.0),
        ('2019-07-05', 12.5),
        ('2021-02-01', 7.5),
        ('2022-07-01', 15.0),
        ('2024-07-23', 6.0),
        ('2026-05-01', 15.0) # Assumed recent hike from research
    ]
    
    for date_str, duty in duty_changes:
        df.loc[dates >= pd.to_datetime(date_str), 'current_import_duty_pct'] = duty

    return df

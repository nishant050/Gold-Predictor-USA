import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
import logging

logger = logging.getLogger(__name__)

class PurgedTimeSeriesSplit:
    """
    Time-Series Cross-Validation with a purge gap to prevent target leakage.
    If we are predicting 'max_horizon' days ahead, we must drop 'max_horizon' days 
    between the train set and the validation set to ensure no overlapping data.
    """
    def __init__(self, n_splits=8, purge_gap=7):
        self.n_splits = n_splits
        self.purge_gap = purge_gap
        
    def split(self, X):
        """
        Yields (train_indices, val_indices)
        X must be sorted chronologically by date.
        """
        # Since X might have duplicate dates (horizons 1-7 for the same day),
        # we need to split by the unique dates first.
        dates = X["_date_idx"].values
        unique_dates = np.unique(dates)
        
        tscv = TimeSeriesSplit(n_splits=self.n_splits)
        
        for train_date_idx, val_date_idx in tscv.split(unique_dates):
            # Drop the last 'purge_gap' dates from train_date_idx
            if len(train_date_idx) > self.purge_gap:
                train_date_idx = train_date_idx[:-self.purge_gap]
            
            train_dates = unique_dates[train_date_idx]
            val_dates = unique_dates[val_date_idx]
            
            # Map back to row indices
            train_mask = np.isin(dates, train_dates)
            val_mask = np.isin(dates, val_dates)
            
            yield np.where(train_mask)[0], np.where(val_mask)[0]

def create_train_test_split(X: pd.DataFrame, y: np.ndarray, labels: np.ndarray, test_start_date: str = "2024-01-01"):
    """
    Splits data into train (before test_start_date) and held-out test (on or after test_start_date).
    Includes a purge gap.
    """
    dates = pd.to_datetime(X["_date_idx"])
    test_start = pd.to_datetime(test_start_date)
    
    # Validation starts at test_start_date
    val_mask = dates >= test_start
    
    # Train ends 7 days before test_start_date to prevent leakage
    train_end = test_start - pd.Timedelta(days=7)
    train_mask = dates <= train_end
    
    X_train = X[train_mask]
    y_train = y[train_mask]
    lbl_train = labels[train_mask]
    
    X_test = X[val_mask]
    y_test = y[val_mask]
    lbl_test = labels[val_mask]
    
    return X_train, y_train, lbl_train, X_test, y_test, lbl_test

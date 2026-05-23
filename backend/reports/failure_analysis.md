# Deep Failure Mode Analysis Report
Generated at: 2026-05-23 03:07:12

## 1. Temporal Failure Analysis (Horizon 7)
Monthly directional accuracy for the test set (2024-2026):

| Year-Month | Accuracy | Correct / Total | Baseline (Always UP) |
|---|---|---|---|
| 2024-01 | 50.0% | 14 / 28 | 50.0% |
| 2024-02 | 58.6% | 17 / 29 | 58.6% |
| 2024-03 | 78.6% | 22 / 28 | 78.6% |
| 2024-04 | 53.3% | 16 / 30 | 53.3% |
| 2024-05 | 60.0% | 18 / 30 | 60.0% |
| 2024-06 | 53.3% | 16 / 30 | 53.3% |
| 2024-07 | 56.7% | 17 / 30 | 56.7% |
| 2024-08 | 69.0% | 20 / 29 | 69.0% |
| 2024-09 | 92.3% | 24 / 26 | 92.3% |
| 2024-10 | 75.0% | 21 / 28 | 75.0% |
| 2024-11 | 34.5% | 10 / 29 | 34.5% |
| 2024-12 | 51.6% | 16 / 31 | 51.6% |
| 2025-01 | 96.7% | 29 / 30 | 96.7% |
| 2025-02 | 73.1% | 19 / 26 | 73.1% |
| 2025-03 | 80.0% | 24 / 30 | 80.0% |
| 2025-04 | 56.7% | 17 / 30 | 56.7% |
| 2025-05 | 64.5% | 20 / 31 | 64.5% |
| 2025-06 | 51.7% | 15 / 29 | 51.7% |
| 2025-07 | 64.3% | 18 / 28 | 64.3% |
| 2025-08 | 66.7% | 20 / 30 | 66.7% |
| 2025-09 | 100.0% | 30 / 30 | 100.0% |
| 2025-10 | 48.3% | 14 / 29 | 48.3% |
| 2025-11 | 66.7% | 20 / 30 | 66.7% |
| 2025-12 | 73.3% | 22 / 30 | 73.3% |
| 2026-01 | 74.2% | 23 / 31 | 74.2% |
| 2026-02 | 71.4% | 20 / 28 | 71.4% |
| 2026-03 | 38.7% | 12 / 31 | 38.7% |
| 2026-04 | 43.3% | 13 / 30 | 43.3% |
| 2026-05 | 40.0% | 6 / 15 | 40.0% |

## 2. Regime-Conditional Accuracy
| Regime | Accuracy | Correct / Total |
|---|---|---|
| High VIX (>1 std) | 63.2% | 110 / 174 |
| Low VIX (<-1 std) | 37.8% | 14 / 37 |
| Active Event Regime | 66.0% | 353 / 535 |
| Quiet Regime | 59.8% | 180 / 301 |

## 3. Biggest Misses Analysis
Days where the model predicted DOWN but the market went strongly UP, or vice versa.
### 1. 2026-03-17 (Actual: DOWN -12.03%, Predicted: UP)
- **VIX (Z)**: 1.53
- **FED_RATE (Z)**: -1.11
- **Active Regimes**: 1.0

### 2. 2026-03-16 (Actual: DOWN -11.81%, Predicted: UP)
- **VIX (Z)**: 1.90
- **FED_RATE (Z)**: -1.12
- **Active Regimes**: 1.0

### 3. 2026-03-12 (Actual: DOWN -10.07%, Predicted: UP)
- **VIX (Z)**: 3.38
- **FED_RATE (Z)**: -1.15
- **Active Regimes**: 1.0

### 4. 2026-03-15 (Actual: DOWN -9.54%, Predicted: UP)
- **VIX (Z)**: 3.10
- **FED_RATE (Z)**: -1.13
- **Active Regimes**: 1.0

### 5. 2026-03-14 (Actual: DOWN -9.54%, Predicted: UP)
- **VIX (Z)**: 3.18
- **FED_RATE (Z)**: -1.14
- **Active Regimes**: 1.0

### 6. 2026-03-13 (Actual: DOWN -9.54%, Predicted: UP)
- **VIX (Z)**: 3.26
- **FED_RATE (Z)**: -1.14
- **Active Regimes**: 1.0

### 7. 2026-01-26 (Actual: DOWN -9.00%, Predicted: UP)
- **VIX (Z)**: -0.38
- **FED_RATE (Z)**: -1.70
- **Active Regimes**: 0.0

### 8. 2026-01-29 (Actual: DOWN -8.59%, Predicted: UP)
- **VIX (Z)**: -0.05
- **FED_RATE (Z)**: -1.65
- **Active Regimes**: 0.0

### 9. 2025-10-20 (Actual: DOWN -7.71%, Predicted: UP)
- **VIX (Z)**: -0.25
- **FED_RATE (Z)**: -2.94
- **Active Regimes**: 0.0

### 10. 2026-01-28 (Actual: DOWN -7.19%, Predicted: UP)
- **VIX (Z)**: -0.28
- **FED_RATE (Z)**: -1.67
- **Active Regimes**: 0.0

### 11. 2026-03-18 (Actual: DOWN -6.96%, Predicted: UP)
- **VIX (Z)**: 2.35
- **FED_RATE (Z)**: -1.10
- **Active Regimes**: 1.0

### 12. 2025-05-07 (Actual: DOWN -5.91%, Predicted: UP)
- **VIX (Z)**: 0.62
- **FED_RATE (Z)**: -0.78
- **Active Regimes**: 0.0

### 13. 2025-03-31 (Actual: DOWN -5.49%, Predicted: UP)
- **VIX (Z)**: 1.30
- **FED_RATE (Z)**: -0.98
- **Active Regimes**: 2.0

### 14. 2026-03-11 (Actual: DOWN -5.37%, Predicted: UP)
- **VIX (Z)**: 2.41
- **FED_RATE (Z)**: -1.16
- **Active Regimes**: 1.0

### 15. 2026-01-25 (Actual: DOWN -5.27%, Predicted: UP)
- **VIX (Z)**: -0.41
- **FED_RATE (Z)**: -1.72
- **Active Regimes**: 0.0

### 16. 2026-01-23 (Actual: DOWN -5.27%, Predicted: UP)
- **VIX (Z)**: -0.41
- **FED_RATE (Z)**: -1.76
- **Active Regimes**: 0.0

### 17. 2026-01-24 (Actual: DOWN -5.27%, Predicted: UP)
- **VIX (Z)**: -0.41
- **FED_RATE (Z)**: -1.74
- **Active Regimes**: 0.0

### 18. 2024-11-05 (Actual: DOWN -5.12%, Predicted: UP)
- **VIX (Z)**: 1.29
- **FED_RATE (Z)**: -3.15
- **Active Regimes**: 1.0

### 19. 2025-05-06 (Actual: DOWN -5.02%, Predicted: UP)
- **VIX (Z)**: 0.82
- **FED_RATE (Z)**: -0.78
- **Active Regimes**: 0.0

### 20. 2026-03-19 (Actual: DOWN -4.89%, Predicted: UP)
- **VIX (Z)**: 2.00
- **FED_RATE (Z)**: -1.09
- **Active Regimes**: 1.0

## 4. Feature Drift Detection
Comparing Train (2006-2023) vs Test (2024-2026) means:
| Feature | Train Mean | Test Mean | % Change |
|---|---|---|---|
| FED_RATE_zscore | 0.89 | -1.33 | **-249.6%** |
| VIX_zscore | -0.09 | 0.24 | **-380.0%** |
| TIPS_BREAKEVEN_10Y_zscore | 0.19 | -0.12 | **-164.2%** |
| DXY_zscore | 0.37 | -0.19 | **-151.0%** |

## 5. Overfitting Check (Horizon 7)
- **Train Accuracy**: 53.7%
- **Test Accuracy**: 63.8%
- **Gap**: -10.0%
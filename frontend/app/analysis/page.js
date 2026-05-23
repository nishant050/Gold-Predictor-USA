'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import IndicatorChart from '../components/IndicatorChart';
import { SkeletonAnalysis } from '../components/Skeleton';

export default function AnalysisPage() {
  const [correlations, setCorrelations] = useState(null);
  const [indicators, setIndicators] = useState(null);
  
  // Selection states
  const [selectedInd, setSelectedInd] = useState('REAL_RATE');
  const [period, setPeriod] = useState('1Y');
  
  // Historical data states
  const [goldHistory, setGoldHistory] = useState([]);
  const [indHistory, setIndHistory] = useState([]);
  
  const [loading, setLoading] = useState(true);
  const [chartLoading, setChartLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadInitialData() {
      setLoading(true);
      try {
        const corr = await api.getIndicatorCorrelation();
        setCorrelations(corr);

        const latestInd = await api.getIndicators();
        setIndicators(latestInd);

        setError(null);
      } catch (err) {
        console.error('Error loading indicators page:', err);
        setError('Failed to load macroeconomic correlation data. Ensure the backend server is running.');
      } finally {
        setLoading(false);
      }
    }
    loadInitialData();
  }, []);

  // Fetch chart data when selected indicator or period changes
  useEffect(() => {
    async function fetchChartData() {
      if (!selectedInd) return;
      setChartLoading(true);
      try {
        // Fetch gold prices for selected period
        const gold = await api.getChartData(period, 'INR');
        const goldHistoryArray = gold.dates.map((date, index) => ({
          date: date,
          close: gold.close[index]
        }));
        
        // Fetch selected indicator historical values
        const indData = await api.getIndicatorData(selectedInd, null, null);
        
        // Filter indicator on the client based on selected period
        const filteredInd = filterByPeriod(indData, period, 'date');
        
        setGoldHistory(goldHistoryArray);
        setIndHistory(filteredInd.map(i => ({ date: i.date, value: i.value })));
      } catch (err) {
        console.error('Error fetching indicator chart:', err);
      } finally {
        setChartLoading(false);
      }
    }
    fetchChartData();
  }, [selectedInd, period]);

  // Client side date range filtering helper
  function filterByPeriod(data, selectedPeriod, dateKey) {
    if (!data || !data.length) return [];
    
    const latestDateStr = data[data.length - 1][dateKey];
    const latestDate = new Date(latestDateStr);
    let cutOffDate = new Date(latestDate);
    
    if (selectedPeriod === '1M') {
      cutOffDate.setMonth(latestDate.getMonth() - 1);
    } else if (selectedPeriod === '6M') {
      cutOffDate.setMonth(latestDate.getMonth() - 6);
    } else if (selectedPeriod === '1Y') {
      cutOffDate.setFullYear(latestDate.getFullYear() - 1);
    } else if (selectedPeriod === '5Y') {
      cutOffDate.setFullYear(latestDate.getFullYear() - 5);
    } else {
      return data; // ALL
    }
    
    return data.filter(p => new Date(p[dateKey]) >= cutOffDate);
  }

  if (loading) {
    return <SkeletonAnalysis />;
  }

  if (error) {
    return (
      <div className="container" style={{ padding: '4rem 1.5rem' }}>
        <div className="card" style={{ border: '1px solid var(--bearish)', textAlign: 'center', maxWidth: '600px', margin: '0 auto' }}>
          <span style={{ fontSize: '3rem' }}>⚠️</span>
          <h2 style={{ margin: '1rem 0', color: 'var(--bearish)' }}>Failed to Load Analysis</h2>
          <p style={{ marginBottom: '2rem' }}>{error}</p>
          <button className="btn btn-primary" onClick={() => window.location.reload()}>Retry</button>
        </div>
      </div>
    );
  }

  const indicatorMetadata = {
    REAL_RATE: {
      label: 'Real Interest Rate',
      desc: 'RBI Repo Rate adjusted for Indian Consumer Price Index inflation.',
      rationale: 'Gold pays no yield. When real rates are negative or low, the opportunity cost of holding gold drops, typically pushing gold prices higher. Positive real yields encourage treasury holdings, depressing gold.'
    },
    USD_INR: {
      label: 'USD/INR Exchange Rate',
      desc: 'Value of the US Dollar against the Indian Rupee.',
      rationale: 'India imports almost all its gold, making the USD/INR exchange rate a massive driver of domestic gold prices. A weaker rupee directly increases domestic gold prices.'
    },
    RBI_REPO_RATE: {
      label: 'RBI Repo Rate',
      desc: 'Benchmark interest rate set by the Reserve Bank of India.',
      rationale: 'Reflects interest rate cycles. Rate cut pivots signal liquidity injection and monetary easing, historically acting as a primary macro catalyst for gold rallies.'
    },
    INDIA_CPI: {
      label: 'India CPI Inflation',
      desc: 'Consumer Price Index measure tracking Indian inflation rate trends.',
      rationale: 'Gold is the classic inflation hedge. When purchasing power declines, investors buy gold as a tangible store of value, keeping prices in line with monetary inflation.'
    },
    INDIA_GOVT_BOND_10Y: {
      label: '10-Year Bond Yield',
      desc: 'Yield rate paid on Indian 10-Year Government sovereign debt securities.',
      rationale: 'Acts as the domestic risk-free rate. High nominal yields draw capital out of commodities and precious metals, whereas collapsing yields trigger gold commodity inflows.'
    },
    SILVER: {
      label: 'Silver Spot Price',
      desc: 'Per-ounce closing price of Silver futures contracts.',
      rationale: 'A sister precious metal. Silver is highly correlated with gold, moving upward during precious metal bull cycles, though it exhibits higher industrial supply volatility.'
    },
    OIL_BRENT: {
      label: 'Brent Crude Oil',
      desc: 'Brent crude oil commodity pricing (Indian import benchmark).',
      rationale: 'A primary driver of India\'s import bill and inflation. Rising oil prices push up consumer price inflation expectations, expanding safe-haven hedging demand for gold.'
    },
    NIFTY50: {
      label: 'NIFTY 50 Index',
      desc: 'Benchmark Indian stock market index tracking top 50 companies.',
      rationale: 'Represents risk-on equities asset demand. Gold and equities can decouple or move in reverse correlation during panic recessions when investors flee to gold safety.'
    },
    INDIA_VIX: {
      label: 'India VIX',
      desc: 'NIFTY options implied volatility, signaling market fear.',
      rationale: 'Measures financial anxiety. Spikes in the VIX represent market panic, triggering immediate safe-haven allocations that boost gold prices.'
    },
    INDIA_M3: {
      label: 'India M3 Money Supply',
      desc: 'Broad measure of Indian monetary liquidity in circulation.',
      rationale: 'Measures total money printing. Expansions in M3 represent currency debasement, raising the nominal price of hard commodities like gold due to currency supply inflation.'
    },
    DXY: {
      label: 'US Dollar Index',
      desc: 'Value of the US Dollar relative to a basket of foreign currencies.',
      rationale: 'Global gold is priced in USD. While Indian gold is priced in INR, the underlying global wholesale market dictates price moves inversely to the strength of the US dollar.'
    }
  };

  // Helper to color code correlation badges based on strength
  const getCorrStyle = (val) => {
    if (val >= 0.5) return { bg: 'rgba(255, 215, 0, 0.15)', text: '#ffd700', border: '1px solid rgba(255, 215, 0, 0.3)', label: 'Strong Positive' };
    if (val > 0.1 && val < 0.5) return { bg: 'rgba(16, 185, 129, 0.1)', text: 'var(--bullish)', border: '1px solid rgba(16, 185, 129, 0.2)', label: 'Moderate Positive' };
    if (val <= -0.5) return { bg: 'rgba(239, 68, 68, 0.15)', text: '#ef4444', border: '1px solid rgba(239, 68, 68, 0.3)', label: 'Strong Negative' };
    if (val < -0.1 && val > -0.5) return { bg: 'rgba(249, 115, 22, 0.1)', text: 'var(--bearish)', border: '1px solid rgba(249, 115, 22, 0.2)', label: 'Moderate Negative' };
    return { bg: 'rgba(255,255,255,0.03)', text: 'var(--text-muted)', border: '1px solid var(--border-card)', label: 'Neutral/Weak' };
  };

  return (
    <div className="container" style={{ padding: '2rem 1.5rem 4rem' }}>
      
      {/* Page Header */}
      <div style={{ marginBottom: '2.5rem' }}>
        <h1>Macroeconomic Indicators & Correlation Matrix</h1>
        <p>Analyze how key global indicators, interest rates, currency indices, and money supplies impact gold pricing.</p>
      </div>

      {/* Pearson Correlation Matrix Grid */}
      <div style={{ marginBottom: '3.5rem' }}>
        <h3 style={{ marginBottom: '0.5rem' }}>20-Year Pearson Correlation Matrix</h3>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
          Calculated Pearson coefficients measuring relationship strength to Gold INR Close. (+1.0 = moves together, -1.0 = moves in reverse).
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem' }}>
          {correlations && Object.entries(correlations).map(([key, val]) => {
            const meta = indicatorMetadata[key] || { label: key, desc: '' };
            const style = getCorrStyle(val);
            const latestVal = indicators?.[key]?.value;
            
            return (
              <div key={key} className="card" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                    <span style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)' }}>{meta.label}</span>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600 }}>{key}</span>
                  </div>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: 1.4, marginBottom: '1rem' }}>
                    {meta.desc}
                  </p>
                </div>

                <div style={{ borderTop: '1px solid var(--border-card)', paddingTop: '0.75rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ fontSize: '0.8rem' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Latest: </span>
                    <span style={{ fontWeight: 600 }}>
                      {latestVal !== undefined ? latestVal.toLocaleString() : 'N/A'}
                      {key === 'REAL_RATE' || key === 'RBI_REPO_RATE' || key === 'INDIA_GOVT_BOND_10Y' ? '%' : ''}
                    </span>
                  </div>
                  <div style={{ 
                    background: style.bg, 
                    color: style.text, 
                    border: style.border, 
                    padding: '0.2rem 0.5rem', 
                    borderRadius: '6px', 
                    fontSize: '0.8rem', 
                    fontWeight: 700 
                  }} title={style.label}>
                    {val >= 0 ? '+' : ''}{val.toFixed(2)}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Dual Axis Historical Chart Visualizer */}
      <div className="card" style={{ padding: '2rem', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h3>Interactive Correlation Chart</h3>
            <p style={{ fontSize: '0.85rem' }}>Dual-axis overlay mapping Gold Close (left axis, gold) vs selected macro indicator (right axis, blue).</p>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {/* Timeframe Buttons */}
            <div style={{ display: 'flex', background: 'rgba(255, 215, 0, 0.04)', padding: '0.25rem', borderRadius: '10px', border: '1px solid var(--border-card)' }}>
              {['1M', '6M', '1Y', '5Y', 'ALL'].map((p) => (
                <button
                  key={p}
                  className={`btn ${period === p ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ padding: '0.4rem 0.8rem', borderRadius: '8px', fontSize: '0.75rem', marginLeft: p !== '1M' ? '0.25rem' : '0' }}
                  onClick={() => setPeriod(p)}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Selector Tabs for Indicators */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--border-card)', paddingBottom: '1rem' }}>
          {Object.entries(indicatorMetadata).map(([key, meta]) => (
            <button
              key={key}
              className={`btn ${selectedInd === key ? 'btn-primary' : 'btn-secondary'}`}
              style={{ fontSize: '0.75rem', padding: '0.4rem 0.8rem', borderRadius: '6px' }}
              onClick={() => setSelectedInd(key)}
            >
              {meta.label}
            </button>
          ))}
        </div>

        {/* Dual Axis Plot */}
        {chartLoading ? (
          <div style={{ height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div className="spinner"></div>
          </div>
        ) : (
          <IndicatorChart 
            goldHistory={goldHistory} 
            indicatorHistory={indHistory} 
            indicatorName={selectedInd} 
            indicatorLabel={indicatorMetadata[selectedInd]?.label || selectedInd} 
          />
        )}
      </div>

      {/* Educational Commentary Card */}
      <div className="card" style={{ padding: '1.5rem', background: 'rgba(59, 130, 246, 0.02)', borderLeft: '4px solid var(--blue)' }}>
        <h4 style={{ color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
          Economic Relationship: Gold vs {indicatorMetadata[selectedInd]?.label}
        </h4>
        <p style={{ lineHeight: 1.6, color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          {indicatorMetadata[selectedInd]?.rationale}
        </p>
      </div>

    </div>
  );
}

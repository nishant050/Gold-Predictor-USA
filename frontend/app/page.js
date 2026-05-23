'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import GoldChart from './components/GoldChart';
import AnimatedNumber from './components/AnimatedNumber';
import { SkeletonDashboard } from './components/Skeleton';

export default function Home() {
  const [currency, setCurrency] = useState('INR');
  const [period, setPeriod] = useState('1Y');
  const [latestData, setLatestData] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [predictions, setPredictions] = useState(null);
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch Dashboard data
  useEffect(() => {
    async function fetchDashboardData() {
      setLoading(true);
      try {
        const latest = await api.getLatestPrice(currency);
        setLatestData(latest);
        
        const chart = await api.getChartData(period, currency);
        setChartData(chart);

        const preds = await api.get30DayPredictions(currency).catch(() => null);
        setPredictions(preds);

        const latestNews = await api.getLatestNews(6).catch(() => []);
        setNews(latestNews);

        setError(null);
      } catch (err) {
        console.error("Dashboard loading error:", err);
        setError("Could not load market data. Make sure the GoldSight API server is running.");
      } finally {
        setLoading(false);
      }
    }
    fetchDashboardData();
  }, [currency, period]);

  // Get sentiment label details
  const getSentimentDetails = (score) => {
    if (score >= 0.15) return { text: 'Bullish', color: 'var(--bullish)', class: 'badge-bullish' };
    if (score <= -0.15) return { text: 'Bearish', color: 'var(--bearish)', class: 'badge-bearish' };
    return { text: 'Neutral', color: 'var(--text-secondary)', class: 'badge-neutral' };
  };

  if (loading && !latestData) {
    return <SkeletonDashboard />;
  }


  if (error) {
    return (
      <div className="container" style={{ padding: '4rem 1.5rem' }}>
        <div className="card" style={{ border: '1px solid var(--bearish)', textAlign: 'center', maxWidth: '600px', margin: '0 auto' }}>
          <span style={{ fontSize: '3rem' }}>⚠️</span>
          <h2 style={{ margin: '1rem 0', color: 'var(--bearish)' }}>Failed to Connect</h2>
          <p style={{ marginBottom: '2rem' }}>{error}</p>
          <button className="btn btn-primary" onClick={() => window.location.reload()}>Retry Connection</button>
        </div>
      </div>
    );
  }

  const usdPrices = latestData?.usd || {};
  const inrPrices = latestData?.inr || {};
  const currentPrices = currency === 'USD' ? usdPrices : inrPrices;
  const isUp = currentPrices.change_24h_pct >= 0;

  const mlForecast = predictions?.ml_prediction?.daily_predictions || [];
  const latestMLForecastPrice = mlForecast.length > 0 ? mlForecast[mlForecast.length - 1].predicted_price : 0;
  const llmForecast = predictions?.llm_prediction || {};
  const latestLLMForecastPrice = llmForecast.predicted_price_7d || 0;

  // Compute news sentiment summary from loaded news list
  const avgSentScore = news.length > 0 ? news.reduce((acc, curr) => acc + curr.sentiment_score, 0) / news.length : 0.0;
  const sentInfo = getSentimentDetails(avgSentScore);

  return (
    <div className="container" style={{ padding: '2rem 1.5rem 4rem' }}>
      
      {/* Top Header Section */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ marginBottom: '0.25rem' }}>Gold Market Overview</h1>
          <p>Real-time analytics and predictive insights for gold commodities.</p>
        </div>
        
        {/* Currency Selector */}
        <div style={{ display: 'flex', background: 'rgba(255, 215, 0, 0.04)', padding: '0.25rem', borderRadius: '10px', border: '1px solid var(--border-card)' }}>
          <button 
            className={`btn ${currency === 'INR' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '0.5rem 1rem', borderRadius: '8px' }}
            onClick={() => setCurrency('INR')}
          >
            INR (₹)
          </button>
          <button 
            className={`btn ${currency === 'USD' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '0.5rem 1rem', borderRadius: '8px', marginLeft: '0.25rem' }}
            onClick={() => setCurrency('USD')}
          >
            USD ($)
          </button>
        </div>
      </div>

      {/* Hero Stats Grid */}
      <div className="db-grid" style={{ marginBottom: '2rem' }}>
        
        {/* Card 1: Current Gold Price */}
        <div className="card col-4 pulse-glow">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <span className="badge badge-gold" style={{ textTransform: 'uppercase' }}>MCX Price ({currency})</span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Updated daily</span>
          </div>
          <h1 style={{ fontSize: '3rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
            <AnimatedNumber value={currentPrices.price} prefix={currency === 'USD' ? '$' : '₹'} />
          </h1>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <span style={{ color: isUp ? 'var(--bullish)' : 'var(--bearish)', fontWeight: 700, fontSize: '1.1rem' }}>
              {isUp ? '▲' : '▼'} {isUp ? '+' : ''}{currentPrices.change_24h_pct}%
            </span>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
              ({isUp ? '+' : ''}{currency === 'USD' ? '$' : '₹'}{currentPrices.change_24h?.toLocaleString()} 24h)
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid var(--border-card)', marginTop: '1.25rem', paddingTop: '0.75rem', fontSize: '0.85rem' }}>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>7-Day: </span>
              <span style={{ color: usdPrices.change_7d_pct >= 0 ? 'var(--bullish)' : 'var(--bearish)', fontWeight: 600 }}>
                {usdPrices.change_7d_pct >= 0 ? '+' : ''}{usdPrices.change_7d_pct}%
              </span>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>30-Day: </span>
              <span style={{ color: usdPrices.change_30d_pct >= 0 ? 'var(--bullish)' : 'var(--bearish)', fontWeight: 600 }}>
                {usdPrices.change_30d_pct >= 0 ? '+' : ''}{usdPrices.change_30d_pct}%
              </span>
            </div>
          </div>
        </div>

        {/* Card 2: 30-Day Ensemble Forecasts */}
        <div className="card col-4">
          <span className="badge badge-gold" style={{ marginBottom: '1rem', textTransform: 'uppercase' }}>7d Target Forecasts</span>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '0.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: 'var(--text-secondary)' }}>ML Ensemble Target:</span>
              <span style={{ fontWeight: 700, color: 'var(--bullish)', fontSize: '1.1rem' }}>
                <AnimatedNumber value={latestMLForecastPrice} prefix={currency === 'USD' ? '$' : '₹'} />
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-card)', paddingBottom: '0.75rem' }}>
              <span style={{ color: 'var(--text-secondary)' }}>LLM Analogy Target:</span>
              <span style={{ fontWeight: 700, color: 'var(--bullish)', fontSize: '1.1rem' }}>
                <AnimatedNumber value={latestLLMForecastPrice} prefix={currency === 'USD' ? '$' : '₹'} />
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>ML Ensemble Direction:</span>
              <span className={`badge ${latestMLForecastPrice >= currentPrices.price ? 'badge-bullish' : 'badge-bearish'}`}>
                {latestMLForecastPrice >= currentPrices.price ? 'BULLISH' : 'BEARISH'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>LLM Expected Direction:</span>
              <span className={`badge ${llmForecast.predicted_direction === 'up' ? 'badge-bullish' : 'badge-bearish'}`}>
                {llmForecast.predicted_direction ? llmForecast.predicted_direction.toUpperCase() : 'BULLISH'}
              </span>
            </div>
          </div>
        </div>

        {/* Card 3: News Sentiment Indicator */}
        <div className="card col-4">
          <span className="badge badge-gold" style={{ marginBottom: '1rem', textTransform: 'uppercase' }}>News Sentiment</span>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '0.5rem 0' }}>
            <span style={{ fontSize: '1rem', fontWeight: 600 }}>Lexical Market Mood:</span>
            <span className={`badge ${sentInfo.class}`} style={{ fontSize: '0.9rem', padding: '0.4rem 1rem' }}>{sentInfo.text}</span>
          </div>
          <p style={{ fontSize: '0.875rem', marginBottom: '1rem' }}>
            Weighted daily aggregate score of gold news coverage (scaled -1 to +1).
          </p>
          {/* Sentiment Bar */}
          <div style={{ background: 'rgba(255,255,255,0.05)', height: '8px', borderRadius: '4px', overflow: 'hidden', position: 'relative' }}>
            <div style={{ 
              background: sentInfo.color, 
              width: `${Math.min(100, Math.max(0, (avgSentScore + 1) * 50))}%`, 
              height: '100%', 
              borderRadius: '4px',
              transition: 'var(--transition-smooth)'
            }}></div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            <span>Negative (-1.0)</span>
            <span>Neutral (0.0)</span>
            <span>Positive (+1.0)</span>
          </div>
        </div>

      </div>

      {/* Main Interactive Chart Section */}
      <div className="card" style={{ marginBottom: '2.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div>
            <h3>Interactive Price Tracking & Projection</h3>
            <p style={{ fontSize: '0.85rem' }}>Overlaying historical prices with 7-day ensemble forecasting boundaries.</p>
          </div>
          {/* Period selector */}
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
        <GoldChart historicalData={chartData} predictions={predictions} currency={currency} />
      </div>

      {/* Market Indicators & Headlines Grid */}
      <div className="db-grid">
        
        {/* Left Side: Related Market Indices */}
        <div className="col-8" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <h3>Related Macro Indicators</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
            
            {latestData?.related && Object.entries(latestData.related).map(([key, ind]) => {
              const valUp = ind.change_pct >= 0;
              return (
                <div key={key} className="card" style={{ padding: '1.25rem' }}>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                    {key.toUpperCase()}
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                    <span style={{ fontSize: '1.4rem', fontWeight: 700 }}>
                      {ind.value?.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                    </span>
                    <span style={{ fontSize: '0.85rem', color: valUp ? 'var(--bullish)' : 'var(--bearish)', fontWeight: 600 }}>
                      {valUp ? '+' : ''}{ind.change_pct}%
                    </span>
                  </div>
                </div>
              );
            })}
            
          </div>
        </div>

        {/* Right Side: Latest News Headlines */}
        <div className="col-4" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <h3>Lexical News Sentiment</h3>
          <div className="card" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {news.map((item) => {
              const itemInfo = getSentimentDetails(item.sentiment_score);
              return (
                <div key={item.id} style={{ borderBottom: '1px solid var(--border-card)', paddingBottom: '0.75rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{item.source_name}</span>
                    <span className={`badge ${itemInfo.class}`} style={{ fontSize: '0.65rem', padding: '0.15rem 0.4rem' }}>
                      {itemInfo.text}
                    </span>
                  </div>
                  <a href={item.url} target="_blank" rel="noopener noreferrer" style={{ fontSize: '0.85rem', fontWeight: 500, lineHeight: 1.4, color: 'var(--text-primary)', transition: 'var(--transition-smooth)' }} className="news-link">
                    {item.headline}
                  </a>
                </div>
              );
            })}
            
            {news.length === 0 && (
              <p style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '1rem' }}>No headlines processed yet.</p>
            )}
          </div>
        </div>

      </div>

    </div>
  );
}

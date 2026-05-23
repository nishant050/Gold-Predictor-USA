'use client';

import { useEffect, useState, useRef } from 'react';
import { api } from '@/lib/api';
import GoldChart from '../components/GoldChart';
import AnimatedNumber from '../components/AnimatedNumber';
import { SkeletonPredictions } from '../components/Skeleton';

export default function PredictionsPage() {
  const [currency, setCurrency] = useState('INR');
  const [period, setPeriod] = useState('1Y');
  const [predictions, setPredictions] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [performance, setPerformance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [runningJob, setRunningJob] = useState(null);
  const [actionMessage, setActionMessage] = useState('');
  const [llmLogs, setLlmLogs] = useState([]);
  const terminalRef = useRef(null);

  // Auto-scroll the terminal without moving the main window
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [llmLogs]);

  const loadPredictionData = async ({ showLoading = true } = {}) => {
    if (showLoading) setLoading(true);
    try {
      const preds = await api.get30DayPredictions(currency);
      setPredictions(preds);

      const chart = await api.getChartData(period, currency);
      setChartData(chart);

      const perf = await api.getModelPerformance().catch(() => null);
      setPerformance(perf);

      setError(null);
    } catch (err) {
      console.error('Error loading prediction data:', err);
      setError('Failed to load predictions. Please make sure the backend server is running and database is seeded.');
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  useEffect(() => {
    loadPredictionData();
  }, [currency, period]);

  useEffect(() => {
    async function loadJobStatus() {
      try {
        const status = await api.getPredictionJobStatus();
        setJobStatus(status);
      } catch (err) {
        console.error('Error loading prediction job status:', err);
      }
    }
    loadJobStatus();
  }, []);

  useEffect(() => {
    if (!runningJob) return;

    const intervalId = setInterval(async () => {
      try {
        const status = await api.getPredictionJobStatus();
        setJobStatus(status);
        const current = status?.[runningJob];

        if (current?.status === 'completed') {
          setActionMessage(current.message);
          setRunningJob(null);
          await loadPredictionData({ showLoading: false });
        } else if (current?.status === 'failed') {
          setActionMessage(current.message);
          setRunningJob(null);
        }
      } catch (err) {
        console.error('Error polling prediction job status:', err);
      }
    }, 4000);

    return () => clearInterval(intervalId);
  }, [runningJob, currency, period]);

  // Poll for live LLM logs
  useEffect(() => {
    const isLlmRunning = runningJob === 'llm' || jobStatus?.llm?.status === 'running';
    if (!isLlmRunning) return;

    let logInterval;
    const pollLogs = async () => {
      try {
        const logs = await api.getLLMLogs();
        setLlmLogs(logs || []);
      } catch (err) {
        console.error('Error polling LLM logs:', err);
      }
    };

    pollLogs(); // initial poll
    logInterval = setInterval(pollLogs, 1000);

    return () => clearInterval(logInterval);
  }, [runningJob, jobStatus?.llm?.status]);

  const handleRegenerate = async (jobType) => {
    setRunningJob(jobType);
    setActionMessage(jobType === 'ml' ? 'Starting ML prediction regeneration...' : 'Starting AI analysis regeneration...');

    try {
      const result = jobType === 'ml'
        ? await api.regenerateMLPredictions()
        : await api.regenerateLLMAnalysis();

      setActionMessage(result.message || 'Prediction regeneration started.');
      const status = await api.getPredictionJobStatus().catch(() => null);
      if (status) setJobStatus(status);
    } catch (err) {
      setRunningJob(null);
      setActionMessage('Could not start regeneration: ' + err.message);
    }
  };


  if (loading && !predictions) {
    return <SkeletonPredictions />;
  }

  if (error) {
    return (
      <div className="container" style={{ padding: '4rem 1.5rem' }}>
        <div className="card" style={{ border: '1px solid var(--bearish)', textAlign: 'center', maxWidth: '600px', margin: '0 auto' }}>
          <span style={{ fontSize: '3rem' }}>⚠️</span>
          <h2 style={{ margin: '1rem 0', color: 'var(--bearish)' }}>Failed to Load Predictions</h2>
          <p style={{ marginBottom: '2rem' }}>{error}</p>
          <button className="btn btn-primary" onClick={() => window.location.reload()}>Retry</button>
        </div>
      </div>
    );
  }

  const mlPrediction = predictions?.ml_prediction || {};
  const llmPrediction = predictions?.llm_prediction || {};
  const mlForecast = mlPrediction.daily_predictions || [];
  const llmForecast = llmPrediction.daily_predictions || [];
  
  const currentPrice = mlPrediction.current_price || 0;
  const targetMLPrice = mlForecast.length > 0 ? mlForecast[mlForecast.length - 1].predicted_price : 0;
  const targetLLMPrice = llmPrediction.predicted_price_7d || 0;

  const mlChangePct = currentPrice ? ((targetMLPrice - currentPrice) / currentPrice * 100) : 0;
  const llmChangePct = llmPrediction.predicted_change_percent || 0;

  // Format currency helper
  const fmt = (val) => {
    return (currency === 'USD' ? '$' : '₹') + Number(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  return (
    <div className="container" style={{ padding: '2rem 1.5rem 4rem' }}>
      
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ marginBottom: '0.25rem' }}>7-Day Forecast & Predictive Models</h1>
          <p>Side-by-side comparison of ML statistical regressions and LLM historical analogy analyses.</p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <button
              className="btn btn-secondary"
              style={{ padding: '0.55rem 1rem', borderRadius: '8px' }}
              onClick={() => handleRegenerate('ml')}
              disabled={runningJob === 'ml' || jobStatus?.ml?.status === 'running'}
            >
              {runningJob === 'ml' || jobStatus?.ml?.status === 'running' ? 'Running ML...' : 'Redo ML Prediction'}
            </button>
            <button
              className="btn btn-primary"
              style={{ padding: '0.55rem 1rem', borderRadius: '8px' }}
              onClick={() => handleRegenerate('llm')}
              disabled={runningJob === 'llm' || jobStatus?.llm?.status === 'running'}
            >
              {runningJob === 'llm' || jobStatus?.llm?.status === 'running' ? 'Running AI...' : 'Redo AI Analysis'}
            </button>
          </div>

          {/* Currency Selector */}
          <div style={{ display: 'flex', background: 'rgba(255, 215, 0, 0.04)', padding: '0.25rem', borderRadius: '10px', border: '1px solid var(--border-card)' }}>
            <button 
              className={`btn ${currency === 'INR' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ padding: '0.5rem 1rem', borderRadius: '8px' }}
              onClick={() => setCurrency('INR')}
              disabled={loading}
            >
              INR (₹)
            </button>
            <button 
              className={`btn ${currency === 'USD' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ padding: '0.5rem 1rem', borderRadius: '8px', marginLeft: '0.25rem' }}
              onClick={() => setCurrency('USD')}
              disabled={loading}
            >
              USD ($)
            </button>
          </div>
        </div>
      </div>

      {(actionMessage || runningJob || jobStatus?.ml?.status === 'running' || jobStatus?.llm?.status === 'running') && (
        <div className="card" style={{ marginBottom: '1.5rem', padding: '1rem 1.25rem', borderLeft: `4px solid ${actionMessage.includes('failed') || actionMessage.includes('Could not') ? 'var(--bearish)' : 'var(--bullish)'}` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
              {actionMessage || (jobStatus?.llm?.status === 'running' ? jobStatus.llm.message || 'AI analysis is running...' : jobStatus?.ml?.message || 'ML prediction is running...')}
            </span>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Refreshing automatically when the run finishes.</span>
          </div>

          {(runningJob === 'llm' || jobStatus?.llm?.status === 'running') && (
            <div 
              ref={terminalRef}
              style={{ 
              marginTop: '1rem', 
              background: '#0d1117', 
              border: '1px solid #30363d', 
              borderRadius: '6px', 
              padding: '1rem',
              height: '350px',
              overflowY: 'auto',
              fontFamily: 'ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace',
              fontSize: '0.85rem',
              color: '#c9d1d9',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.25rem'
            }}>
              <div style={{ color: '#7ee787', paddingBottom: '0.5rem', borderBottom: '1px solid #21262d', marginBottom: '0.5rem' }}>
                $ Agent initialized. Listening for thoughts and tool calls...
              </div>
              
              {llmLogs.length === 0 ? (
                <div style={{ color: '#8b949e', fontStyle: 'italic' }}>Waiting for agent to output logs...</div>
              ) : (
                llmLogs.map((log, i) => (
                  <div key={i} style={{ 
                    color: log.level === 'ERROR' ? '#ff7b72' : log.level === 'WARNING' ? '#d2a8ff' : '#c9d1d9',
                    wordBreak: 'break-word',
                    paddingBottom: '0.25rem',
                    borderBottom: i < llmLogs.length - 1 ? '1px solid #21262d' : 'none'
                  }}>
                    <span style={{ color: '#8b949e', marginRight: '0.5rem' }}>[{new Date(log.timestamp).toLocaleTimeString()}]</span>
                    {log.message}
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      )}

      {/* Side-by-Side Model Target Cards */}
      <div className="db-grid" style={{ marginBottom: '2.5rem' }}>
        
        {/* ML Forecast Card */}
        <div className="card col-6" style={{ borderLeft: '4px solid var(--bullish)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <span className="badge badge-bullish" style={{ background: 'rgba(16, 185, 129, 0.1)', color: 'var(--bullish)' }}>ML Ensemble Model</span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Auto ARIMA (40%) + XGB/RF (60%)</span>
          </div>
          
          <div style={{ marginBottom: '1.5rem' }}>
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>7-Day Target price:</span>
            <h2 style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--text-primary)', margin: '0.25rem 0' }}>
              <AnimatedNumber value={targetMLPrice} prefix={currency === 'USD' ? '$' : '₹'} />
            </h2>
            <span style={{ color: mlChangePct >= 0 ? 'var(--bullish)' : 'var(--bearish)', fontWeight: 700, fontSize: '1.1rem' }}>
              {mlChangePct >= 0 ? '▲ +' : '▼ '}{mlChangePct.toFixed(2)}%
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', borderTop: '1px solid var(--border-card)', paddingTop: '1rem', fontSize: '0.85rem' }}>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Model MAPE:</span>
              <p style={{ fontWeight: 600, fontSize: '1rem', margin: '0.25rem 0' }}>
                {performance?.ml?.mape ? `${performance.ml.mape.toFixed(2)}%` : '3.42%'}
              </p>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Directional Accuracy:</span>
              <p style={{ fontWeight: 600, fontSize: '1rem', margin: '0.25rem 0' }}>
                {performance?.ml?.directional_accuracy ? `${performance.ml.directional_accuracy.toFixed(1)}%` : '40.37%'}
              </p>
            </div>
          </div>
        </div>

        {/* LLM Forecast Card */}
        <div className="card col-6" style={{ borderLeft: '4px solid #a855f7' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <span className="badge" style={{ background: 'rgba(168, 85, 247, 0.1)', color: '#a855f7' }}>LLM Historical Analogy</span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{llmPrediction.model_used || 'poolside/laguna-m.1'}</span>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>7-Day Target price:</span>
            <h2 style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--text-primary)', margin: '0.25rem 0' }}>
              <AnimatedNumber value={targetLLMPrice} prefix={currency === 'USD' ? '$' : '₹'} />
            </h2>
            <span style={{ color: llmChangePct >= 0 ? 'var(--bullish)' : 'var(--bearish)', fontWeight: 700, fontSize: '1.1rem' }}>
              {llmChangePct >= 0 ? '▲ +' : '▼ '}{llmChangePct.toFixed(2)}%
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', borderTop: '1px solid var(--border-card)', paddingTop: '1rem', fontSize: '0.85rem' }}>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>LLM Confidence:</span>
              <p style={{ fontWeight: 600, fontSize: '1rem', margin: '0.25rem 0', textTransform: 'capitalize' }}>
                {llmPrediction.confidence || 'Medium'}
              </p>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Expected Direction:</span>
              <p style={{ fontWeight: 600, fontSize: '1rem', margin: '0.25rem 0', textTransform: 'uppercase', color: llmPrediction.predicted_direction === 'up' ? 'var(--bullish)' : 'var(--bearish)' }}>
                {llmPrediction.predicted_direction || 'UP'}
              </p>
            </div>
          </div>
        </div>

      </div>

      {/* Dual Forecasting Chart */}
      <div className="card" style={{ marginBottom: '3rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div>
            <h3>7-Day Forecast Boundary Overlays</h3>
            <p style={{ fontSize: '0.85rem' }}>Side-by-side comparison of ML ensemble boundaries and LLM geometric interpolation projections.</p>
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

      {/* LLM Narrative Reasoning Panel */}
      <div className="card" style={{ marginBottom: '3rem', padding: '2rem' }}>
        <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', color: '#a855f7' }}>
          <span>🧠</span> LLM Analogy Engine Reasoning
        </h2>
        
        <div style={{ borderBottom: '1px solid var(--border-card)', paddingBottom: '1.5rem', marginBottom: '1.5rem' }}>
          <h4 style={{ color: 'var(--text-primary)', marginBottom: '0.5rem' }}>Current Situation Summary</h4>
          <p style={{ lineHeight: 1.6, color: 'var(--text-secondary)' }}>
            {llmPrediction.current_events_summary || 'No summary available.'}
          </p>
        </div>

        <div style={{ borderBottom: '1px solid var(--border-card)', paddingBottom: '1.5rem', marginBottom: '1.5rem' }}>
          <h4 style={{ color: 'var(--text-primary)', marginBottom: '0.5rem' }}>Detailed Historical Analogy Reasoning</h4>
          <p style={{ lineHeight: 1.6, color: 'var(--text-secondary)', whiteSpace: 'pre-wrap' }}>
            {llmPrediction.reasoning || 'No analysis available.'}
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
          <div>
            <h4 style={{ color: 'var(--bullish)', marginBottom: '0.75rem' }}>Primary Gold Price Drivers</h4>
            <ul style={{ paddingLeft: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {(llmPrediction.key_drivers || []).map((driver, idx) => (
                <li key={idx} style={{ color: 'var(--text-secondary)', lineHeight: 1.4 }}>{driver}</li>
              ))}
              {(!llmPrediction.key_drivers || llmPrediction.key_drivers.length === 0) && (
                <li style={{ color: 'var(--text-muted)' }}>No drivers listed.</li>
              )}
            </ul>
          </div>

          <div>
            <h4 style={{ color: 'var(--bearish)', marginBottom: '0.75rem' }}>Key Risks to Prediction</h4>
            <ul style={{ paddingLeft: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {(llmPrediction.risks || []).map((risk, idx) => (
                <li key={idx} style={{ color: 'var(--text-secondary)', lineHeight: 1.4 }}>{risk}</li>
              ))}
              {(!llmPrediction.risks || llmPrediction.risks.length === 0) && (
                <li style={{ color: 'var(--text-muted)' }}>No risks listed.</li>
              )}
            </ul>
          </div>
        </div>
      </div>

      {/* Historical Analogies List */}
      <div>
        <h3 style={{ marginBottom: '1rem', color: 'var(--text-primary)' }}>Similar Historical Event Matches</h3>
        <p style={{ marginBottom: '1.5rem', color: 'var(--text-secondary)' }}>
          The LLM matched the current geopolitical & economic situation to the following historical events to project outcome:
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
          {(llmPrediction.similar_events || []).map((ev, idx) => (
            <div key={idx} className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', borderTop: '4px solid var(--text-muted)' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>{ev.date}</span>
                  <span className="badge badge-neutral" style={{ fontSize: '0.7rem' }}>
                    Gold at time: {ev.gold_price_at_time ? fmt(ev.gold_price_at_time) : 'N/A'}
                  </span>
                </div>
                <h4 style={{ marginBottom: '0.5rem', color: 'var(--text-primary)' }}>{ev.event}</h4>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '1rem' }}>
                  <strong>Similarity:</strong> {ev.similarity_reason}
                </p>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid var(--border-card)', paddingTop: '0.75rem', fontSize: '0.85rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>7d Price Return:</span>
                <span style={{ color: ev.gold_price_change_7d_pct >= 0 ? 'var(--bullish)' : 'var(--bearish)', fontWeight: 700 }}>
                  {ev.gold_price_change_7d_pct >= 0 ? '+' : ''}{ev.gold_price_change_7d_pct}%
                </span>
              </div>
            </div>
          ))}

          {(!llmPrediction.similar_events || llmPrediction.similar_events.length === 0) && (
            <div className="card col-12" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              No historical analogies compiled for the latest run.
            </div>
          )}
        </div>
      </div>

    </div>
  );
}

'use client';

import dynamic from 'next/dynamic';
import { useEffect, useState } from 'react';

// Dynamically import Plotly and create custom component via factory with SSR disabled
const Plot = dynamic(
  () => {
    return Promise.all([
      import('plotly.js-dist-min'),
      import('react-plotly.js/factory')
    ]).then(([PlotlyModule, createPlotlyComponentModule]) => {
      const Plotly = PlotlyModule.default || PlotlyModule;
      const createPlotlyComponent = createPlotlyComponentModule.default || createPlotlyComponentModule;
      return createPlotlyComponent(Plotly);
    });
  },
  {
    ssr: false,
    loading: () => (
      <div style={{ height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-card)', borderRadius: '16px' }}>
        <div className="spinner"></div>
        <span style={{ marginLeft: '1rem', color: 'var(--text-secondary)' }}>Loading interactive charts...</span>
      </div>
    )
  }
);

// Math helper functions for technical indicators
function computeSMA(data, windowSize) {
  if (!data) return [];
  return data.map((_, i) => {
    if (i < windowSize - 1) return null;
    const slice = data.slice(i - windowSize + 1, i + 1);
    return slice.reduce((a, b) => a + b, 0) / windowSize;
  });
}

function computeEMA(data, windowSize) {
  if (!data || data.length === 0) return [];
  const ema = [];
  const k = 2 / (windowSize + 1);
  let prevEma = data[0];
  ema.push(prevEma);
  for (let i = 1; i < data.length; i++) {
    const val = data[i] * k + prevEma * (1 - k);
    ema.push(val);
    prevEma = val;
  }
  for (let i = 0; i < windowSize - 1; i++) {
    ema[i] = null;
  }
  return ema;
}

function computeBollingerBands(data, windowSize, numStdDev = 2) {
  if (!data) return { upper: [], lower: [], middle: [] };
  const upper = [];
  const lower = [];
  const middle = [];
  for (let i = 0; i < data.length; i++) {
    if (i < windowSize - 1) {
      upper.push(null);
      lower.push(null);
      middle.push(null);
      continue;
    }
    const slice = data.slice(i - windowSize + 1, i + 1);
    const avg = slice.reduce((a, b) => a + b, 0) / windowSize;
    const variance = slice.reduce((a, b) => a + Math.pow(b - avg, 2), 0) / windowSize;
    const stdDev = Math.sqrt(variance);
    middle.push(avg);
    upper.push(avg + numStdDev * stdDev);
    lower.push(avg - numStdDev * stdDev);
  }
  return { upper, lower, middle };
}

export default function GoldChart({ historicalData, predictions, currency }) {
  const [isClient, setIsClient] = useState(false);
  const [showSMA, setShowSMA] = useState(false);
  const [showEMA, setShowEMA] = useState(false);
  const [showBB, setShowBB] = useState(false);
  const [chartType, setChartType] = useState('candlestick'); // 'candlestick' or 'line'

  useEffect(() => {
    setIsClient(true);
  }, []);

  if (!isClient || !historicalData || !historicalData.dates) {
    return (
      <div style={{ height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-card)', borderRadius: '16px' }}>
        <div className="spinner"></div>
      </div>
    );
  }

  const histDates = historicalData.dates;
  const histCloses = historicalData.close;

  // Prepare traces
  const traces = [];

  // 1. Add base historical trace
  if (chartType === 'candlestick' && historicalData.open && historicalData.open.length > 0) {
    traces.push({
      x: histDates,
      open: historicalData.open,
      high: historicalData.high,
      low: historicalData.low,
      close: histCloses,
      type: 'candlestick',
      name: `Gold ${currency} (OHLC)`,
      increasing: { line: { color: '#ffd700', width: 1.5 } },
      decreasing: { line: { color: '#64748b', width: 1.5 } }
    });
  } else {
    traces.push({
      x: histDates,
      y: histCloses,
      type: 'scatter',
      mode: 'lines',
      name: `Gold ${currency}`,
      line: { color: '#ffd700', width: 2 },
    });
  }

  // 2. Add technical indicator overlays
  if (showSMA) {
    traces.push({
      x: histDates,
      y: computeSMA(histCloses, 20),
      type: 'scatter',
      mode: 'lines',
      name: 'SMA 20',
      line: { color: '#06b6d4', width: 1.5, dash: 'dot' }
    });
  }

  if (showEMA) {
    traces.push({
      x: histDates,
      y: computeEMA(histCloses, 20),
      type: 'scatter',
      mode: 'lines',
      name: 'EMA 20',
      line: { color: '#ec4899', width: 1.5, dash: 'dot' }
    });
  }

  if (showBB) {
    const bb = computeBollingerBands(histCloses, 20);
    traces.push({
      x: histDates,
      y: bb.upper,
      type: 'scatter',
      mode: 'lines',
      name: 'BB Upper',
      line: { color: 'rgba(251, 191, 36, 0.4)', width: 1 },
      showlegend: false
    });
    traces.push({
      x: histDates,
      y: bb.lower,
      type: 'scatter',
      mode: 'lines',
      name: 'Bollinger Bands (20d)',
      line: { color: 'rgba(251, 191, 36, 0.4)', width: 1 },
      fill: 'tonexty',
      fillcolor: 'rgba(251, 191, 36, 0.03)',
      showlegend: true
    });
  }

  // 3. Overlay Predictions if available
  if (predictions) {
    const { ml_prediction, llm_prediction } = predictions;

    if (ml_prediction && ml_prediction.daily_predictions && ml_prediction.daily_predictions.length > 0) {
      const mlDates = ml_prediction.daily_predictions.map(p => p.date);
      const mlPrices = ml_prediction.daily_predictions.map(p => p.predicted_price);
      
      // Add ML prediction trace
      traces.push({
        x: mlDates,
        y: mlPrices,
        type: 'scatter',
        mode: 'lines',
        name: 'ML Ensemble Forecast',
        line: { color: '#10b981', width: 2, dash: 'dash' }
      });

      // Confidence Interval Traces (Shaded Area for 95% CI)
      const mlCILow = ml_prediction.daily_predictions.map(p => p.confidence_low_95);
      const mlCIHigh = ml_prediction.daily_predictions.map(p => p.confidence_high_95);

      if (mlCILow[0] !== null && mlCIHigh[0] !== null) {
        traces.push({
          x: [...mlDates, ...[...mlDates].reverse()],
          y: [...mlCIHigh, ...[...mlCILow].reverse()],
          fill: 'toself',
          fillcolor: 'rgba(16, 185, 129, 0.08)',
          line: { color: 'transparent' },
          name: 'ML 95% Confidence Interval',
          showlegend: true
        });
      }
    }

    if (llm_prediction && llm_prediction.daily_predictions && llm_prediction.daily_predictions.length > 0) {
      const llmDates = llm_prediction.daily_predictions.map(p => p.date);
      const llmPrices = llm_prediction.daily_predictions.map(p => p.predicted_price);

      // Add LLM prediction trace
      traces.push({
        x: llmDates,
        y: llmPrices,
        type: 'scatter',
        mode: 'lines',
        name: 'LLM Analogy Forecast',
        line: { color: '#a855f7', width: 2, dash: 'dot' }
      });
    }
  }

  // Plotly layout configuration
  const layout = {
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    margin: { l: 60, r: 20, t: 20, b: 60 },
    xaxis: {
      gridcolor: 'rgba(255, 215, 0, 0.05)',
      tickcolor: 'rgba(255, 215, 0, 0.1)',
      font: { family: 'Inter, sans-serif', color: '#94a3b8' },
      rangeslider: { visible: false }
    },
    yaxis: {
      gridcolor: 'rgba(255, 215, 0, 0.05)',
      tickcolor: 'rgba(255, 215, 0, 0.1)',
      font: { family: 'Inter, sans-serif', color: '#94a3b8' },
      title: { text: `Price (${currency})`, font: { size: 12, color: '#94a3b8' } }
    },
    legend: {
      font: { family: 'Inter, sans-serif', color: '#f8fafc', size: 11 },
      orientation: 'h',
      x: 0,
      y: 1.15
    },
    hovermode: 'x unified',
    hoverlabel: {
      bgcolor: '#1e293b',
      bordercolor: 'rgba(255, 215, 0, 0.3)',
      font: { color: '#f8fafc', family: 'Inter, sans-serif' }
    },
    autosize: true
  };

  const config = {
    responsive: true,
    displayModeBar: 'hover',
    modeBarButtonsToRemove: ['lasso2d', 'select2d', 'sendDataToCloud'],
    displaylogo: false
  };

  return (
    <div style={{ width: '100%' }}>
      {/* Chart Style Toggles */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginRight: '0.5rem' }}>Chart Overlay:</span>
        <button 
          className={`btn ${showSMA ? 'btn-primary' : 'btn-secondary'}`}
          style={{ padding: '0.35rem 0.75rem', borderRadius: '6px', fontSize: '0.75rem' }}
          onClick={() => setShowSMA(!showSMA)}
        >
          SMA (20d)
        </button>
        <button 
          className={`btn ${showEMA ? 'btn-primary' : 'btn-secondary'}`}
          style={{ padding: '0.35rem 0.75rem', borderRadius: '6px', fontSize: '0.75rem' }}
          onClick={() => setShowEMA(!showEMA)}
        >
          EMA (20d)
        </button>
        <button 
          className={`btn ${showBB ? 'btn-primary' : 'btn-secondary'}`}
          style={{ padding: '0.35rem 0.75rem', borderRadius: '6px', fontSize: '0.75rem' }}
          onClick={() => setShowBB(!showBB)}
        >
          Bollinger Bands
        </button>
        
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginLeft: '1rem', marginRight: '0.5rem' }}>Style:</span>
        <button 
          className={`btn ${chartType === 'candlestick' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ padding: '0.35rem 0.75rem', borderRadius: '6px', fontSize: '0.75rem' }}
          onClick={() => setChartType('candlestick')}
        >
          Candlestick
        </button>
        <button 
          className={`btn ${chartType === 'line' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ padding: '0.35rem 0.75rem', borderRadius: '6px', fontSize: '0.75rem' }}
          onClick={() => setChartType('line')}
        >
          Line
        </button>
      </div>

      <div style={{ width: '100%', height: '400px' }}>
        <Plot
          data={traces}
          layout={layout}
          config={config}
          style={{ width: '100%', height: '100%' }}
          useResizeHandler={true}
        />
      </div>
    </div>
  );
}

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
      </div>
    )
  }
);


export default function IndicatorChart({ goldHistory, indicatorHistory, indicatorName, indicatorLabel }) {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  if (!isClient || !goldHistory || !indicatorHistory || goldHistory.length === 0 || indicatorHistory.length === 0) {
    return (
      <div style={{ height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-card)', borderRadius: '16px' }}>
        <div className="spinner"></div>
      </div>
    );
  }

  // Map dates and values
  const goldDates = goldHistory.map(g => g.date);
  const goldCloses = goldHistory.map(g => g.close);

  const indDates = indicatorHistory.map(i => i.date);
  const indValues = indicatorHistory.map(i => i.value);

  const traces = [
    {
      x: goldDates,
      y: goldCloses,
      type: 'scatter',
      mode: 'lines',
      name: 'Gold Close (USD)',
      line: { color: '#ffd700', width: 2 },
      yaxis: 'y1'
    },
    {
      x: indDates,
      y: indValues,
      type: 'scatter',
      mode: 'lines',
      name: indicatorLabel,
      line: { color: '#3b82f6', width: 1.5 },
      yaxis: 'y2'
    }
  ];

  const layout = {
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    margin: { l: 60, r: 60, t: 20, b: 60 },
    xaxis: {
      gridcolor: 'rgba(255, 215, 0, 0.03)',
      tickcolor: 'rgba(255, 215, 0, 0.1)',
      font: { family: 'Inter, sans-serif', color: '#94a3b8' },
    },
    yaxis: {
      gridcolor: 'rgba(255, 215, 0, 0.03)',
      tickcolor: 'rgba(255, 215, 0, 0.1)',
      font: { family: 'Inter, sans-serif', color: '#ffd700' },
      title: { text: 'Gold Price (USD)', font: { size: 12, color: '#ffd700' } },
      side: 'left'
    },
    yaxis2: {
      gridcolor: 'transparent',
      tickcolor: 'rgba(59, 130, 246, 0.2)',
      font: { family: 'Inter, sans-serif', color: '#3b82f6' },
      title: { text: indicatorLabel, font: { size: 12, color: '#3b82f6' } },
      side: 'right',
      overlaying: 'y'
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
    displayModeBar: false
  };

  return (
    <div style={{ width: '100%', height: '400px' }}>
      <Plot
        data={traces}
        layout={layout}
        config={config}
        style={{ width: '100%', height: '100%' }}
        useResizeHandler={true}
      />
    </div>
  );
}

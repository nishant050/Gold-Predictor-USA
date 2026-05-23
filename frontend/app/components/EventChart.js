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
      <div style={{ height: '250px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-card)', borderRadius: '12px' }}>
        <div className="spinner"></div>
      </div>
    )
  }
);


export default function EventChart({ priceHistory, eventDate, eventTitle }) {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  if (!isClient || !priceHistory || priceHistory.length === 0) {
    return (
      <div style={{ height: '250px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-card)', borderRadius: '12px' }}>
        <span style={{ color: 'var(--text-muted)' }}>No chart data available</span>
      </div>
    );
  }

  const xData = priceHistory.map(p => p.date);
  const yData = priceHistory.map(p => p.price);

  const traces = [
    {
      x: xData,
      y: yData,
      type: 'scatter',
      mode: 'lines+markers',
      name: 'Gold Close (USD)',
      line: { color: '#ffd700', width: 2 },
      marker: { color: '#ffd700', size: 4 },
    }
  ];

  const layout = {
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    margin: { l: 50, r: 20, t: 20, b: 40 },
    xaxis: {
      gridcolor: 'rgba(255, 215, 0, 0.03)',
      tickcolor: 'rgba(255, 215, 0, 0.1)',
      font: { family: 'Inter, sans-serif', color: '#94a3b8', size: 9 },
    },
    yaxis: {
      gridcolor: 'rgba(255, 215, 0, 0.03)',
      tickcolor: 'rgba(255, 215, 0, 0.1)',
      font: { family: 'Inter, sans-serif', color: '#94a3b8', size: 9 },
      tickformat: '$,.0f'
    },
    shapes: [
      {
        type: 'line',
        x0: eventDate,
        y0: 0,
        x1: eventDate,
        y1: 1,
        yref: 'paper',
        line: {
          color: '#ef4444',
          width: 2,
          dash: 'dashdot'
        }
      }
    ],
    annotations: [
      {
        x: eventDate,
        y: 1.05,
        yref: 'paper',
        text: 'Event Trigger',
        showarrow: false,
        font: {
          family: 'Inter, sans-serif',
          color: '#ef4444',
          size: 10,
          weight: 'bold'
        },
        bgcolor: '#0a0a0f',
        bordercolor: '#ef4444',
        borderwidth: 1,
        borderpad: 2
      }
    ],
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
    <div style={{ width: '100%', height: '250px' }}>
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

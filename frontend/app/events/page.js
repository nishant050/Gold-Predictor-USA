'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import EventChart from '../components/EventChart';
import { SkeletonEvents } from '../components/Skeleton';

export default function EventsPage() {
  const [timeline, setTimeline] = useState([]);
  const [impactAnalysis, setImpactAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Filtering and detail state
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedEventId, setSelectedEventId] = useState(null);
  const [eventDetail, setEventDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    async function loadEventsData() {
      setLoading(true);
      try {
        const tl = await api.getEventTimeline();
        setTimeline(tl);

        const analysis = await api.getEventImpactAnalysis();
        setImpactAnalysis(analysis?.by_type || null);

        setError(null);
      } catch (err) {
        console.error('Error loading events:', err);
        setError('Failed to load historical events timeline. Ensure the backend server is running.');
      } finally {
        setLoading(false);
      }
    }
    loadEventsData();
  }, []);

  // Fetch event details when an event is clicked
  const handleEventClick = async (id) => {
    setSelectedEventId(id);
    setDetailLoading(true);
    setIsModalOpen(true);
    try {
      const details = await api.getEventDetail(id);
      setEventDetail(details);
    } catch (err) {
      console.error('Error loading event detail:', err);
    } finally {
      setDetailLoading(false);
    }
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEventDetail(null);
    setSelectedEventId(null);
  };

  if (loading) {
    return <SkeletonEvents />;
  }

  if (error) {
    return (
      <div className="container" style={{ padding: '4rem 1.5rem' }}>
        <div className="card" style={{ border: '1px solid var(--bearish)', textAlign: 'center', maxWidth: '600px', margin: '0 auto' }}>
          <span style={{ fontSize: '3rem' }}>⚠️</span>
          <h2 style={{ margin: '1rem 0', color: 'var(--bearish)' }}>Failed to Load Timeline</h2>
          <p style={{ marginBottom: '2rem' }}>{error}</p>
          <button className="btn btn-primary" onClick={() => window.location.reload()}>Retry</button>
        </div>
      </div>
    );
  }

  // Category labels mapping
  const categoryLabels = {
    all: 'All Categories',
    war: 'Wars & Conflicts',
    monetary_policy: 'Monetary Policy',
    economic_crisis: 'Financial Crises',
    pandemic: 'Pandemics & Health',
    trade: 'Trade & Sanctions',
    inflation: 'Inflation Events',
    election: 'Elections & Politics',
    market_crash: 'Equity Crashes'
  };

  const categoryColors = {
    war: '#ef4444',
    monetary_policy: '#eab308',
    economic_crisis: '#f97316',
    pandemic: '#a855f7',
    trade: '#06b6d4',
    inflation: '#3b82f6',
    election: '#10b981',
    market_crash: '#ec4899'
  };

  // Filter timeline items
  const filteredTimeline = selectedCategory === 'all' 
    ? timeline 
    : timeline.filter(item => item.type === selectedCategory);

  return (
    <div className="container" style={{ padding: '2rem 1.5rem 4rem' }}>
      
      {/* Page Header */}
      <div style={{ marginBottom: '2.5rem' }}>
        <h1>Historical Event Timeline & Gold Correlation</h1>
        <p>Connecting the dots between 20 years of major world events and how they moved gold commodities.</p>
      </div>

      {/* Aggregate Impact Stats Panel */}
      <div className="card" style={{ marginBottom: '3.5rem', padding: '1.5rem' }}>
        <h3 style={{ marginBottom: '1.25rem' }}>Average Gold Price Impact by Event Type</h3>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
          Aggregated performance showing gold price reactions across 7-day, 30-day, and 90-day horizons post-trigger.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem' }}>
          {impactAnalysis && Object.entries(impactAnalysis).map(([cat, stats]) => (
            <div key={cat} className="card" style={{ padding: '1.25rem', borderTop: `4px solid ${categoryColors[cat] || '#64748b'}`, background: 'rgba(255,255,255,0.01)' }}>
              <h4 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '0.75rem', color: 'var(--text-primary)' }}>
                {categoryLabels[cat] || cat}
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.85rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Events Tracked:</span>
                  <span style={{ fontWeight: 600 }}>{stats.count}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Avg 7d return:</span>
                  <span style={{ color: stats.avg_7d_change >= 0 ? 'var(--bullish)' : 'var(--bearish)', fontWeight: 600 }}>
                    {stats.avg_7d_change >= 0 ? '+' : ''}{stats.avg_7d_change}%
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Avg 30d return:</span>
                  <span style={{ color: stats.avg_30d_change >= 0 ? 'var(--bullish)' : 'var(--bearish)', fontWeight: 600 }}>
                    {stats.avg_30d_change >= 0 ? '+' : ''}{stats.avg_30d_change}%
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Avg 90d return:</span>
                  <span style={{ color: stats.avg_90d_change >= 0 ? 'var(--bullish)' : 'var(--bearish)', fontWeight: 600 }}>
                    {stats.avg_90d_change >= 0 ? '+' : ''}{stats.avg_90d_change}%
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Main Timeline Section */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
          <h3>Chronological Timeline</h3>
          
          {/* Category Filter Buttons */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
            {Object.entries(categoryLabels).map(([key, label]) => (
              <button
                key={key}
                className={`btn ${selectedCategory === key ? 'btn-primary' : 'btn-secondary'}`}
                style={{ 
                  fontSize: '0.75rem', 
                  padding: '0.4rem 0.8rem', 
                  borderRadius: '6px',
                  border: selectedCategory === key ? 'none' : '1px solid var(--border-card)'
                }}
                onClick={() => setSelectedCategory(key)}
              >
                {key !== 'all' && (
                  <span style={{ 
                    display: 'inline-block', 
                    width: '8px', 
                    height: '8px', 
                    borderRadius: '50%', 
                    background: categoryColors[key], 
                    marginRight: '0.35rem' 
                  }}></span>
                )}
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* Timeline Visual Feed */}
        <div style={{ position: 'relative', paddingLeft: '2rem', borderLeft: '2px solid var(--border-card)', margin: '1rem 0 3rem 0.5rem' }}>
          
          {filteredTimeline.map((item) => {
            const up = item.gold_change_30d.startsWith('+');
            const flat = item.gold_change_30d === 'N/A';
            return (
              <div 
                key={item.id} 
                className="timeline-item card" 
                style={{ 
                  position: 'relative', 
                  marginBottom: '2rem', 
                  padding: '1.25rem 1.5rem', 
                  cursor: 'pointer',
                  transition: 'transform var(--transition-fast), box-shadow var(--transition-fast)',
                  borderLeft: `4px solid ${item.color}`
                }}
                onClick={() => handleEventClick(item.id)}
              >
                {/* Timeline node dot */}
                <div style={{ 
                  position: 'absolute', 
                  left: 'calc(-2rem - 7px)', 
                  top: '1.5rem', 
                  width: '12px', 
                  height: '12px', 
                  borderRadius: '50%', 
                  background: item.color,
                  boxShadow: `0 0 8px ${item.color}`
                }}></div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>{item.date}</span>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                      {categoryLabels[item.type]}
                    </span>
                  </div>
                  
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>30d Return:</span>
                    <span className={`badge ${flat ? 'badge-neutral' : up ? 'badge-bullish' : 'badge-bearish'}`} style={{ fontSize: '0.75rem' }}>
                      {item.gold_change_30d}
                    </span>
                  </div>
                </div>

                <h4 style={{ color: 'var(--text-primary)', fontSize: '1.1rem', fontWeight: 600 }}>{item.title}</h4>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.75rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  <span>Impact Level: {'★'.repeat(item.impact_level)}{'☆'.repeat(5 - item.impact_level)}</span>
                  <span style={{ textDecoration: 'underline' }}>View Impact Chart →</span>
                </div>
              </div>
            );
          })}

          {filteredTimeline.length === 0 && (
            <p style={{ color: 'var(--text-muted)', padding: '2rem 0' }}>No events matches this category in the database.</p>
          )}

        </div>
      </div>

      {/* Modal Detail Dialog */}
      {isModalOpen && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          background: 'rgba(0,0,0,0.8)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '1.5rem'
        }} onClick={closeModal}>
          
          <div style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-card)',
            borderRadius: '16px',
            maxWidth: '750px',
            width: '100%',
            maxHeight: '90vh',
            overflowY: 'auto',
            padding: '2rem',
            position: 'relative',
            boxShadow: 'var(--shadow-glass)'
          }} onClick={e => e.stopPropagation()}>
            
            {/* Close Button */}
            <button style={{
              position: 'absolute',
              top: '1rem',
              right: '1.5rem',
              background: 'none',
              border: 'none',
              color: 'var(--text-muted)',
              fontSize: '1.75rem',
              cursor: 'pointer',
              lineHeight: 1
            }} onClick={closeModal}>×</button>

            {detailLoading || !eventDetail ? (
              <div style={{ height: '350px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div className="spinner"></div>
              </div>
            ) : (
              <div>
                {/* Event Category Title */}
                <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <span style={{ 
                    display: 'inline-block', 
                    width: '10px', 
                    height: '10px', 
                    borderRadius: '50%', 
                    background: categoryColors[eventDetail.event.event_type] 
                  }}></span>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                    {categoryLabels[eventDetail.event.event_type]}
                  </span>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>•</span>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{eventDetail.event.event_date}</span>
                </div>

                <h2 style={{ color: 'var(--text-primary)', marginBottom: '1rem', fontSize: '1.6rem', fontWeight: 800 }}>
                  {eventDetail.event.title}
                </h2>

                <p style={{ lineHeight: 1.6, color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '0.95rem' }}>
                  {eventDetail.event.description}
                </p>

                {/* Return metrics boxes */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
                  <div style={{ background: 'rgba(255,255,255,0.02)', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-card)', textAlign: 'center' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>7-Day Return</span>
                    {eventDetail.event.gold_price_change_7d !== null ? (
                      <h3 style={{ margin: '0.25rem 0 0', color: eventDetail.event.gold_price_change_7d >= 0 ? 'var(--bullish)' : 'var(--bearish)', fontSize: '1.2rem', fontWeight: 700 }}>
                        {eventDetail.event.gold_price_change_7d >= 0 ? '+' : ''}{eventDetail.event.gold_price_change_7d}%
                      </h3>
                    ) : (
                      <h3 style={{ margin: '0.25rem 0 0', color: 'var(--text-muted)', fontSize: '1.2rem', fontWeight: 700 }}>N/A</h3>
                    )}
                  </div>
                  <div style={{ background: 'rgba(255,255,255,0.02)', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-card)', textAlign: 'center' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>30-Day Return</span>
                    {eventDetail.event.gold_price_change_30d !== null ? (
                      <h3 style={{ margin: '0.25rem 0 0', color: eventDetail.event.gold_price_change_30d >= 0 ? 'var(--bullish)' : 'var(--bearish)', fontSize: '1.2rem', fontWeight: 700 }}>
                        {eventDetail.event.gold_price_change_30d >= 0 ? '+' : ''}{eventDetail.event.gold_price_change_30d}%
                      </h3>
                    ) : (
                      <h3 style={{ margin: '0.25rem 0 0', color: 'var(--text-muted)', fontSize: '1.2rem', fontWeight: 700 }}>N/A</h3>
                    )}
                  </div>
                  <div style={{ background: 'rgba(255,255,255,0.02)', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-card)', textAlign: 'center' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>90-Day Return</span>
                    {eventDetail.event.gold_price_change_90d !== null ? (
                      <h3 style={{ margin: '0.25rem 0 0', color: eventDetail.event.gold_price_change_90d >= 0 ? 'var(--bullish)' : 'var(--bearish)', fontSize: '1.2rem', fontWeight: 700 }}>
                        {eventDetail.event.gold_price_change_90d >= 0 ? '+' : ''}{eventDetail.event.gold_price_change_90d}%
                      </h3>
                    ) : (
                      <h3 style={{ margin: '0.25rem 0 0', color: 'var(--text-muted)', fontSize: '1.2rem', fontWeight: 700 }}>N/A</h3>
                    )}
                  </div>
                </div>

                {/* 60-Day price chart centered on event */}
                <div>
                  <h4 style={{ marginBottom: '0.75rem', color: 'var(--text-primary)' }}>60-Day Price Window Surrounding Trigger</h4>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                    Plotted daily gold closes (INR) from 30 days before event trigger to 30 days after.
                  </p>
                  <EventChart 
                    priceHistory={eventDetail.price_history} 
                    eventDate={eventDetail.event.event_date} 
                    eventTitle={eventDetail.event.title} 
                  />
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid var(--border-card)', marginTop: '1.5rem', paddingTop: '1rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  <span>Impact rating: {'★'.repeat(eventDetail.event.impact_level)}{'☆'.repeat(5 - eventDetail.event.impact_level)} (level {eventDetail.event.impact_level}/5)</span>
                  <span>Source: {eventDetail.event.source}</span>
                </div>
              </div>
            )}

          </div>
        </div>
      )}

    </div>
  );
}

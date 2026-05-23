'use client';

export function SkeletonLine({ width = '100%', height = '1rem', marginBottom = '0.5rem', style = {} }) {
  return (
    <div 
      className="skeleton" 
      style={{ 
        width, 
        height, 
        marginBottom, 
        ...style 
      }} 
    />
  );
}

export function SkeletonCard({ height = '150px', style = {} }) {
  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', height, ...style }}>
      <SkeletonLine width="40%" height="0.8rem" marginBottom="1rem" />
      <SkeletonLine width="75%" height="2rem" marginBottom="1rem" />
      <SkeletonLine width="60%" height="1rem" marginBottom="0" />
    </div>
  );
}

export function SkeletonDashboard() {
  return (
    <div className="container" style={{ padding: '2rem 1.5rem 4rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '2rem' }}>
        <div>
          <SkeletonLine width="200px" height="2rem" marginBottom="0.5rem" />
          <SkeletonLine width="350px" height="1rem" marginBottom="0" />
        </div>
        <div style={{ width: '120px', height: '40px', borderRadius: '10px' }} className="skeleton" />
      </div>

      {/* Grid: 3 Metric Cards */}
      <div className="db-grid" style={{ marginBottom: '2rem' }}>
        <SkeletonCard style={{ gridColumn: 'span 4' }} />
        <SkeletonCard style={{ gridColumn: 'span 4' }} />
        <SkeletonCard style={{ gridColumn: 'span 4' }} />
      </div>

      {/* Big Chart Card */}
      <div className="card" style={{ marginBottom: '2.5rem', height: '480px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <div>
            <SkeletonLine width="250px" height="1.25rem" marginBottom="0.5rem" />
            <SkeletonLine width="400px" height="0.8rem" marginBottom="0" />
          </div>
          <div style={{ width: '200px', height: '35px', borderRadius: '10px' }} className="skeleton" />
        </div>
        <div style={{ height: '350px', borderRadius: '12px' }} className="skeleton" />
      </div>

      {/* Indicators and News */}
      <div className="db-grid">
        <div className="col-8" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <SkeletonLine width="200px" height="1.5rem" marginBottom="0.5rem" />
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
            <div className="card" style={{ padding: '1.25rem' }}>
              <SkeletonLine width="50%" height="0.75rem" marginBottom="0.75rem" />
              <SkeletonLine width="80%" height="1.5rem" marginBottom="0" />
            </div>
            <div className="card" style={{ padding: '1.25rem' }}>
              <SkeletonLine width="50%" height="0.75rem" marginBottom="0.75rem" />
              <SkeletonLine width="80%" height="1.5rem" marginBottom="0" />
            </div>
            <div className="card" style={{ padding: '1.25rem' }}>
              <SkeletonLine width="50%" height="0.75rem" marginBottom="0.75rem" />
              <SkeletonLine width="80%" height="1.5rem" marginBottom="0" />
            </div>
          </div>
        </div>
        <div className="col-4" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <SkeletonLine width="180px" height="1.5rem" marginBottom="0.5rem" />
          <div className="card" style={{ padding: '1.25rem', height: '220px', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <SkeletonLine width="30%" height="0.6rem" marginBottom="0.4rem" />
              <SkeletonLine width="90%" height="0.8rem" marginBottom="0" />
            </div>
            <div>
              <SkeletonLine width="25%" height="0.6rem" marginBottom="0.4rem" />
              <SkeletonLine width="95%" height="0.8rem" marginBottom="0" />
            </div>
            <div>
              <SkeletonLine width="40%" height="0.6rem" marginBottom="0.4rem" />
              <SkeletonLine width="85%" height="0.8rem" marginBottom="0" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function SkeletonPredictions() {
  return (
    <div className="container" style={{ padding: '2rem 1.5rem 4rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '2rem' }}>
        <div>
          <SkeletonLine width="220px" height="2rem" marginBottom="0.5rem" />
          <SkeletonLine width="380px" height="1rem" marginBottom="0" />
        </div>
      </div>
      <div className="db-grid" style={{ marginBottom: '2rem' }}>
        <SkeletonCard style={{ gridColumn: 'span 3' }} />
        <SkeletonCard style={{ gridColumn: 'span 3' }} />
        <SkeletonCard style={{ gridColumn: 'span 3' }} />
        <SkeletonCard style={{ gridColumn: 'span 3' }} />
      </div>
      <div className="card" style={{ marginBottom: '2.5rem', height: '480px' }}>
        <div style={{ height: '30px', marginBottom: '1.5rem' }} className="skeleton" />
        <div style={{ height: '350px', borderRadius: '12px' }} className="skeleton" />
      </div>
    </div>
  );
}

export function SkeletonEvents() {
  return (
    <div className="container" style={{ padding: '2rem 1.5rem 4rem' }}>
      <div style={{ marginBottom: '2rem' }}>
        <SkeletonLine width="250px" height="2rem" marginBottom="0.5rem" />
        <SkeletonLine width="450px" height="1rem" marginBottom="0" />
      </div>
      <div className="card" style={{ marginBottom: '2rem', height: '80px' }} />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1.5rem' }}>
        <div className="card" style={{ height: '220px' }}>
          <SkeletonLine width="20%" height="0.7rem" marginBottom="1rem" />
          <SkeletonLine width="80%" height="1.2rem" marginBottom="0.5rem" />
          <SkeletonLine width="95%" height="0.8rem" marginBottom="1.5rem" />
          <SkeletonLine width="40%" height="0.8rem" marginBottom="0" />
        </div>
        <div className="card" style={{ height: '220px' }}>
          <SkeletonLine width="20%" height="0.7rem" marginBottom="1rem" />
          <SkeletonLine width="80%" height="1.2rem" marginBottom="0.5rem" />
          <SkeletonLine width="95%" height="0.8rem" marginBottom="1.5rem" />
          <SkeletonLine width="40%" height="0.8rem" marginBottom="0" />
        </div>
        <div className="card" style={{ height: '220px' }}>
          <SkeletonLine width="20%" height="0.7rem" marginBottom="1rem" />
          <SkeletonLine width="80%" height="1.2rem" marginBottom="0.5rem" />
          <SkeletonLine width="95%" height="0.8rem" marginBottom="1.5rem" />
          <SkeletonLine width="40%" height="0.8rem" marginBottom="0" />
        </div>
      </div>
    </div>
  );
}

export function SkeletonAnalysis() {
  return (
    <div className="container" style={{ padding: '2rem 1.5rem 4rem' }}>
      <div style={{ marginBottom: '2rem' }}>
        <SkeletonLine width="260px" height="2rem" marginBottom="0.5rem" />
        <SkeletonLine width="400px" height="1rem" marginBottom="0" />
      </div>
      <div className="db-grid" style={{ marginBottom: '2rem' }}>
        <div className="card col-4" style={{ height: '350px' }}>
          <SkeletonLine width="60%" height="1.25rem" marginBottom="1rem" />
          <SkeletonLine width="100%" height="0.8rem" marginBottom="0.5rem" />
          <SkeletonLine width="100%" height="0.8rem" marginBottom="0.5rem" />
          <SkeletonLine width="80%" height="0.8rem" marginBottom="1.5rem" />
          <SkeletonLine width="90%" height="1.5rem" marginBottom="0.75rem" />
          <SkeletonLine width="90%" height="1.5rem" marginBottom="0" />
        </div>
        <div className="card col-8" style={{ height: '350px' }}>
          <div style={{ height: '30px', marginBottom: '1.5rem' }} className="skeleton" />
          <div style={{ height: '250px', borderRadius: '12px' }} className="skeleton" />
        </div>
      </div>
    </div>
  );
}

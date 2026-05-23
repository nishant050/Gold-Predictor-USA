'use client';

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="footer">
      <div className="container footer-inner">
        <div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            &copy; {currentYear} GoldSight Inc. All rights reserved. Historical market correlations & analogy engine.
          </p>
        </div>
        <div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Data sources: Yahoo Finance & FRED. Predictions are educational and do not constitute financial advice.
          </p>
        </div>
      </div>
    </footer>
  );
}

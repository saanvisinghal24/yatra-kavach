import React, { useState } from 'react';
import { 
  ShieldCheck, 
  AlertTriangle, 
  AlertOctagon, 
  Compass, 
  Sun, 
  Moon, 
  Mountain,
  Clock
} from 'lucide-react';

export const TokenPreview: React.FC = () => {
  const [isDark, setIsDark] = useState(false);

  return (
    <div className={isDark ? 'theme-control-dark' : ''} style={{ minHeight: '100vh', background: 'var(--paper)', color: 'var(--ink)' }}>
      {/* Top Survey Header with subtle contour effect */}
      <header className="contour-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div className="meta-label">YATRA KAVACH • DESIGN REFERENCE</div>
          <h1 style={{ marginTop: 'var(--space-1)' }}>Yatra Kavach • यात्रा कवच</h1>
        </div>
        <button 
          onClick={() => setIsDark(!isDark)} 
          style={{ minHeight: 'var(--tap-min)', minWidth: 'var(--tap-min)' }}
          aria-label="Toggle dark control-room theme"
        >
          {isDark ? <Sun size={18} /> : <Moon size={18} />}
          <span style={{ marginLeft: 'var(--space-2)' }}>{isDark ? 'Day Paper' : 'Control Dark'}</span>
        </button>
      </header>

      <main style={{ maxWidth: '880px', margin: '0 auto', padding: 'var(--space-6) var(--space-4)' }}>
        
        {/* Sprint 0 Scaffold Notice */}
        <section className="trail-card" style={{ marginBottom: 'var(--space-6)' }}>
          <div className="meta-label">SYSTEM NOTICE • SPRINT 0 FOUNDATION</div>
          <h2 style={{ margin: 'var(--space-2) 0' }}>Design System & Tokens Verification</h2>
          <p style={{ color: 'var(--ink-2)', marginBottom: 'var(--space-4)' }}>
            This board renders the locked visual foundation for Yatra Kavach: authentic Survey of India cartographic aesthetics,
            high-contrast sunlight readability, zero SaaS gradients or emoji, and strict severity accessibility.
          </p>
          <div className="indicative-notice">
            Indicative Data Notice: All trail metrics, GPS coordinates, and altitudes are unverified draft seeds pending administrative sign-off.
          </div>
        </section>

        {/* Trail Board Notice Sample */}
        <section className="trail-card-secondary" style={{ marginBottom: 'var(--space-6)' }}>
          <div className="meta-label">TRAIL NOTICE • MANIMAHESH ROUTE</div>
          <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginTop: 'var(--space-2)' }}>
            <h3 style={{ fontSize: '1.4rem' }}>Next: Dhancho (धंचो)</h3>
            <span className="numeral" style={{ fontSize: '1.1rem', fontWeight: 600 }}>3,000 m</span>
          </div>
          <p style={{ marginTop: 'var(--space-2)', fontSize: '1.05rem' }}>
            Usual time <span className="numeral">2 h 10 m – 2 h 50 m</span>. Cross by <span className="numeral">15:00</span>.
          </p>
          <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-4)', flexWrap: 'wrap' }}>
            <div className="severity-badge severity-ok">
              <ShieldCheck size={14} /> Normal Pace
            </div>
            <div className="severity-badge severity-watch">
              <AlertTriangle size={14} /> Cutoff approaching
            </div>
            <div className="severity-badge severity-urgent">
              <AlertOctagon size={14} /> Severe Weather Warning
            </div>
          </div>
        </section>

        {/* Color Palette Grid */}
        <section style={{ marginBottom: 'var(--space-6)' }}>
          <div className="meta-label" style={{ marginBottom: 'var(--space-3)' }}>DESIGN TOKENS PALETTE</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: 'var(--space-3)' }}>
            {[
              { name: '--paper', color: 'var(--paper)', text: 'var(--ink)' },
              { name: '--paper-2', color: 'var(--paper-2)', text: 'var(--ink)' },
              { name: '--line', color: 'var(--line)', text: 'var(--ink)' },
              { name: '--ink', color: 'var(--ink)', text: 'var(--paper)' },
              { name: '--ink-2', color: 'var(--ink-2)', text: '#FFFFFF' },
              { name: '--deodar', color: 'var(--deodar)', text: '#FFFFFF' },
              { name: '--deodar-dark', color: 'var(--deodar-dark)', text: '#FFFFFF' },
              { name: '--accent', color: 'var(--accent)', text: '#FFFFFF' },
              { name: '--ok', color: 'var(--ok)', text: '#FFFFFF' },
              { name: '--watch', color: 'var(--watch)', text: '#FFFFFF' },
              { name: '--urgent', color: 'var(--urgent)', text: '#FFFFFF' },
            ].map((token) => (
              <div 
                key={token.name} 
                style={{ 
                  background: token.color, 
                  color: token.text, 
                  padding: 'var(--space-3)', 
                  borderRadius: 'var(--radius)', 
                  border: 'var(--border-hairline)',
                  minHeight: '72px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'flex-end'
                }}
              >
                <span className="numeral" style={{ fontSize: '0.75rem', fontWeight: 600 }}>{token.name}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Typography & Numerals Comparison */}
        <section className="trail-card" style={{ marginBottom: 'var(--space-6)' }}>
          <div className="meta-label">TYPOGRAPHY HIERARCHY & SCRIPTS</div>
          <div style={{ marginTop: 'var(--space-3)' }}>
            <div style={{ marginBottom: 'var(--space-3)' }}>
              <span className="meta-label">DISPLAY SERIF (FRAUNCES):</span>
              <div style={{ fontFamily: 'var(--font-serif)', fontSize: '1.35rem', marginTop: 'var(--space-1)' }}>
                Manimahesh, Kinner Kailash & Shrikhand Mahadev Expeditions
              </div>
            </div>

            <div style={{ marginBottom: 'var(--space-3)' }}>
              <span className="meta-label">HINDI DEVANAGARI (NOTO SANS DEVANAGARI):</span>
              <div lang="hi" style={{ fontSize: '1.2rem', marginTop: 'var(--space-1)' }}>
                मणिमहेश • किन्नर कैलाश • श्रीखंड महादेव यात्रा सुरक्षा कवच
              </div>
            </div>

            <div style={{ marginBottom: 'var(--space-3)' }}>
              <span className="meta-label">TABULAR MONO NUMERALS (IBM PLEX MONO):</span>
              <div className="numeral" style={{ fontSize: '1.25rem', marginTop: 'var(--space-1)' }}>
                Elev: 4,080 m | GPS: 32.3982° N, 76.6434° E | Clock: 14:45:30 IST | Count: 04/04
              </div>
            </div>
          </div>
        </section>

        {/* Interactive Button Scale (>= 48px Target) */}
        <section className="trail-card">
          <div className="meta-label">INTERACTIVE TAP TARGETS (≥ 48PX MINIMUM)</div>
          <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-3)', flexWrap: 'wrap' }}>
            <button className="btn-primary" onClick={() => window.location.href = '/register'}>
              <Compass size={18} /> Register Pilgrim Group
            </button>
            <button className="btn-accent" onClick={() => window.location.href = '/register'}>
              <Mountain size={18} /> Begin Trail Scan
            </button>
            <button onClick={() => window.location.href = '/register'}>
              <Clock size={18} /> View Checkpoint Times
            </button>
          </div>
        </section>

      </main>
    </div>
  );
};

import {useText} from '../../lib/i18n/useText';
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ShieldCheck, EyeOff } from 'lucide-react';

export const FamilyLink: React.FC = () => {
  const tr=useText();
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    const load = () => fetch(`/api/v1/share/${token}`).then(res=>{if(!res.ok)throw new Error();return res.json();}).then(d=>{setData(d);setLoading(false);}).catch(()=>{setData(null);setLoading(false);});
    load();const timer=setInterval(load,2000);return()=>clearInterval(timer);
  }, [token]);

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', background: 'var(--paper)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="meta-label">{tr("CONNECTING TO YATRA KAVACH SURVEY RELAY...")}</div>
      </div>
    );
  }

  if (!data) return <main className="page"><h1>{tr("Family link unavailable")}</h1><p>{tr("Check your connection or request a fresh family link.")}</p></main>;
  return (
    <div style={{ minHeight: '100vh', background: 'var(--paper)', padding: 'var(--space-4)' }}>
      <div style={{ maxWidth: '480px', margin: '0 auto' }}>
        
        {/* Header */}
        <div className="contour-header" style={{ marginBottom: 'var(--space-4)', borderRadius: 'var(--radius)' }}>
          <div className="meta-label">{tr("YATRA KAVACH · FAMILY VIEW")}</div>
          <h1 style={{ fontSize: '1.4rem', marginTop: 'var(--space-1)' }}>{tr("Pilgrim Safety Status")}</h1>
        </div>

        {/* Status Card */}
        <div className="trail-card" style={{ marginBottom: 'var(--space-4)', border: '2px solid var(--deodar)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="meta-label">{tr("EXPEDITION PARTY")}</span>
            <span className="severity-badge severity-ok">
              <ShieldCheck size={14} /> {data.status}
            </span>
          </div>

          <div style={{ borderTop: 'var(--border-hairline)', paddingTop: 'var(--space-3)' }}>
            <div className="meta-label">{tr("LAST RECORDED CHECKPOINT:")}</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--deodar)', marginTop: '2px' }}>
              {data.last_checkpoint}
            </div>
            <div className="numeral" style={{ fontSize: '0.85rem', color: 'var(--ink-2)', marginTop: '2px' }}>
              {tr("Timestamp:")} {data.last_seen_time}
            </div>
          </div>

          <div style={{ borderTop: 'var(--border-hairline)', paddingTop: 'var(--space-3)', marginTop: 'var(--space-3)' }}>
            <div className="meta-label">{tr("ESTIMATED SEGMENT TIMELINE:")}</div>
            <div className="numeral" style={{ fontSize: '1rem', fontWeight: 600, marginTop: '2px' }}>
              {data.eta_range}
            </div>
          </div>
        </div>

        {/* Privacy Minimal Notice */}
        <div className="trail-card-secondary" style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
          <EyeOff size={22} style={{ color: 'var(--ink-2)', flexShrink: 0 }} />
          <div style={{ fontSize: '0.82rem', color: 'var(--ink-2)', lineHeight: '1.4' }}>
            {data.advisory_note}
          </div>
        </div>

        <button onClick={() => navigate('/')} style={{ width: '100%' }}>
          {tr("Return to Trail Guide")}
        </button>

      </div>
    </div>
  );
};

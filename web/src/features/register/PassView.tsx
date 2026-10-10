import {useText} from '../../lib/i18n/useText';
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import QRCode from 'qrcode';
import { ShieldCheck, Mountain, ArrowRight } from 'lucide-react';
import {post} from '../../lib/api';
import { db, LocalGroup } from '../../lib/db';

export const PassView: React.FC = () => {
  const tr=useText();
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();
  const [qrUrl, setQrUrl] = useState<string>('');
  const [group, setGroup] = useState<LocalGroup | null>(null);
  const [qrError,setQrError]=useState('');
  const [share,setShare]=useState('');
  const [advisory, setAdvisory] = useState<string | null>(null);

  useEffect(() => {
    if (!code) return;

    // Generate QR Data URL
    const passPayload = `${location.origin}/pass/${code}?token=YK1:${code}`;
    QRCode.toDataURL(passPayload, {
      width: 280,
      margin: 2,
      color: {
        dark: '#1B2620',
        light: '#F3EFE6'
      }
    }).then(setQrUrl).catch(() => setQrError('QR could not render. Reload this page or use the pass code.'));

    // Retrieve from Dexie
    db.groups.get(code).then(stored => {
      if (stored) {
        setGroup(stored);
      }
    }).catch(() => undefined);

    // Check backend status if online
    fetch(`/api/v1/groups/${code}`)
      .then(res => res.json())
      .then(data => {
        if (data.code) setGroup(old => old || ({code:data.code,leaderName:data.leader_name,size:data.size} as LocalGroup));
        if (data.open_advice && data.open_advice.length > 0) {
          setAdvisory(data.open_advice[0].message_en);
        }
      })
      .catch(() => {
        // Offline is fine
      });
  }, [code]);

  return (
    <div style={{ minHeight: '100vh', background: 'var(--paper)', padding: 'var(--space-4)' }}>
      <div style={{ maxWidth: '440px', margin: '0 auto', textAlign: 'center' }}>
        
        {/* Pass Header */}
        <div className="meta-label" style={{ marginBottom: 'var(--space-1)' }}>{tr("HIMACHAL PRADESH • PILGRIM DIGITAL PASS")}</div>
        <h2>{tr("Yatra Kavach Pass")}</h2>

        <button onClick={async()=>{try{const data=await post(`/share/generate/${code}`);setShare(location.origin+data.share_url);}catch(e){setAdvisory((e as Error).message);}}}>Create family link / परिवार लिंक</button>{share&&<p><a href={share}>{share}</a></p>}
        {/* Physical Trail Pass Card */}
        <div 
          className="trail-card" 
          style={{ 
            marginTop: 'var(--space-4)', 
            padding: 'var(--space-6) var(--space-4)',
            border: '2px solid var(--ink)',
            background: 'var(--paper)'
          }}
        >
          <div className="meta-label">{tr("DEMO PASS CODE")}</div>
          <div className="numeral" style={{ fontSize: '2.4rem', fontWeight: 700, letterSpacing: '0.1em', margin: 'var(--space-2) 0' }}>
            {code}
          </div>

          {/* QR Code Canvas */}
          {qrUrl ? (
            <div style={{ display: 'inline-block', padding: 'var(--space-2)', border: '1px solid var(--line)', background: '#FFFFFF', borderRadius: 'var(--radius)' }}>
              <img src={qrUrl} alt={`Pass QR for group ${code}`} style={{ display: 'block', width: '220px', height: '220px' }} />
            </div>
          ) : (
            <div style={{ height: '220px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {qrError || tr("Generating QR...")}
            </div>
          )}

          {qrUrl&&<div className="pass-actions"><a className="btn" href={qrUrl} download={`Yatra-Pass-${code}.png`}>Download QR</a><button onClick={()=>window.print()}>Print pass</button></div>}
          <div style={{ marginTop: 'var(--space-4)', textAlign: 'left', borderTop: 'var(--border-hairline)', paddingTop: 'var(--space-3)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
              <span className="meta-label">{tr("LEADER:")}</span>
              <span style={{ fontWeight: 600 }}>{group?.leaderName || 'Details not loaded'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
              <span className="meta-label">{tr("PARTY SIZE:")}</span>
              <span className="numeral" style={{ fontWeight: 600 }}>{group?.size || '—'} {tr("Person(s)")}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span className="meta-label">{tr("ROUTE:")}</span>
              <span style={{ fontSize: '0.9rem', color: 'var(--ink-2)' }}>{tr("Manimahesh Dal Lake")}</span>
            </div>
          </div>
        </div>

        {/* Advisory alert if R10 triggered */}
        {advisory && (
          <div className="trail-card-secondary" style={{ marginTop: 'var(--space-4)', textAlign: 'left', borderLeft: '4px solid var(--watch)' }}>
            <div className="meta-label" style={{ color: 'var(--watch)' }}>{tr("ITINERARY ADVISORY (R10)")}</div>
            <p style={{ fontSize: '0.88rem', marginTop: 'var(--space-1)' }}>{advisory}</p>
          </div>
        )}

        {/* Offline Badge */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 'var(--space-2)', marginTop: 'var(--space-4)', color: 'var(--ok)' }}>
          <ShieldCheck size={18} />
          <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>{tr("Pass saved locally. Verify downloaded resources before going offline.")}</span>
        </div>

        <button onClick={()=>navigate("/demo/offline-check")}>Download & verify offline / ऑफलाइन तैयारी</button>{/* Action Buttons */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)', marginTop: 'var(--space-6)' }}>
          <button 
            className="btn-primary" 
            onClick={() => navigate(`/trail/${code}`)}
            style={{ width: '100%' }}
          >
            <Mountain size={18} /> {tr("Proceed to Live Trail View")} <ArrowRight size={16} />
          </button>
          
          <button 
            onClick={() => navigate('/')}
            style={{ width: '100%' }}
          >
            {tr("Return to Trail Guide")}
          </button>
        </div>

      </div>
    </div>
  );
};

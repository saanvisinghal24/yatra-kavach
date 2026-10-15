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
  const [tripStatus, setTripStatus] = useState('');
  const [statusVerified, setStatusVerified] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [cancelMessage, setCancelMessage] = useState('');
  const [online, setOnline] = useState(navigator.onLine);
  useEffect(() => {
    const update = () => setOnline(navigator.onLine);
    window.addEventListener('online', update); window.addEventListener('offline', update);
    return () => { window.removeEventListener('online', update); window.removeEventListener('offline', update); };
  }, []);
  const cancelTrip = async () => {
    if (!code || !group?.cancellationToken || !navigator.onLine || cancelling) return;
    if (!window.confirm('Cancel the ENTIRE group trip? Confirm that nobody has started travelling or recorded an offline checkpoint scan. This cannot be undone.')) return;
    const reason = window.prompt('Reason (optional, maximum 300 characters):', '');
    if (reason === null) return;
    if (reason.length > 300) { setCancelMessage('Keep the reason within 300 characters.'); return; }
    setCancelling(true); setCancelMessage('');
    try {
      const pending = (await db.checkins.where('groupCode').equals(code).toArray()).some(event => event.status === 'pending');
      if (pending) throw new Error('Pending checkpoint scans exist. Sync them before requesting cancellation.');
      await post(`/groups/${code}/cancel`, {cancellation_token: group.cancellationToken, reason});
      setTripStatus('cancelled'); setCancelMessage('Your group trip has been cancelled.');
      await db.groups.update(code, {tripStatus: 'cancelled'}).catch(() => undefined);
    } catch (error) { setCancelMessage((error as Error).message); }
    finally { setCancelling(false); }
  };
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
        if (stored.tripStatus === "cancelled") setTripStatus("cancelled");
      }
    }).catch(() => undefined);

    const awaitStatusCache = (status: string) => { void db.groups.update(code, {tripStatus: status}).catch(() => undefined); };

    // Check backend status if online
    fetch(`/api/v1/groups/${code}`)
      .then(res => { if (!res.ok) throw new Error("Could not verify pass status"); return res.json(); })
      .then(data => {
        if (data.code) { setTripStatus(data.status); setStatusVerified(true); awaitStatusCache(data.status); }
        if (data.code) setGroup(old => old || ({code:data.code,leaderName:data.leader_name,size:data.size} as LocalGroup));
        if (data.open_advice && data.open_advice.length > 0) {
          setAdvisory(data.open_advice[0].message_en);
        }
      })
      .catch(() => {
        // Offline is fine
      });
  }, [code, online]);

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
          {tripStatus === "cancelled" ? <h3 role="status">TRIP CANCELLED</h3> : qrUrl ? (
            <div style={{ display: 'inline-block', padding: 'var(--space-2)', border: '1px solid var(--line)', background: '#FFFFFF', borderRadius: 'var(--radius)' }}>
              <img src={qrUrl} alt={`Pass QR for group ${code}`} style={{ display: 'block', width: '220px', height: '220px' }} />
            </div>
          ) : (
            <div style={{ height: '220px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {qrError || tr("Generating QR...")}
            </div>
          )}

          {qrUrl && tripStatus !== "cancelled" && <div className="pass-actions"><a className="btn" href={qrUrl} download={`Yatra-Pass-${code}.png`}>Download QR</a><button onClick={()=>window.print()}>Print pass</button></div>}
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

        <section className="trail-card-secondary" style={{marginTop: 'var(--space-4)'}} aria-label="Trip cancellation">
          <h3>Cancel group trip</h3>
          {tripStatus === 'cancelled' ? <p>This pass is cancelled and cannot be checked in.</p> : <>
            <p>Only before the journey starts. Cancels every member on this pass.</p>
            {!group?.cancellationToken && <p>Available only for new passes on the browser used to register. Existing passes cannot be cancelled here.</p>}
            {!online && <p>Connect to the internet to cancel.</p>}
            {statusVerified && tripStatus !== 'planned' && <p>Journey already started. Contact checkpoint staff for return assistance.</p>}
            <button type="button" disabled={!online || !statusVerified || tripStatus !== 'planned' || !group?.cancellationToken || cancelling} onClick={cancelTrip}>
              {cancelling ? 'Cancelling...' : 'Cancel Entire Group Trip'}
            </button>
          </>}
          {cancelMessage && <p role="status">{cancelMessage}</p>}
        </section>

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
            disabled={tripStatus === "cancelled"}
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

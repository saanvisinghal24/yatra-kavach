import {useText} from '../../lib/i18n/useText';
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AlertOctagon, PhoneCall, MessageSquare, ArrowLeft } from 'lucide-react';
import {queueAction} from '../../lib/sync';
import { db, LocalCheckin } from '../../lib/db';

export const SOSScreen: React.FC = () => {
  const tr=useText();
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();

  const [lastCheckin, setLastCheckin] = useState<LocalCheckin | null>(null);
  const [coords, setCoords] = useState<{ lat: number; lon: number } | null>(null);
  const [alarmSent, setAlarmSent] = useState(false);
  const [queued,setQueued]=useState(false);
  const [busy,setBusy]=useState(false);
  const [acknowledged,setAcknowledged]=useState(false);
  const [reason,setReason]=useState('');
  useEffect(()=>{if(!code)return;const refresh=async()=>{try{const response=await fetch('/api/v1/groups/'+code);if(!response.ok)return;const group=await response.json();if(group.incidents?.some((i:any)=>i.type==='emergency_sos'))setAlarmSent(true);setAcknowledged(group.open_advice?.some((f:any)=>f.rule_id==='SOS'&&f.status==='acked')||false);}catch{/* Offline state stays local. */}};void refresh();const timer=setInterval(refresh,10000);return()=>clearInterval(timer);},[code]);

  const [controlRoomPhone,setControlRoomPhone]=useState('');
  const [sendError,setSendError]=useState('');
  useEffect(()=>{fetch('/api/v1/config').then(r=>r.json()).then(c=>setControlRoomPhone(c.sms_number)).catch(()=>{});},[]);

  useEffect(() => {
    if (!code) return;
    db.checkins.where('groupCode').equals(code).sortBy('clientTs').then(list => {
      if (list.length > 0) {
        setLastCheckin(list[list.length - 1]);
      }
    });

    // Try reading device GPS if permitted (optional fallback)
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => setCoords({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
        () => undefined
      );
    }
  }, [code]);

  // Construct SMS payload with group code, last station, coordinates
  const lastLocationStr = lastCheckin ? `${lastCheckin.checkpointName} (CP ${lastCheckin.checkpointId})` : 'No recorded checkpoint / कोई चेकपॉइंट रिकॉर्ड नहीं';
  const gpsStr = coords ? ` GPS: ${coords.lat.toFixed(4)}, ${coords.lon.toFixed(4)}` : '';
  const smsBodyText = encodeURIComponent(`YATRA KAVACH SOS! Group: ${code || 'PILGRIM'}. Last Checkpoint: ${lastLocationStr}.${gpsStr}. Urgent assistance needed!`);

  // Compatible for both Android and iOS
  const smsHrefAndroid = `sms:${controlRoomPhone}?body=${smsBodyText}`;
  const smsHrefIOS = `sms:${controlRoomPhone}&body=${smsBodyText}`;

  const handleTriggerLocalAlarm = async () => {
    if(busy||queued)return;
    setBusy(true);setSendError('');
    try {
      const delivered = await queueAction('/sos',{group_code:code,checkpoint_id:lastCheckin?.checkpointId,lat:coords?.lat,lon:coords?.lon,reason:reason||'Distress via pilgrim app'});
      setQueued(true);setAlarmSent(delivered);
      if(!delivered)setSendError('Saved locally; upload pending. No confirmed remote receipt. / फोन पर सहेजा; अपलोड बाकी है।');
    } catch {
      setSendError('Could not save on this device. Try a call if cellular coverage is available. / फोन पर सहेजना विफल; नेटवर्क हो तो कॉल करें।');
    } finally {setBusy(false);}

  };

  return (
    <div style={{ minHeight: '100vh', background: 'var(--paper)', padding: 'var(--space-4)' }}>
      <div style={{ maxWidth: '480px', margin: '0 auto' }}>
        
<p role="alert">{sendError}</p>{/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-4)' }}>
          <button onClick={() => navigate(`/trail/${code}`)}>
            <ArrowLeft size={16} /> {tr("Back to Trail")}
          </button>
          <div className="meta-label" style={{ color: 'var(--urgent)' }}>{tr("DISTRESS EMERGENCY")}</div>
        </div>

        {/* SOS Warning Banner */}
        <div 
          className="trail-card" 
          style={{ 
            background: 'rgba(180, 35, 24, 0.08)', 
            border: '2px solid var(--urgent)',
            marginBottom: 'var(--space-4)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <AlertOctagon size={24} style={{ color: 'var(--urgent)' }} />
            <div>
              <h2 style={{ fontSize: '1.25rem', color: 'var(--urgent)' }}>{tr("Mountain Rescue & SOS")}</h2>
              <div className="meta-label">{tr("CALLS AND SMS REQUIRE CELLULAR COVERAGE")}</div>
            </div>
          </div>
          <p style={{ marginTop: 'var(--space-2)', fontSize: '0.9rem', lineHeight: '1.4' }}>
            {tr("If mobile data fails but cellular coverage remains, try a call or SMS.\n            Use direct emergency dial or the pre-filled offline SMS below.")}
          </p>
        </div>

        {/* Direct Emergency Telephone Hotlines (>= 48px) */}
        <section style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)', marginBottom: 'var(--space-4)' }}>
          <a 
            href="tel:112" 
            className="btn" 
            style={{ 
              background: 'var(--urgent)', 
              color: '#FFFFFF', 
              borderColor: '#8B180F', 
              fontSize: '1.1rem',
              fontWeight: 700,
              minHeight: '56px'
            }}
          >
            <PhoneCall size={20} /> {tr("DIAL 112 (Emergency assistance)")}
          </a>

          <a 
            href="tel:108" 
            className="btn btn-primary" 
            style={{ 
              fontSize: '1.1rem', 
              fontWeight: 700,
              minHeight: '56px'
            }}
          >
            <PhoneCall size={20} /> {tr("DIAL 108 (Ambulance)")}
          </a>
        </section>

        {/* SMS Fallback Protocol */}
        <section className="trail-card" style={{ marginBottom: 'var(--space-4)' }}>
          <div className="meta-label">{tr("SMS CELLULAR FALLBACK")}</div>
          <p style={{ fontSize: '0.85rem', color: 'var(--ink-2)', margin: 'var(--space-1) 0 var(--space-3)' }}>
            {tr("Taps your phone's native SMS composer with your verified Group Code and last checkpoint pre-filled:")}
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-2)' }}>
            <a 
              href={controlRoomPhone?smsHrefAndroid:undefined} aria-disabled={!controlRoomPhone} 
              className="btn btn-accent" 
              style={{ fontSize: '0.85rem', textDecoration: 'none', minHeight: '48px' }}
            >
              <MessageSquare size={16} /> {tr("SMS (Android)")}
            </a>
            <a 
              href={controlRoomPhone?smsHrefIOS:undefined} aria-disabled={!controlRoomPhone} 
              className="btn btn-accent" 
              style={{ fontSize: '0.85rem', textDecoration: 'none', minHeight: '48px' }}
            >
              <MessageSquare size={16} /> {tr("SMS (iPhone)")}
            </a>
          </div>

          <div style={{ background: 'var(--paper-2)', padding: 'var(--space-2)', borderRadius: 'var(--radius)', marginTop: 'var(--space-3)', fontSize: '0.78rem' }}>
            <span className="meta-label">{tr("PRE-COMPOSED TEXT:")}</span>
            <div style={{ fontFamily: 'var(--font-mono)', marginTop: '2px', wordBreak: 'break-all' }}>
              {tr("YATRA KAVACH SOS! Group:")} {code}{tr(". Last Checkpoint:")} {lastLocationStr}.{gpsStr}
            </div>
          </div>
        </section>

        {!controlRoomPhone&&<p>Monitored SMS contact is not configured. / निगरानी वाला एसएमएस संपर्क निर्धारित नहीं है।</p>}
        <label>Concern / समस्या<textarea maxLength={1000} value={reason} onChange={e=>setReason(e.target.value)}/></label>
        <p role="status">{acknowledged?'Staff acknowledged / कर्मचारी ने स्वीकार किया':alarmSent?'Server received; staff acknowledgment pending / सर्वर प्राप्ति; कर्मचारी पुष्टि बाकी':queued?'Local only; upload pending / केवल फोन पर; अपलोड बाकी':'No SOS recorded here / यहाँ एसओएस दर्ज नहीं है'}</p>
        <p>No rescue dispatch is confirmed by this screen. / इस स्क्रीन से बचाव दल रवाना होने की पुष्टि नहीं होती।</p>
        {/* Digital Distress Alarm Trigger */}
        <button 
          onClick={handleTriggerLocalAlarm}
          disabled={busy||queued||alarmSent}
          style={{ width: '100%', minHeight: '48px' }}
        >
          {busy?'Saving… / सहेज रहे हैं':queued||alarmSent?'SOS recorded / एसओएस दर्ज':'Save SOS request / एसओएस अनुरोध सहेजें'}
        </button>

      </div>
    </div>
  );
};

import {Advisories} from './Advisories';
import {ControlMap} from '../control/ControlMap';
import {RoutePack} from './RoutePack';
import {Link} from 'react-router-dom';
import {useText} from '../../lib/i18n/useText';
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Camera, 
  RefreshCw, 
  AlertOctagon, 
  HeartPulse
} from 'lucide-react';
import {api} from '../../lib/api';
import {profile} from '../../lib/trail';
import {useTranslation} from '../../lib/i18n/LanguageContext';
import { AltitudeProfile } from './AltitudeProfile';
import { db, LocalGroup, LocalCheckin } from '../../lib/db';
import { syncPendingCheckins, getPendingCheckinCount, getLastSyncTime } from '../../lib/sync';

export const TrailView: React.FC = () => {
  const tr=useText();
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();

  const {language}=useTranslation();
  const [remote,setRemote]=useState<any>(null);
  const [weather,setWeather]=useState<any>(null);
  const [checkpoints,setCheckpoints]=useState<any[]>([]);
  const [group, setGroup] = useState<LocalGroup | null>(null);
  const [recentCheckin, setRecentCheckin] = useState<LocalCheckin | null>(null);
  const [pendingCount, setPendingCount] = useState<number>(0);
  const [syncing, setSyncing] = useState<boolean>(false);
  const [lastSync, setLastSync] = useState<string | null>(null);
  const [currentCpId, setCurrentCpId] = useState<number>(1);

  const refreshState = async () => {
    if (!code) return;
    const g = await db.groups.get(code);
    if (g) {
      setGroup(g);
      try {const y=await api<any[]>('/yatras');const r=y.flatMap(v=>v.routes).find(r=>r.id===g.routeId);if(r){setCheckpoints(r.checkpoints);if(!navigator.onLine){const last=await db.checkins.where('groupCode').equals(code).sortBy('clientTs');const latest=last.filter(e=>e.status!=='invalid').at(-1);const cp=r.checkpoints.find((c:any)=>c.id===latest?.checkpointId)||r.checkpoints[0];if(cp)setWeather(await api('/weather/'+cp.id));}}}catch{}
    }
    try {const data=await api(`/groups/${code}`);setRemote(data);if(data.last_checkpoint)setCurrentCpId(data.last_checkpoint.id);if(data.next_checkpoint)setWeather(await api(`/weather/${data.next_checkpoint.id}`));}catch{}

    const checkins = await db.checkins.where('groupCode').equals(code).sortBy('clientTs');
    if (checkins.length > 0) {
      const last = checkins[checkins.length - 1];
      setRecentCheckin(last);
      if(last.status!=='invalid')setCurrentCpId(last.checkpointId);
    }

    const pending = await getPendingCheckinCount();
    setPendingCount(pending);
    setLastSync(getLastSyncTime());
  };

  useEffect(() => {
    refreshState();
    const interval = setInterval(refreshState, 4000);
    return () => clearInterval(interval);
  }, [code]);

  const handleManualSync = async () => {
    setSyncing(true);
    try {
      await syncPendingCheckins();
      await refreshState();
    } finally {
      setSyncing(false);
    }
  };

  const localCurrent=checkpoints.find(c=>c.id===currentCpId);
  const next = remote?.next_checkpoint || checkpoints.find(c=>c.seq>(localCurrent?.seq||0));
  const nextCheckpoint = next ? {name:language==='hi'?next.name_hi:next.name_en,alt:`${next.altitude_m} m`,time:remote?.eta_range||`${next.min_minutes}–${next.max_minutes} min`,cutoff:next.cutoff_time||'—',dist:`${next.dist_from_prev_km||0} km`} : {name: remote?'No next checkpoint':'Connect to load trail status',alt:'—',time:'—',cutoff:'—',dist:'—'};


  return (
    <div style={{ minHeight: '100vh', background: 'var(--paper)', padding: 'var(--space-3)' }}>
      <div style={{ maxWidth: '640px', margin: '0 auto' }}>
        
        {/* Top Operational Status Ribbon */}
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-3)' }}>
          <div>
            <div className="meta-label">{tr("TRAIL MONITOR • GROUP")} {code}</div>
            <h2 style={{ fontSize: '1.25rem', marginTop: '2px' }}>{tr("Manimahesh Route")}</h2>
          </div>
          
          {/* Mandatory Visible Sync Button for iOS & Offline Status */}
          <button 
            onClick={handleManualSync}
            disabled={syncing}
            style={{ 
              fontSize: '0.8rem', 
              padding: '0 var(--space-3)', 
              minHeight: '40px',
              background: pendingCount > 0 ? 'var(--paper-2)' : 'var(--paper)',
              borderColor: pendingCount > 0 ? 'var(--watch)' : 'var(--line)'
            }}
            aria-label="Sync pending checkins with server"
          >
            <RefreshCw size={14} className={syncing ? 'animate-spin' : ''} />
            <span>{syncing ? 'Syncing...' : pendingCount > 0 ? `Sync now (${pendingCount})` : 'Check sync'}</span>
          </button>
        </header>

        <Link to="/demo/offline-check">Download & verify offline / ऑफलाइन तैयारी</Link><ControlMap checkpoints={checkpoints}/><RoutePack/>{group&&<Advisories routeId={group.routeId}/>}{remote?.journey_counts&&<section className="trail-card"><h2>Member journey status / सदस्य यात्रा स्थिति</h2><dl>{Object.entries(remote.journey_counts).map(([state,count])=><React.Fragment key={state}><dt>{({planned:'Planned / नियोजित',outbound:'Outbound / ऊपर की ओर',returning:'Returning / वापस',exit_pending:'Exit pending confirmation / निकास पुष्टि बाकी',exited:'Exited / निकास पूर्ण'} as Record<string,string>)[state]||state}</dt><dd>{String(count)}</dd></React.Fragment>)}</dl><p>Final exit needs member-by-member reconciliation at Hadsar. / हड़सर में हर सदस्य का निकास मिलान आवश्यक है।</p></section>}{/* Hand-drawn SVG Altitude Profile */}
        <section style={{ marginBottom: 'var(--space-4)' }}>
          <div className="meta-label" style={{ marginBottom: 'var(--space-2)' }}>{tr("ELEVATION PROFILE & POSITION")}</div>
          {checkpoints.length>0&&<AltitudeProfile checkpoints={profile(checkpoints)} currentCheckpointId={currentCpId} />}
        </section>

        {remote?.open_advice?.map((a:any,i:number)=><p className={`trail-card severity-${a.severity}`} key={i}>{a.rule_id} · {a.severity} · {a.status}: {language==='hi'?a.message_hi:a.message_en}</p>)}
        {remote?.incidents?.map((i:any)=><p key={i.id}>{tr("Incident #")}{i.id}: {i.status} {i.assigned_to}</p>)}
        {remote?.checkpoint_statuses?.filter((c:any)=>c.status!=='open').map((c:any)=><p role="status" key={c.id}>{c.name_en}: {c.status}</p>)}
        <p>Weather / मौसम: {weather?.status==='active'&&(!weather.valid_until||Date.parse(weather.valid_until)>Date.now())?`${weather.temp_current_c} °C · gusts ${weather.wind_gusts_max_kmh} km/h`:'Unavailable or stale / उपलब्ध नहीं'} </p>
        <p>Forecast retrieval / प्राप्ति: {weather?.retrieved_at||weather?.fetched_at||"unavailable"} · Valid until / मान्य: {weather?.valid_until||"unavailable"} · Provider issue time / जारी समय: {weather?.issue_time||"not supplied"}</p><p>Forecast: Open-Meteo. Cached information is not a safe-to-proceed guarantee. / पुराना पूर्वानुमान सुरक्षा की गारंटी नहीं है।</p>{/* Next Checkpoint Trail Notice */}
        <section className="trail-card" style={{ marginBottom: 'var(--space-4)', borderLeft: '4px solid var(--deodar)' }}>
          <div className="meta-label">{tr("NEXT TRAIL CHECKPOINT")}</div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginTop: 'var(--space-1)' }}>
            <h3 style={{ fontSize: '1.3rem' }}>{tr("Next:")} {nextCheckpoint.name}</h3>
            <span className="numeral" style={{ fontWeight: 700, fontSize: '1.1rem' }}>{nextCheckpoint.alt}</span>
          </div>
          <p style={{ marginTop: 'var(--space-2)', fontSize: '1rem', color: 'var(--ink)' }}>
            {tr("Usual time")} <span className="numeral" style={{ fontWeight: 600 }}>{nextCheckpoint.time}</span>.
          </p>
          {next?.cutoff_time && <p>Configured daily cutoff (IST): <strong>{next.cutoff_time}</strong> · {new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Kolkata',hour:'2-digit',minute:'2-digit',hour12:false}).format(new Date()) >= next.cutoff_time.slice(0,5) ? 'Cutoff reached — check with checkpoint staff.' : 'Before cutoff — confirm current conditions with staff.'} This is a preset schedule, not a live arrival estimate.</p>}
          <div style={{ display: 'flex', gap: 'var(--space-2)', marginTop: 'var(--space-3)', fontSize: '0.82rem', color: 'var(--ink-2)' }}>
            <span>{tr("Segment Distance:")} <strong className="numeral">{nextCheckpoint.dist}</strong></span>
            <span>•</span>
            <span>{tr("Party Count:")} <strong className="numeral">{recentCheckin?.headcount || group?.size || 1} / {group?.size || 1}</strong></span>
          </div>
        </section>

        {/* Trail Actions Grid (>= 48px Tap Targets) */}
        <section style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)', marginBottom: 'var(--space-4)' }}>
          <button 
            className="btn-accent" 
            onClick={() => navigate(`/scan/${code}`)}
            style={{ minHeight: '52px' }}
          >
            <Camera size={18} /> {tr("Scan Checkpoint")}
          </button>
          
          <button 
            onClick={() => navigate(`/health/${code}`)}
            style={{ minHeight: '52px' }}
          >
            <HeartPulse size={18} /> {tr("Health Check")}
          </button>
        </section>

        {/* SOS Emergency Button */}
        <button 
          onClick={() => navigate(`/sos/${code}`)}
          style={{ 
            width: '100%', 
            minHeight: '52px', 
            background: 'var(--urgent)', 
            color: '#FFFFFF',
            borderColor: '#8B180F',
            fontWeight: 700,
            marginBottom: 'var(--space-4)'
          }}
        >
          <AlertOctagon size={18} /> {tr("Emergency SOS / SMS Fallback")}
        </button>

        {/* Recent Scan Audit & Queue Info */}
        <section className="trail-card-secondary">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="meta-label">{tr("DEVICE QUEUE AUDIT")}</span>
            <span className="numeral" style={{ fontSize: '0.78rem', color: 'var(--ink-2)' }}>
              {tr("Last sync:")} {lastSync || 'Not yet synced'}
            </span>
          </div>
          <div style={{ marginTop: 'var(--space-2)', fontSize: '0.88rem' }}>
            {recentCheckin ? (
              <div>
                {tr("Last scanned:")} <strong>{recentCheckin.checkpointName}</strong> {tr("at")}{' '}
                <span className="numeral">{new Date(recentCheckin.clientTs).toLocaleTimeString()}</span>{' '}
                ({recentCheckin.status === 'synced' ? 'Synced to Control Room' : recentCheckin.status==='invalid'?recentCheckin.invalidReason:'Queued Locally'})
              </div>
            ) : (
              <div>{tr("No physical checkpoints scanned yet. Scan board at trailhead.")}</div>
            )}
          </div>
          <div className="indicative-notice" style={{ marginTop: 'var(--space-2)' }}>
            {tr("Indicative data. Not verified by district authorities.")}
          </div>
        </section>

      </div>
    </div>
  );
};

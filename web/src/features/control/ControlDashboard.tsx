import React, { useEffect, useState, Suspense, lazy } from 'react';
import {api} from '../../lib/api';
import {profile} from '../../lib/trail';
import {OperationsLinks} from '../../routes/Operations';
import { Link, useNavigate } from 'react-router-dom';
import { 
  ShieldAlert, 
  Users, 
  MapPin, 
  AlertTriangle, 
  AlertOctagon, 
  Check, 
  RefreshCw,
  FileSpreadsheet,
  ArrowLeft
} from 'lucide-react';
import { AltitudeProfile } from '../trail/AltitudeProfile';

const ControlMap = lazy(() => import('./ControlMap'));

interface SummaryKPIs {
  active_groups: number;
  total_pilgrims_on_trail: number;
  urgent_alerts: number;
  watch_alerts: number;
  overdue_groups: number;
  control_status: string;
}

interface RiskFlagItem {
  id: number;
  group_id: number;
  checkpoint_id?: number;
  rule_id: string;
  severity: 'info' | 'watch' | 'urgent';
  message_en: string;
  status: 'open' | 'acked' | 'resolved';
  created_at: string;
}

interface GroupSummary {
  id: number;
  code: string;
  leader_name: string;
  leader_phone: string;
  size: number;
  current_headcount: number;
  status: string;
  last_checkpoint_id?: number;
  last_scan_time?: string;
  open_flags: any[];
}

export const ControlDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [kpis, setKpis] = useState<SummaryKPIs>({active_groups:0,total_pilgrims_on_trail:0,urgent_alerts:0,watch_alerts:0,overdue_groups:0,control_status:'LOADING'});
  const [flags, setFlags] = useState<RiskFlagItem[]>([]);
  const [error,setError] = useState('');
  const [checkpoints,setCheckpoints]=useState<any[]>([]);
  const [groups, setGroups] = useState<GroupSummary[]>([]);
  const [selectedTab, setSelectedTab] = useState<'alerts' | 'map' | 'groups'>('alerts');

  // Fetch initial summary & groups
  const loadData = async () => {
    try {
      const [y,summary,alerts,registered]=await Promise.all([api('/yatras/manimahesh'),api('/dashboard/summary'),api('/flags?status=open'),api('/dashboard/groups')]);
      setCheckpoints(y.routes[0].checkpoints);setKpis(summary);setFlags(alerts);setGroups(registered);setError('');
    } catch {
      setError('Control-room update unavailable; displayed data may be stale.');
    }
  };

  useEffect(() => {
    loadData();

    // Setup Server-Sent Events (SSE) live stream
    let eventSource: EventSource | null = null;
    try {
      eventSource = new EventSource('/api/v1/dashboard/stream');
      eventSource.addEventListener('flag_update', (e) => {
        const payload = JSON.parse(e.data);
        setFlags(prev => prev.filter(f => f.id !== payload.flag_id || payload.status === 'open'));
      });
      eventSource.addEventListener('refresh', loadData);
      eventSource.addEventListener('checkin', () => {
        loadData();
      });
    } catch (err) {

    }

    const interval = setInterval(loadData, 5000);
    return () => {
      clearInterval(interval);
      if (eventSource) eventSource.close();
    };
  }, []);

  const handleFlagAction = async (flagId: number, action: 'ack' | 'resolve') => {
    try {
      const result = await fetch(`/api/v1/flags/${flagId}?action=${action}`, {
        method: 'PATCH'
      });
      if (!result.ok) throw new Error('Update failed');
      await loadData();
    } catch {
      setError('Update failed. Please retry.');
    }
  };

  const groupDots = groups.filter(g=>g.last_checkpoint_id).map(g=>({id:String(g.id),checkpointId:g.last_checkpoint_id!,label:g.code}));

  return (
    <div className="theme-control-dark" style={{ minHeight: '100vh', background: 'var(--paper)', color: 'var(--ink)' }}>
      {/* Control Room Top Header */}
      <header className="contour-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          <button onClick={() => navigate('/')} style={{ minHeight: '40px', padding: '0 var(--space-3)' }}>
            <ArrowLeft size={16} /> Public View
          </button>
          <div>
            <div className="meta-label">CHAMBA · DEMO CONTROL ROOM</div>
            <h1 style={{ fontSize: '1.4rem', marginTop: '2px' }}>Trail Operations & Incident Desk</h1>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
          <a 
            href="/api/v1/admin/report.csv" 
            target="_blank" 
            rel="noreferrer"
            className="btn"
            style={{ fontSize: '0.82rem', minHeight: '40px' }}
          >
            <FileSpreadsheet size={16} /> Export Audit CSV
          </a>
          <button onClick={loadData} style={{ minHeight: '40px', padding: '0 var(--space-3)' }}>
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </header>

      <main style={{ maxWidth: '1100px', margin: '0 auto', padding: 'var(--space-4)' }}>
        
        <OperationsLinks/><p role="alert">{error}</p>{/* KPI Strip */}
        <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: 'var(--space-3)', marginBottom: 'var(--space-4)' }}>
          <div className="trail-card">
            <div className="meta-label">ACTIVE EXPEDITIONS</div>
            <div className="numeral" style={{ fontSize: '2rem', fontWeight: 700, marginTop: 'var(--space-1)' }}>
              {kpis.active_groups}
            </div>
          </div>

          <div className="trail-card">
            <div className="meta-label">PILGRIMS ON TRAIL</div>
            <div className="numeral" style={{ fontSize: '2rem', fontWeight: 700, marginTop: 'var(--space-1)' }}>
              {kpis.total_pilgrims_on_trail}
            </div>
          </div>

          <div className="trail-card" style={{ borderLeft: '4px solid var(--urgent)' }}>
            <div className="meta-label" style={{ color: 'var(--urgent)' }}>CRITICAL ALERTS (R8/R2)</div>
            <div className="numeral" style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--urgent)', marginTop: 'var(--space-1)' }}>
              {kpis.urgent_alerts}
            </div>
          </div>

          <div className="trail-card" style={{ borderLeft: '4px solid var(--watch)' }}>
            <div className="meta-label" style={{ color: 'var(--watch)' }}>OVERDUE / SLOW GROUPS</div>
            <div className="numeral" style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--watch)', marginTop: 'var(--space-1)' }}>
              {kpis.overdue_groups}
            </div>
          </div>
        </section>

        {/* Live Elevation Profile with Group Dots */}
        <section className="trail-card" style={{ marginBottom: 'var(--space-4)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-2)' }}>
            <span className="meta-label">LIVE HIGH-ALTITUDE TRAIL RIBBON (DOTS = ACTIVE PILGRIM GROUPS)</span>
            <span className="numeral" style={{ fontSize: '0.8rem', color: 'var(--ink-2)' }}>
              Hadsar (2,100 m) ➔ Dal Lake (4,080 m)
            </span>
          </div>
          {checkpoints.length>0&&<AltitudeProfile checkpoints={profile(checkpoints)} currentCheckpointId={0} groupDots={groupDots} />}
        </section>

        {/* View Switcher Tabs */}
        <div style={{ display: 'flex', gap: 'var(--space-2)', marginBottom: 'var(--space-4)' }}>
          <button 
            onClick={() => setSelectedTab('alerts')}
            className={selectedTab === 'alerts' ? 'btn-primary' : ''}
            style={{ minHeight: '44px' }}
          >
            <ShieldAlert size={16} /> Alerts Inbox ({flags.length})
          </button>
          <button 
            onClick={() => setSelectedTab('map')}
            className={selectedTab === 'map' ? 'btn-primary' : ''}
            style={{ minHeight: '44px' }}
          >
            <MapPin size={16} /> Terrain Map (Survey)
          </button>
          <button 
            onClick={() => setSelectedTab('groups')}
            className={selectedTab === 'groups' ? 'btn-primary' : ''}
            style={{ minHeight: '44px' }}
          >
            <Users size={16} /> Groups Registry ({groups.length})
          </button>
        </div>

        {/* Tab 1: Alerts Inbox */}
        {selectedTab === 'alerts' && (
          <section style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            {flags.length === 0 ? (
              <div className="trail-card" style={{ textAlign: 'center', padding: 'var(--space-8)' }}>
                <Check size={32} style={{ color: 'var(--ok)', margin: '0 auto var(--space-2)' }} />
                <h3>All Clear: Zero Active Risk Flags</h3>
                <p style={{ color: 'var(--ink-2)', fontSize: '0.9rem', marginTop: 'var(--space-1)' }}>
                  Active sweeps running every 60s for overdue, missing, and headcount anomalies.
                </p>
              </div>
            ) : (
              flags.map(flag => (
                <div 
                  key={flag.id} 
                  className="trail-card" 
                  style={{ 
                    borderLeft: `4px solid ${flag.severity === 'urgent' ? 'var(--urgent)' : 'var(--watch)'}`,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 'var(--space-2)'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                      <span className={`severity-badge severity-${flag.severity}`}>
                        {flag.severity === 'urgent' ? <AlertOctagon size={13} /> : <AlertTriangle size={13} />}
                        {flag.rule_id} • {flag.severity.toUpperCase()}
                      </span>
                      <span className="numeral" style={{ fontSize: '0.8rem', color: 'var(--ink-2)' }}>
                        Group #{flag.group_id} • {new Date(flag.created_at).toLocaleTimeString()}
                      </span>
                    </div>

                    <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                      <button 
                        onClick={() => handleFlagAction(flag.id, 'ack')}
                        style={{ fontSize: '0.8rem', minHeight: '36px', padding: '0 var(--space-3)' }}
                      >
                        Acknowledge
                      </button>
                      <button 
                        onClick={() => handleFlagAction(flag.id, 'resolve')}
                        className="btn-primary"
                        style={{ fontSize: '0.8rem', minHeight: '36px', padding: '0 var(--space-3)' }}
                      >
                        Resolve & Clear
                      </button>
                    </div>
                  </div>

                  <p style={{ fontSize: '1rem', lineHeight: '1.4', marginTop: 'var(--space-1)' }}>
                    {flag.message_en}
                  </p>
                </div>
              ))
            )}
          </section>
        )}

        {/* Tab 2: Leaflet Terrain Map (Code Split) */}
        {selectedTab === 'map' && (
          <section className="trail-card">
            <div className="meta-label" style={{ marginBottom: 'var(--space-2)' }}>
              MANIMAHESH CHECKPOINT MAP
            </div>
            <Suspense fallback={<div style={{ height: '340px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>Loading Cartographic Layer...</div>}>
              <ControlMap checkpoints={checkpoints} groups={groups}/>
            </Suspense>
          </section>
        )}

        {/* Tab 3: Groups Registry */}
        {selectedTab === 'groups' && (
          <section className="trail-card" style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--line)' }}>
                  <th style={{ padding: 'var(--space-2)' }} className="meta-label">CODE</th>
                  <th style={{ padding: 'var(--space-2)' }} className="meta-label">LEADER</th>
                  <th style={{ padding: 'var(--space-2)' }} className="meta-label">HEADCOUNT</th>
                  <th style={{ padding: 'var(--space-2)' }} className="meta-label">STATUS</th>
                  <th style={{ padding: 'var(--space-2)' }} className="meta-label">PHONE</th>
                </tr>
              </thead>
              <tbody>
                {groups.length === 0 ? (
                  <tr>
                    <td colSpan={5} style={{ padding: 'var(--space-4)', textAlign: 'center', color: 'var(--ink-2)' }}>
                      No registered groups currently loaded.
                    </td>
                  </tr>
                ) : (
                  groups.map(g => (
                    <tr key={g.id} style={{ borderBottom: '1px solid var(--line)' }}>
                      <td style={{ padding: 'var(--space-2)' }} className="numeral"><Link to={`/control/groups/${g.id}`}>{g.code}</Link></td>
                      <td style={{ padding: 'var(--space-2)' }}>{g.leader_name}</td>
                      <td style={{ padding: 'var(--space-2)' }} className="numeral">{g.current_headcount} / {g.size}</td>
                      <td style={{ padding: 'var(--space-2)' }}>
                        <span className={`severity-badge severity-${g.open_flags.length > 0 ? 'watch' : 'ok'}`}>
                          {g.status}
                        </span>
                      </td>
                      <td style={{ padding: 'var(--space-2)' }} className="numeral">{g.leader_phone}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </section>
        )}

      </main>
    </div>
  );
};

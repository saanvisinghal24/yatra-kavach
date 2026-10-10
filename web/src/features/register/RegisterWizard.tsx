import {useText} from '../../lib/i18n/useText';
import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, ArrowRight, AlertTriangle } from 'lucide-react';
import { api } from '../../lib/api';
import { db } from '../../lib/db';

interface MemberItem {
  name: string;
  age_band: '<18' | '18-40' | '41-60' | '60+';
  note: string;
}

export const RegisterWizard: React.FC = () => {
  const tr=useText();
  const navigate = useNavigate();
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [advisories, setAdvisories] = useState<any[]>([]);

  // Form State
  const [yatras,setYatras]=useState<any[]>([]);
  const [yatraId,setYatraId] = useState<number>(1);
  useEffect(()=>{api<any[]>('/yatras').then(setYatras).catch(e=>setError(e.message));},[]);
  const [routeId,setRouteId] = useState<number>(1);
  const [plannedStart, setPlannedStart] = useState<string>(new Date(Date.now()+19800000).toISOString().slice(0,16));
  const [plannedReturn,setPlannedReturn]=useState('');
  const [plannedStops,setPlannedStops] = useState<{checkpoint_id:number;day:number}[]>([]);
  const selectedRoute=yatras.flatMap(y=>y.routes).find(r=>r.id===routeId);


  const [leaderName, setLeaderName] = useState('');
  const [leaderPhone, setLeaderPhone] = useState('');
  const [emergencyName, setEmergencyName] = useState('');
  const [emergencyPhone, setEmergencyPhone] = useState('');
  const [groupSize, setGroupSize] = useState<number>(2);

  const [members, setMembers] = useState<MemberItem[]>([
    { name: '', age_band: '18-40', note: '' },
    { name: '', age_band: '18-40', note: '' }
  ]);

  const handleSizeChange = (val: number) => {
    const size = Math.max(1, Math.min(20, val));
    setGroupSize(size);
    const updated = [...members];
    while (updated.length < size) {
      updated.push({ name: '', age_band: '18-40', note: '' });
    }
    setMembers(updated.slice(0, size));
  };

  const handleMemberChange = (idx: number, field: keyof MemberItem, val: string) => {
    const updated = [...members];
    updated[idx] = { ...updated[idx], [field]: val };
    setMembers(updated);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    const payload = {
      yatra_id: yatraId,
      route_id: routeId,
      leader_name: leaderName,
      leader_phone: leaderPhone,
      emergency_name: emergencyName,
      emergency_phone: emergencyPhone,
      size: groupSize,
      planned_start: new Date(plannedStart+':00+05:30').toISOString(),
      planned_return: plannedReturn?new Date(plannedReturn+':00+05:30').toISOString():null,
      consent: true,
      members: members.map(m => ({
        name: m.name.trim(),
        age_band: m.age_band,
        note: m.note ? m.note.trim() : null
      })),
      planned_stops: plannedStops
    };

    try {
      const res = await fetch('/api/v1/groups', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      let code = '';
      let passToken = '';
      if (res.ok) {
        const data = await res.json();
        code = data.code;
        passToken = data.pass_token;
        if (data.advisories && data.advisories.length > 0) {
          setAdvisories(data.advisories);
        }
      } else { const body=await res.json().catch(()=>({})); throw new Error(Array.isArray(body.detail)?body.detail.map((v:any)=>`${v.loc.slice(1).join(' ')}: ${v.msg}`).join('; '):body.detail||'Registration failed. Check the server terminal.'); }

      // Persist in local IndexedDB for airplane mode access
      await db.groups.put({
        code,
        yatraId,
        routeId,
        routeName: selectedRoute?.name||'Selected trail',
        leaderName,
        leaderPhone,
        emergencyName,
        emergencyPhone,
        size: groupSize,
        passToken,
        createdAt: new Date().toISOString(),
        synced: res.ok
      }).catch(()=>undefined);

      navigate(`/pass/${code}`);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: 'var(--paper)', padding: 'var(--space-4)' }}>
      <div style={{ maxWidth: '540px', margin: '0 auto' }}>
<p role="alert">{error}</p>{/* Navigation / Step Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-4)' }}>
          <button 
            type="button" 
            onClick={() => step > 1 ? setStep((step - 1) as any) : navigate('/')}
            style={{ padding: '0 var(--space-3)' }}
          >
            <ArrowLeft size={16} /> {tr("Back")}
          </button>
          <div className="meta-label">{tr("STEP")} {step} {tr("OF 3 • REGISTRATION")}</div>
        </div>

        <div className="trail-card" style={{ marginBottom: 'var(--space-4)' }}>
          <div className="meta-label">{selectedRoute?.name || tr("MANIMAHESH PILGRIMAGE • 2026 SEASON")}</div>
          <h2 style={{ marginTop: 'var(--space-1)' }}>{tr("Pilgrim Group Registration")}</h2>
          <p style={{ color: 'var(--ink-2)', fontSize: '0.9rem', marginTop: 'var(--space-1)' }}>
            {tr("Register online once. Your saved pass and checkpoint scans work offline.")}
          </p>
        </div>

        <label>Yatra / यात्रा<select value={yatraId} onChange={e=>{const id=+e.target.value;setYatraId(id);setRouteId(yatras.find(y=>y.id===id).routes[0].id);setPlannedStops([]);}}>{yatras.filter(y=>y.slug==='manimahesh' && y.status==='active').map(y=><option key={y.id} value={y.id}>{y.name_en} / {y.name_hi}</option>)}</select></label>
        <label>First sleeping stop / पहला रात्रि पड़ाव<select value={plannedStops[1]?.checkpoint_id||''} onChange={e=>{setPlannedStops(e.target.value?[{checkpoint_id:selectedRoute.checkpoints[0].id,day:1},{checkpoint_id:+e.target.value,day:2}]:[]);}}><option value="">{tr("No planned overnight stop")}</option>{selectedRoute?.checkpoints?.slice(1).map((cp:any)=><option key={cp.id} value={cp.id}>{cp.name_en} · {cp.altitude_m} m</option>)}</select></label>
        {advisories.length > 0 && (
          <div className="trail-card-secondary" style={{ marginBottom: 'var(--space-4)', borderLeft: '4px solid var(--watch)' }}>
            <div className="meta-label" style={{ color: 'var(--watch)', display: 'flex', alignItems: 'center', gap: 'var(--space-1)' }}>
              <AlertTriangle size={14} /> {tr("ITINERARY ADVISORY")}
            </div>
            {advisories.map((adv, idx) => (
              <p key={idx} style={{ fontSize: '0.88rem', marginTop: 'var(--space-1)' }}>{adv.message_en}</p>
            ))}
          </div>
        )}

        <form onSubmit={step === 3 ? handleSubmit : (e) => { e.preventDefault(); setStep((step + 1) as any); }}>
          {step === 1 && (
            <div className="trail-card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              <div>
                <label className="meta-label" htmlFor="trail-select">{tr("SELECTED ROUTE")}</label>
                <input 
                  id="trail-select" 
                  type="text" 
                  readOnly 
                  value={selectedRoute?.name||"Loading route…"}
                  style={{ background: 'var(--paper-2)', marginTop: 'var(--space-1)' }} 
                />
              </div>

              <div>
                <label className="meta-label" htmlFor="start-date">{tr("PLANNED START DATE & TIME")}</label>
                <input 
                  id="start-date" 
                  type="datetime-local" 
                  required
                  value={plannedStart}
                  onChange={(e) => setPlannedStart(e.target.value)}
                  style={{ marginTop: 'var(--space-1)' }}
                />
              </div>

              <div>
                <label>Planned return to Hadsar (IST) / हड़सर वापसी का समय<input type="datetime-local" required min={plannedStart} value={plannedReturn} onChange={e=>setPlannedReturn(e.target.value)}/></label><label className="meta-label" htmlFor="group-size">{tr("NUMBER OF PILGRIMS IN GROUP")}</label>
                <input 
                  id="group-size" 
                  type="number" 
                  min="1" 
                  max="20"
                  required
                  value={groupSize}
                  onChange={(e) => handleSizeChange(parseInt(e.target.value) || 1)}
                  style={{ marginTop: 'var(--space-1)' }}
                />
              </div>

              <div className="indicative-notice" style={{ marginTop: 'var(--space-2)' }}>
                {tr("Indicative Schedule: R10 advisory engine verifies itinerary against acute altitude sickness thresholds.")}
              </div>

              <label><input type="checkbox" required/> {tr("I consent to processing for trail safety and accept the")} <Link to="/privacy">{tr("Privacy notice")}</Link> {tr("and")} <Link to="/terms">{tr("Terms")}</Link>. Simulated details only. / सुरक्षा के लिए डेटा उपयोग की सहमति है; केवल काल्पनिक विवरण।</label>
          <button type="submit" className="btn-primary" style={{ marginTop: 'var(--space-2)' }}>
                {tr("Next: Leader & Emergency")} <ArrowRight size={16} />
              </button>
            </div>
          )}

          {step === 2 && (
            <div className="trail-card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              <div>
                <label className="meta-label" htmlFor="leader-name">{tr("GROUP LEADER FULL NAME")}</label>
                <input 
                  id="leader-name" 
                  type="text" 
                  required
                  placeholder="Group leader name"
                  value={leaderName}
                  onChange={(e) => setLeaderName(e.target.value)}
                  style={{ marginTop: 'var(--space-1)' }}
                />
              </div>

              <div>
                <label className="meta-label" htmlFor="leader-phone">{tr("LEADER MOBILE (WHATSAPP / SMS)")}</label>
                <input 
                  id="leader-phone" 
                  type="tel" 
                  required
                  placeholder="Phone number"
                  value={leaderPhone}
                  onChange={(e) => setLeaderPhone(e.target.value)}
                  style={{ marginTop: 'var(--space-1)' }}
                />
              </div>

              <div>
                <label className="meta-label" htmlFor="em-name">{tr("EMERGENCY CONTACT NAME (BASE / FAMILY)")}</label>
                <input 
                  id="em-name" 
                  type="text" 
                  required
                  placeholder="Emergency contact name"
                  value={emergencyName}
                  onChange={(e) => setEmergencyName(e.target.value)}
                  style={{ marginTop: 'var(--space-1)' }}
                />
              </div>

              <div>
                <label className="meta-label" htmlFor="em-phone">{tr("EMERGENCY CONTACT PHONE")}</label>
                <input 
                  id="em-phone" 
                  type="tel" 
                  required
                  placeholder="Emergency phone"
                  value={emergencyPhone}
                  onChange={(e) => setEmergencyPhone(e.target.value)}
                  style={{ marginTop: 'var(--space-1)' }}
                />
              </div>

              <button type="submit" className="btn-primary" style={{ marginTop: 'var(--space-2)' }}>
                {tr("Next: Member Details")} <ArrowRight size={16} />
              </button>
            </div>
          )}

          {step === 3 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              {members.map((m, idx) => (
                <div key={idx} className="trail-card">
                  <div className="meta-label">{tr("PILGRIM #")}{idx + 1} {idx === 0 ? '(LEADER)' : ''}</div>
                  <div style={{ marginTop: 'var(--space-2)' }}>
                    <input 
                      type="text" 
                      required
                      aria-label={`Member ${idx+1} name`} placeholder={`Pilgrim ${idx + 1} Name`}
                      value={m.name}
                      onChange={(e) => handleMemberChange(idx, 'name', e.target.value)}
                    />
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-2)', marginTop: 'var(--space-2)' }}>
                    <div>
                      <label className="meta-label">{tr("AGE BAND")}</label>
                      <select 
                        aria-label={`Member ${idx+1} age band`} value={m.age_band} 
                        onChange={(e) => handleMemberChange(idx, 'age_band', e.target.value as any)}
                        style={{ marginTop: 'var(--space-1)' }}
                      >
                        <option value="<18">{tr("&lt; 18 years")}</option>
                        <option value="18-40">{tr("18 – 40 years")}</option>
                        <option value="41-60">{tr("41 – 60 years")}</option>
                        <option value="60+">{tr("60+ years")}</option>
                      </select>
                    </div>
                    <div>
                      <label className="meta-label">{tr("MEDICAL NOTE (OPTIONAL)")}</label>
                      <input 
                        type="text" 
                        aria-label={`Member ${idx+1} optional note`} placeholder="Optional, consented note"
                        value={m.note}
                        onChange={(e) => handleMemberChange(idx, 'note', e.target.value)}
                        style={{ marginTop: 'var(--space-1)' }}
                      />
                    </div>
                  </div>
                </div>
              ))}

              <button type="submit" disabled={loading} className="btn-accent" style={{ marginTop: 'var(--space-2)' }}>
                {loading ? tr("Generating Pass...") : tr("Generate Offline QR Pass")}
              </button>
            </div>
          )}
        </form>
      </div>
    </div>
  );
};

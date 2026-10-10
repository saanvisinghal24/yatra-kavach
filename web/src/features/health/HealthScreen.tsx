import {useText} from '../../lib/i18n/useText';
import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {db} from '../../lib/db';
import {useTranslation} from '../../lib/i18n/LanguageContext';
import { ArrowLeft, PhoneCall } from 'lucide-react';

export const HealthScreen: React.FC = () => {
  const tr=useText();
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();
  const {language}=useTranslation();
  const [delivery,setDelivery]=useState('');

  // Lake Louise 4-item score (0-3 each)
  const [headache, setHeadache] = useState<number>(0);
  const [stomach, setStomach] = useState<number>(0);
  const [fatigue, setFatigue] = useState<number>(0);
  const [dizziness, setDizziness] = useState<number>(0);

  // Red flags
  const [redFlags, setRedFlags] = useState<{ [key: string]: boolean }>({
    confusion: false,
    ataxia: false,
    breathless_at_rest: false,
    wet_cough: false
  });

  const [result, setResult] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);

  const toggleRedFlag = (key: string) => {
    setRedFlags(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleEvaluate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    const activeRedFlags = Object.keys(redFlags).filter(k => redFlags[k]);
    const score = headache + stomach + fatigue + dizziness;

    const payload = {
      group_code: code,
      headache,
      stomach,
      fatigue,
      dizziness,
      red_flags: activeRedFlags
    };

    const eventId=crypto.randomUUID();
    await db.outbox.put({id:eventId,path:'/symptom-reports',payload,status:'pending'});
    try {
      const res = await fetch('/api/v1/symptom-reports', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Idempotency-Key':eventId },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const data = await res.json();
        setResult(data);
        await db.outbox.update(eventId,{status:'synced'});
        setLoading(false);setDelivery('Saved to control room / नियंत्रण कक्ष में सहेजा');
        return;
      }
    } catch {
      // Offline fallback calculation
    }

    setDelivery('Saved on this device; not delivered yet. Sync when online. / फोन पर सहेजा; ऑनलाइन होने पर सिंक करें।');
    // Local offline pure evaluation fallback
    const isSevere = activeRedFlags.length > 0 || score >= 10;
    const isModerate = score >= 6;
    setResult({
      score,
      advice_level: isSevere ? 'severe' : isModerate ? 'moderate' : score >= 3 ? 'mild' : 'normal',
      guidance_hi: isSevere?'गंभीर चेतावनी। आगे न चढ़ें। सहायता लें; 112 / 108 पर कॉल करें।':isModerate?'चढ़ाई रोकें। विश्राम करें और सहायता लें। 112 / 108 उपलब्ध है।':'विश्राम करें। लक्षण बने रहने पर आगे न चढ़ें।',
      guidance_en: isSevere
        ? 'CRITICAL: Severe altitude sickness signs. DO NOT ASCEND FURTHER. Begin descent to lower altitude immediately. Call 112 / 108.'
        : isModerate
        ? 'Moderate altitude symptoms. Halt ascent and rest at this station. Call 112 / 108 if condition worsens.'
        : score >= 3
        ? 'Mild symptoms. Walk slowly, hydrate, and do not gain more altitude today.'
        : 'Symptom scores are within normal limits. Maintain adequate hydration.',
      emergency_contact_needed: isSevere || isModerate,
      red_flags_detected: activeRedFlags
    });
    setLoading(false);
  };

  return (
    <div style={{ minHeight: '100vh', background: 'var(--paper)', padding: 'var(--space-4)' }}>
      <div style={{ maxWidth: '520px', margin: '0 auto' }}>
        
<p role="status">{delivery}</p>{/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-4)' }}>
          <button onClick={() => navigate(`/trail/${code}`)}>
            <ArrowLeft size={16} /> {tr("Back to Trail")}
          </button>
          <div className="meta-label">{tr("LAKE LOUISE AMS ADVISORY")}</div>
        </div>

        <div className="trail-card" style={{ marginBottom: 'var(--space-4)' }}>
          <div className="meta-label">{tr("GUIDANCE, NOT CLINICAL DIAGNOSIS")}</div>
          <h2 style={{ marginTop: 'var(--space-1)' }}>{tr("High-Altitude Health Check")}</h2>
          <p style={{ color: 'var(--ink-2)', fontSize: '0.88rem', marginTop: 'var(--space-1)' }}>
            {tr("Evaluates acute mountain sickness indicators. If anyone feels severe distress, halt ascent immediately.")}
          </p>
        </div>

        {!result ? (
          <form onSubmit={handleEvaluate} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            
            {/* Headache */}
            <div className="trail-card">
              <label className="meta-label">{tr("1. HEADACHE SEVERITY")}</label>
              <select aria-label="headache" value={headache} onChange={(e) => setHeadache(parseInt(e.target.value))} style={{ marginTop: 'var(--space-1)' }}>
                <option value={0}>{tr("0 — None (No headache)")}</option>
                <option value={1}>{tr("1 — Mild (Noticeable, does not affect activity)")}</option>
                <option value={2}>{tr("2 — Moderate (Throbbing, uncomfortable)")}</option>
                <option value={3}>{tr("3 — Severe (Incapacitating, severe pain)")}</option>
              </select>
            </div>

            {/* Gastrointestinal */}
            <div className="trail-card">
              <label className="meta-label">{tr("2. GASTROINTESTINAL / STOMACH")}</label>
              <select aria-label="stomach" value={stomach} onChange={(e) => setStomach(parseInt(e.target.value))} style={{ marginTop: 'var(--space-1)' }}>
                <option value={0}>{tr("0 — Normal appetite")}</option>
                <option value={1}>{tr("1 — Poor appetite or mild nausea")}</option>
                <option value={2}>{tr("2 — Moderate nausea or occasional vomiting")}</option>
                <option value={3}>{tr("3 — Severe nausea and frequent vomiting")}</option>
              </select>
            </div>

            {/* Fatigue */}
            <div className="trail-card">
              <label className="meta-label">{tr("3. FATIGUE / WEAKNESS")}</label>
              <select aria-label="fatigue" value={fatigue} onChange={(e) => setFatigue(parseInt(e.target.value))} style={{ marginTop: 'var(--space-1)' }}>
                <option value={0}>{tr("0 — Not tired")}</option>
                <option value={1}>{tr("1 — Mild fatigue, manageable")}</option>
                <option value={2}>{tr("2 — Moderate weakness, walking is slow")}</option>
                <option value={3}>{tr("3 — Severe exhaustion, cannot walk without help")}</option>
              </select>
            </div>

            {/* Dizziness */}
            <div className="trail-card">
              <label className="meta-label">{tr("4. DIZZINESS / LIGHTHEADEDNESS")}</label>
              <select aria-label="dizziness" value={dizziness} onChange={(e) => setDizziness(parseInt(e.target.value))} style={{ marginTop: 'var(--space-1)' }}>
                <option value={0}>{tr("0 — None")}</option>
                <option value={1}>{tr("1 — Mild")}</option>
                <option value={2}>{tr("2 — Moderate")}</option>
                <option value={3}>{tr("3 — Severe, unsteady standing")}</option>
              </select>
            </div>

            {/* Red Flags Section */}
            <div className="trail-card" style={{ borderLeft: '4px solid var(--urgent)' }}>
              <div className="meta-label" style={{ color: 'var(--urgent)' }}>{tr("CRITICAL RED FLAGS (HAPE / HACE)")}</div>
              <p style={{ fontSize: '0.82rem', color: 'var(--ink-2)', margin: 'var(--space-1) 0 var(--space-2)' }}>
                {tr("Check any condition observed in any group member right now:")}
              </p>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                {[
                  { key: 'confusion', label: 'Confusion, disorientation, or slurred speech' },
                  { key: 'ataxia', label: 'Loss of coordination (stumbling / cannot walk straight)' },
                  { key: 'breathless_at_rest', label: 'Severe breathlessness while resting or sitting' },
                  { key: 'wet_cough', label: 'Rattling chest sound or wet cough' }
                ].map(rf => (
                  <label key={rf.key} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', fontSize: '0.9rem', cursor: 'pointer' }}>
                    <input 
                      type="checkbox" 
                      checked={redFlags[rf.key]} 
                      onChange={() => toggleRedFlag(rf.key)} 
                      style={{ width: '20px', height: '20px', accentColor: 'var(--urgent)' }}
                    />
                    <span>{tr(rf.label)}</span>
                  </label>
                ))}
              </div>
            </div>

            <button type="submit" disabled={loading} className="btn-accent" style={{ marginTop: 'var(--space-2)' }}>
              {loading ? tr("Evaluating...") : tr("Evaluate Lake Louise Score")}
            </button>
          </form>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            
            {/* Advice Result Card */}
            <div 
              className="trail-card" 
              style={{ 
                borderLeft: `5px solid ${result.advice_level === 'severe' ? 'var(--urgent)' : result.advice_level === 'moderate' ? 'var(--watch)' : 'var(--ok)'}` 
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className={`severity-badge severity-${result.advice_level === 'severe' ? 'urgent' : result.advice_level === 'moderate' ? 'watch' : 'ok'}`}>
                  {result.advice_level.toUpperCase()} {tr("ADVISORY")}
                </span>
                <span className="numeral" style={{ fontWeight: 700 }}>{tr("Score:")} {result.score} / 12</span>
              </div>

              <h3 style={{ margin: 'var(--space-3) 0 var(--space-2)' }}>
                {result.advice_level === 'severe' ? 'Immediate Descent Required' : result.advice_level === 'moderate' ? 'Halt Ascent & Rest' : 'Normal Progress'}
              </h3>

              <p style={{ fontSize: '1rem', lineHeight: '1.5' }}>
                {language==='hi'?result.guidance_hi:result.guidance_en}
              </p>
            </div>

            {/* Mandatory Call Option at Moderate or Higher */}
            {result.emergency_contact_needed && (
              <div className="trail-card" style={{ background: 'var(--paper-2)', border: '2px solid var(--urgent)' }}>
                <div className="meta-label" style={{ color: 'var(--urgent)' }}>{tr("EMERGENCY CONTACT MANDATE")}</div>
                <p style={{ fontSize: '0.9rem', marginTop: 'var(--space-1)' }}>
                  {tr("Assistance required. Contact Himachal Emergency Rescue immediately:")}
                </p>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-2)', marginTop: 'var(--space-3)' }}>
                  <a href="tel:112" className="btn btn-accent" style={{ textDecoration: 'none' }}>
                    <PhoneCall size={16} /> {tr("Call 112 (Disaster)")}
                  </a>
                  <a href="tel:108" className="btn" style={{ textDecoration: 'none', background: 'var(--paper)' }}>
                    <PhoneCall size={16} /> {tr("Call 108 (Medical)")}
                  </a>
                </div>
              </div>
            )}

            <button onClick={() => setResult(null)} style={{ width: '100%' }}>
              {tr("Run Another Assessment")}
            </button>
          </div>
        )}

      </div>
    </div>
  );
};

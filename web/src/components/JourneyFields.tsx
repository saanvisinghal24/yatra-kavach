import {useEffect,useState} from 'react';
import {api} from '../lib/api';
export type Direction='outbound'|'returning'|'exit';
export function JourneyFields({code,direction,onDirection,selected,onSelected,onCount}:{code:string;direction:Direction;onDirection:(d:Direction)=>void;selected:number[];onSelected:(ids:number[])=>void;onCount:(n:number)=>void}){
 const [members,setMembers]=useState<any[]>([]);const [message,setMessage]=useState('');
 useEffect(()=>{let alive=true;setMembers([]);onSelected([]);if(!/^[A-Z0-9]{6}$/.test(code))return;const key='members-'+code;
 const cached=localStorage.getItem(key);if(cached){try{setMembers(JSON.parse(cached));setMessage('Cached member roster / सहेजी सदस्य सूची');}catch{}}
 api('/groups/'+code).then(g=>{if(!alive)return;setMembers(g.members||[]);localStorage.setItem(key,JSON.stringify(g.members||[]));setMessage('Server roster / सर्वर सदस्य सूची');}).catch(()=>{if(alive)setMessage('Offline: cached roster only. Load online before recording a partial group. / आंशिक दल के लिए पहले सूची डाउनलोड करें।');});return()=>{alive=false;};
 },[code]);
 return <fieldset><legend>Journey accounting / यात्रा सदस्य मिलान</legend><label>Direction / दिशा<select value={direction} onChange={e=>onDirection(e.target.value as Direction)}><option value="outbound">Outbound / ऊपर की ओर</option><option value="returning">Returning / वापस (बीच से भी)</option><option value="exit">Hadsar exit / हड़सर निकास</option></select></label><p>Final exit requires volunteer confirmation at Hadsar. Lake arrival is not completion. / अंतिम निकास हड़सर में स्वयंसेवक पुष्टि पर होगा।</p><p>{message}</p>{members.length>0&&<><p>Select members physically present; leave all unchecked only for the entire group. / उपस्थित सदस्य चुनें; पूरे दल के लिए सभी खाली रखें।</p>{members.map(m=><label className="member-choice" key={m.id}><input type="checkbox" checked={selected.includes(m.id)} onChange={e=>{const ids=e.target.checked?[...selected,m.id]:selected.filter(id=>id!==m.id);onSelected(ids);onCount(ids.length||members.length);}}/>{m.name||`Member ${m.id}`} · {m.journey_state||'outbound'}</label>)}</>}</fieldset>;
}

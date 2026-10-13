import {useEffect,useRef,useState} from 'react';
import L from 'leaflet';
import {manimaheshRoute} from '../trail/ManimaheshRoute';
import 'leaflet/dist/leaflet.css';
export const DEMO_CHECKPOINTS=[
 {id:1,name_en:'Hadsar',lat:32.3685,lon:76.6041,altitude_m:2100,status:'open'},
 {id:2,name_en:'Dhancho',lat:32.3812,lon:76.6231,altitude_m:3000,status:'open'},
 {id:3,name_en:'Sundrasi',lat:32.3866,lon:76.6305,altitude_m:3350,status:'open'},
 {id:4,name_en:'Gauri Kund',lat:32.392,lon:76.638,altitude_m:3850,status:'open'},
 {id:5,name_en:'Manimahesh Lake',lat:32.3982,lon:76.6434,altitude_m:4080,status:'open'}
];
export function ControlMap({checkpoints,groups=[]}:{checkpoints:any[];groups?:any[]}){
 const ref=useRef<HTMLDivElement>(null);const [tiles,setTiles]=useState(false);
 const demo=checkpoints.length===0;
 const points=[...(demo?DEMO_CHECKPOINTS:checkpoints)].sort((a:any,b:any)=>(a.seq??0)-(b.seq??0));
 const signature=JSON.stringify([points,groups.map(g=>[g.code,g.last_checkpoint_id])]);
 useEffect(()=>{
  if(!ref.current)return;setTiles(false);
  const map=L.map(ref.current,{scrollWheelZoom:false});
  const route=manimaheshRoute.points.map(p=>[p[1],p[0]] as L.LatLngTuple);
  const layer=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,attribution:'© OpenStreetMap contributors'}).addTo(map);
  layer.on('tileload',()=>setTiles(true));
  L.polyline(route,{color:'#ffffff',weight:8,opacity:0.95}).addTo(map);
  L.polyline(route,{color:'#24583b',weight:4,opacity:1}).addTo(map);
  const bounds=L.latLngBounds(route);
  points.forEach((c,i)=>{
   // Keep the backend checkpoint identity; never invent or snap coordinates.
   if(c.lat==null||c.lon==null||String(c.lat).trim()===''||String(c.lon).trim()==='')return;
   const lat=Number(c.lat),lon=Number(c.lon);
   if(!Number.isFinite(lat)||!Number.isFinite(lon)||Math.abs(lat)>90||Math.abs(lon)>180)return;
   const position:L.LatLngTuple=[lat,lon];
   bounds.extend(position);
   const label=document.createElement('span');
   label.textContent=`${i+1}. ${c.name_en||c.name_hi||'Checkpoint'}`;
   const popup=document.createElement('div');
   const title=document.createElement('strong');title.textContent=label.textContent;
   const detail=document.createElement('p');
   detail.textContent=`${demo?'Demo location':'Configured location'} · unverified. Status: ${c.status||'Unknown'}. Altitude: ${c.altitude_m??'Unknown'} m.`;
   const reported=document.createElement('p');
   reported.textContent=`Groups last reported here: ${groups.filter(g=>String(g.last_checkpoint_id)===String(c.id)).map(g=>g.code).join(', ')||'None'}`;
   popup.append(title,detail,reported);
   L.circleMarker(position,{radius:9,color:'#fff',weight:3,fillColor:'#a74312',fillOpacity:1})
    .addTo(map).bindTooltip(label,{permanent:true,direction:i%2?'left':'right',offset:[i%2?-10:10,0]})
    .bindPopup(popup);
  });
  map.fitBounds(bounds,{padding:[65,45]});
  const observer=new ResizeObserver(()=>map.invalidateSize());observer.observe(ref.current);
  return ()=>{observer.disconnect();map.remove();};
 // Serialized data avoids recreating the map on every polling response.
 // eslint-disable-next-line react-hooks/exhaustive-deps
 },[signature]);
 return <section className="map-section"><div ref={ref} className="manimahesh-map" style={{height:440,width:'100%'}} aria-label="Manimahesh checkpoint map"/>{!tiles&&<p role="status" className="map-note">Basemap unavailable or loading. The recorded route line remains visible offline; use the offline route overview below.</p>}<p className="form-help">Recorded walking track: Wikiloc / inditramp, September 2016. Current trail alignment is unverified. Pins show configured checkpoint coordinates, which are unverified and may not align with the recorded track. They are not navigation directions.</p>{demo&&<p role="status">Showing demo checkpoints while route checkpoint data is unavailable.</p>}<h3>Checkpoint trail / चौकी क्रम</h3><p>Route order below is schematic; tap a checkpoint for details.</p><ol className="checkpoint-overview" style={{display:'flex',flexDirection:'column',gap:12}}>{points.map((c,i)=><li key={c.id}><span>{String(i+1).padStart(2,'0')}</span><div><details><summary><strong>{c.name_en}</strong> · {c.altitude_m} m</summary><p>Status: {c.status||'Unknown'} · Daily cutoff: {c.cutoff_time||'Not supplied'} IST</p><p>Groups last reported here: {groups.filter(g=>g.last_checkpoint_id===c.id).map(g=>g.code).join(', ')||'None'}</p></details></div></li>)}</ol></section>;
}
export default ControlMap;

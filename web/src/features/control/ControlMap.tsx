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
 const points=checkpoints.length?checkpoints:DEMO_CHECKPOINTS;
 const signature=JSON.stringify([points,groups.map(g=>[g.code,g.last_checkpoint_id])]);
 useEffect(()=>{
  if(!ref.current)return;setTiles(false);
  const map=L.map(ref.current,{scrollWheelZoom:false});
  const route=manimaheshRoute.points.map(p=>[p[1],p[0]] as L.LatLngTuple);
  const layer=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,attribution:'© OpenStreetMap contributors'}).addTo(map);
  layer.on('tileload',()=>setTiles(true));
  L.polyline(route,{color:'#ffffff',weight:8,opacity:0.95}).addTo(map);
  L.polyline(route,{color:'#24583b',weight:4,opacity:1}).addTo(map);
  map.fitBounds(L.latLngBounds(route),{padding:[25,35]});
  [[route[0],'Hadsar · recorded start'],[route[route.length-1],'Manimahesh · recorded end']].forEach(([position,name])=>{
   const label=document.createElement('span');label.textContent=String(name);
   L.circleMarker(position as L.LatLngTuple,{radius:7,color:'#fff',weight:2,fillColor:'#a74312',fillOpacity:1}).addTo(map).bindTooltip(label,{direction:'top'});
  });
  const observer=new ResizeObserver(()=>map.invalidateSize());observer.observe(ref.current);
  return ()=>{observer.disconnect();map.remove();};
 // Serialized data avoids recreating the map on every polling response.
 // eslint-disable-next-line react-hooks/exhaustive-deps
 },[signature]);
 return <section className="map-section"><div ref={ref} className="manimahesh-map" aria-label="Manimahesh checkpoint map"/>{!tiles&&<p role="status" className="map-note">Basemap unavailable or loading. The recorded route line remains visible offline; use the offline route overview below.</p>}<p className="form-help">Recorded walking track: Wikiloc / inditramp, September 2016. Current trail alignment is unverified. Unverified checkpoint pins are omitted; checkpoint order is listed below.</p><h3>Checkpoint trail / चौकी क्रम</h3><p>Route order below is schematic; tap a checkpoint for details.</p><ol className="checkpoint-overview" style={{display:'flex',flexDirection:'column',gap:12}}>{points.map((c,i)=><li key={c.id}><span>{String(i+1).padStart(2,'0')}</span><div><details><summary><strong>{c.name_en}</strong> · {c.altitude_m} m</summary><p>Status: {c.status||'Unknown'} · Daily cutoff: {c.cutoff_time||'Not supplied'} IST</p><p>Groups last reported here: {groups.filter(g=>g.last_checkpoint_id===c.id).map(g=>g.code).join(', ')||'None'}</p></details></div></li>)}</ol></section>;
}
export default ControlMap;

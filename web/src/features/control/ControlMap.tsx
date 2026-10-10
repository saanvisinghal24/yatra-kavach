import {useEffect,useRef,useState} from 'react';
import L from 'leaflet';
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
  const valid=points.filter(c=>Number.isFinite(c.lat)&&Number.isFinite(c.lon));
  const layer=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,attribution:'© OpenStreetMap contributors'}).addTo(map);
  layer.on('tileload',()=>setTiles(true));
  const bounds=L.latLngBounds(valid.map(c=>[c.lat,c.lon] as L.LatLngTuple));
  if(valid.length)map.fitBounds(bounds,{padding:[55,55],maxZoom:14});else map.setView([32.383,76.623],13);
  valid.forEach((cp,i)=>{
   const marker=L.circleMarker([cp.lat,cp.lon],{radius:8,color:'#fff',weight:3,fillColor:'#a74312',fillOpacity:1}).addTo(map);
   const label=document.createElement('span');label.textContent=`${i+1}. ${cp.name_en}`;
   marker.bindTooltip(label,{permanent:true,direction:i%2?'left':'right',className:'checkpoint-label'});
   const popup=document.createElement('div');popup.textContent=`${cp.name_en} · ${cp.altitude_m} m · ${cp.status||'Unknown'} (indicative)`;marker.bindPopup(popup);
  });
  groups.forEach(g=>{const cp=valid.find(c=>c.id===g.last_checkpoint_id);if(cp){const label=document.createElement('span');label.textContent=g.code;L.circleMarker([cp.lat,cp.lon],{radius:4,color:'#1e3227'}).addTo(map).bindPopup(label);}});
  const observer=new ResizeObserver(()=>map.invalidateSize());observer.observe(ref.current);
  return ()=>{observer.disconnect();map.remove();};
 // Serialized data avoids recreating the map on every polling response.
 // eslint-disable-next-line react-hooks/exhaustive-deps
 },[signature]);
 return <section className="map-section"><div ref={ref} className="manimahesh-map" aria-label="Manimahesh checkpoint map"/>{!tiles&&<p role="status" className="map-note">Basemap tiles unavailable or loading. Checkpoint markers and the overview below remain available.</p>}<p className="form-help">Indicative locations from the demo dataset, not a verified walking route. Group dots show last reported checkpoints.</p><ol className="checkpoint-overview">{points.map((c,i)=><li key={c.id}><span>{String(i+1).padStart(2,'0')}</span><div><strong>{c.name_en}</strong><small>{c.altitude_m} m</small></div></li>)}</ol></section>;
}
export default ControlMap;

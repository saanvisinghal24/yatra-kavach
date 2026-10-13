import {useEffect,useMemo,useRef,useState} from 'react';
import L from 'leaflet';
import {manimaheshRoute} from '../trail/ManimaheshRoute';
import 'leaflet/dist/leaflet.css';

// Reference LOCALITIES, not surveyed QR-board positions. These replace the
// unrelated demo coordinates previously used for the Manimahesh overview.
// Hadsar and Dhancho: inditramp's original 2016 track waypoints.
// Sundrasi: field collection locality, DOI 10.1080/00087114.2017.1344084.
// Gauri Kund: field collection locality, PMC3833778, Table 1.
// Lake: endpoint of the supplied recorded track.
const REFERENCES=[
 {key:'hadsar',aliases:['hadsar','harsar','hudsar','harser','हड़सर','हड़सर','हडसर'],name_en:'Hadsar',lat:32.452682,lon:76.615205,source:'Wikiloc 15400169, waypoint 15400170'},
 {key:'dhancho',aliases:['dhancho','dhanchho','dhanchoo','धनछो','धनछौ'],name_en:'Dhancho',lat:32.422591,lon:76.607353,source:'Wikiloc 15400169, waypoint 15400178'},
 {key:'sundrasi',aliases:['sundrasi','sundrashi','sundarasi','sundarshi','सुंदरासी','सुन्दरासी'],name_en:'Sundrasi',lat:32.408888889,lon:76.633333333,source:'Field locality: 32°24′32″N, 76°38′00″E; DOI 10.1080/00087114.2017.1344084'},
 {key:'gaurikund',aliases:['gaurikund','गौरीकुंड','गौरीकुण्ड'],name_en:'Gauri Kund',lat:32.401833333,lon:76.6375,source:'Field locality: 32°24.11′N, 76°38.25′E; PMC3833778, Table 1'},
 {key:'manimahesh',aliases:['manimahesh','manimaheshlake','manimaheshdal','dal lake','मणिमहेश','मनिमहेश','मणिमहेशझील','मनिमहेशझील'],name_en:'Manimahesh Lake',lat:manimaheshRoute.points[manimaheshRoute.points.length-1][1],lon:manimaheshRoute.points[manimaheshRoute.points.length-1][0],source:'Endpoint of supplied Wikiloc / inditramp recorded track'}
];
const normalise=(value:unknown)=>String(value??'').toLowerCase().replace(/[\s_\-().]/g,'');
function referenceFor(c:any){
 const names=[c.name_en,c.name_hi,c.name,c.slug].map(normalise).filter(Boolean);
 return REFERENCES.find(r=>r.aliases.some(a=>names.includes(normalise(a))));
}
export const DEMO_CHECKPOINTS=REFERENCES.map((r,i)=>({id:i+1,seq:i+1,name_en:r.name_en,lat:r.lat,lon:r.lon,altitude_m:[2100,3000,3350,3850,4080][i],status:'unknown'}));

// Only display geometry is resolved here. Backend IDs, scans, status, and
// timing values remain untouched. Do not feed these reference points to GPS
// proximity checks or claim that they identify the physical QR boards.
export function resolveMapCheckpoints(checkpoints:any[]){
 return [...checkpoints].sort((a,b)=>Number(a.seq??0)-Number(b.seq??0)).map(c=>{
  const r=referenceFor(c);
  const rawLat=c.lat,rawLon=c.lon;
  const lat=r?.lat??(rawLat==null||String(rawLat).trim()===''?NaN:Number(rawLat));
  const lon=r?.lon??(rawLon==null||String(rawLon).trim()===''?NaN:Number(rawLon));
  return {...c,mapLat:lat,mapLon:lon,mapReference:r?.source,
   hasMapPosition:Number.isFinite(lat)&&Number.isFinite(lon)&&Math.abs(lat)<=90&&Math.abs(lon)<=180};
 });
}

export function ControlMap({checkpoints,groups=[]}:{checkpoints:any[];groups?:any[]}){
 const ref=useRef<HTMLDivElement>(null);
 const [tiles,setTiles]=useState(false);
 const demo=checkpoints.length===0;
 const signature=JSON.stringify([demo,checkpoints,groups.map(g=>[g.code,g.last_checkpoint_id])]);
 const points=useMemo(()=>resolveMapCheckpoints(demo?DEMO_CHECKPOINTS:checkpoints),[signature]);
 useEffect(()=>{
  if(!ref.current)return;
  setTiles(false);
  const map=L.map(ref.current,{scrollWheelZoom:false});
  const route=manimaheshRoute.points.map(p=>[p[1],p[0]] as L.LatLngTuple);
  const layer=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,attribution:'© OpenStreetMap contributors'}).addTo(map);
  layer.on('tileload',()=>setTiles(true));
  L.polyline(route,{color:'#fff',weight:8,opacity:0.95}).addTo(map);
  L.polyline(route,{color:'#24583b',weight:4,opacity:1}).addTo(map);
  const bounds=L.latLngBounds(route);
  points.forEach((c,i)=>{
   if(!c.hasMapPosition)return;
   const position:L.LatLngTuple=[c.mapLat,c.mapLon];
   bounds.extend(position);
   const label=document.createElement('span');
   label.textContent=`${i+1}. ${c.name_en||c.name_hi||'Checkpoint'}`;
   const popup=document.createElement('div');
   const title=document.createElement('strong');title.textContent=label.textContent;
   const detail=document.createElement('p');
   detail.textContent=c.mapReference?'Approximate locality reference. Exact QR-board position has not been surveyed.':'Configured coordinates; position not field-verified.';
   const status=document.createElement('p');status.textContent=`Status: ${demo?'Demo / unavailable':c.status||'Unknown'}`;
   const reported=document.createElement('p');reported.textContent=`Groups last reported here: ${groups.filter(g=>String(g.last_checkpoint_id)===String(c.id)).map(g=>g.code).join(', ')||'None'}`;
   popup.append(title,detail,status,reported);
   L.circleMarker(position,{radius:8,color:'#fff',weight:3,fillColor:'#a74312',fillOpacity:1})
    .addTo(map).bindTooltip(label,{permanent:true,direction:i%2?'left':'right',offset:[i%2?-10:10,0]})
    .bindPopup(popup);
  });
  map.fitBounds(bounds,{paddingTopLeft:[100,45],paddingBottomRight:[145,45]});
  const observer=new ResizeObserver(()=>map.invalidateSize());observer.observe(ref.current);
  return()=>{observer.disconnect();map.remove();};
 // Stable serialized data avoids rebuilding on identical polling responses.
 // eslint-disable-next-line react-hooks/exhaustive-deps
 },[signature]);
 return <section className="map-section">
  <div ref={ref} className="manimahesh-map" style={{height:460,width:'100%',borderRadius:12}} aria-label="Manimahesh route and approximate checkpoint localities"/>
  {!tiles&&<p role="status" className="map-note">Basemap loading or unavailable. Route and checkpoint references remain visible without map tiles.</p>}
  <p className="form-help">Hadsar → Dhancho → Sundrasi → Gauri Kund → Manimahesh Lake. Approximate locality markers; recorded route from 2016. Not turn-by-turn navigation.</p>
  {demo&&<p role="status">Route preview — live checkpoint records have not loaded.</p>}
  <details className="form-help"><summary>Map sources & location accuracy</summary>
   <p>Locality references replace the old demo coordinates for these five named stops. The exact QR-board locations and present-day route still require field verification. Scans continue to use the original checkpoint IDs.</p>
   <ul><li><a href="https://www.wikiloc.com/hiking-trails/hadsar-to-mani-mahesh-lake-15400169" target="_blank" rel="noreferrer">Recorded track and Hadsar / Dhancho waypoints</a></li>
    <li><a href="https://doi.org/10.1080/00087114.2017.1344084" target="_blank" rel="noreferrer">Sundrasi field locality</a></li>
    <li><a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC3833778/" target="_blank" rel="noreferrer">Gauri Kund field locality — Table 1</a></li></ul>
  </details>
  <h3>Checkpoint trail / चौकी क्रम</h3>
  <ol className="checkpoint-overview" style={{display:'flex',flexDirection:'column',gap:12}}>
   {points.map((c,i)=><li key={c.id}><span>{String(i+1).padStart(2,'0')}</span><div><details>
    <summary><strong>{c.name_en||c.name_hi}</strong> · {c.altitude_m??'—'} m</summary>
    <p>Status: {demo?'Demo / unavailable':c.status||'Unknown'} · Daily cutoff: {c.cutoff_time||'Not supplied'} IST</p>
    {!c.hasMapPosition&&<p>Coordinates unavailable; this checkpoint is listed but cannot be placed on the map.</p>}
    <p>Groups last reported here: {groups.filter(g=>String(g.last_checkpoint_id)===String(c.id)).map(g=>g.code).join(', ')||'None'}</p>
   </details></div></li>)}
  </ol>
 </section>;
}
export default ControlMap;

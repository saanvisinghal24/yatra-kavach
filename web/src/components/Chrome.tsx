import React,{useEffect,useState} from 'react';
import {Link,useLocation} from 'react-router-dom';
import {api} from '../lib/api';
import {useTranslation} from '../lib/i18n/LanguageContext';
import {getPendingCheckinCount,getLastSyncTime,syncPendingCheckins} from '../lib/sync';
export class ErrorBoundary extends React.Component<{children:React.ReactNode},{failed:boolean}> {
 state={failed:false}; static getDerivedStateFromError(){return {failed:true};}
 render(){return this.state.failed?<main className="page"><h1>Unable to open this screen</h1><p>Your saved scans remain on this device.</p><button onClick={()=>location.reload()}>Reload</button><a href="/">Home</a></main>:this.props.children;}
}
export function Chrome(){
 const {pathname}=useLocation();const {language}=useTranslation();const [config,setConfig]=useState<any>({});const [queued,setQueued]=useState(0);const [install,setInstall]=useState<any>(null);const [ios,setIos]=useState(false);
 useEffect(()=>{api('/config').then(setConfig).catch(()=>{});const timer=setInterval(()=>getPendingCheckinCount().then(setQueued),2000);syncPendingCheckins();const listener=(e:Event)=>{e.preventDefault();setInstall(e);};window.addEventListener('beforeinstallprompt',listener);if(/iPhone|iPad/.test(navigator.userAgent)&&!localStorage.getItem('install-dismissed'))setIos(true);return()=>{clearInterval(timer);window.removeEventListener('beforeinstallprompt',listener);};},[]);
 useEffect(()=>{const name=pathname.split('/')[1]||'Trail safety';document.title=`${name.replace(/-/g,' ')} · Yatra Kavach`;document.querySelector('meta[name="description"]')?.setAttribute('content',`Yatra Kavach ${name}. Himachal Pradesh pilgrim trail safety demo.`);const canonical=document.querySelector('link[rel="canonical"]');canonical?.setAttribute('href',(import.meta.env.VITE_PUBLIC_ORIGIN||location.origin)+pathname);},[pathname]);
 const dismiss=()=>{setInstall(null);setIos(false);};
 return <><div className="sync-strip" aria-live="polite">{language==='hi'?'सहेजे स्कैन':'Queued scans'}: {queued} · {getLastSyncTime()||'Not yet synced'} <button onClick={()=>syncPendingCheckins()}>Sync now / सिंक करें</button><Link to="/demo/offline-check">Offline check</Link></div>
 <aside className="trail-card install"><h2>Install Yatra Kavach / ऐप इंस्टॉल करें</h2>{install?<button onClick={async()=>{await install.prompt();const result=await install.userChoice;if(result.outcome==='accepted')dismiss();}}>Install app</button>:<p>{ios?'Safari: Share → Add to Home Screen → Add.':'Android Chrome: ⋮ menu → Add to home screen → Install. If already installed, open Yatra Kavach from your home screen.'}</p>}<p>Open online once to save the app for offline use.</p><Link to="/offline-map">Open offline route / ऑफलाइन मार्ग खोलें</Link></aside>
 <footer><p>Yatra Kavach · v1.1.0</p><nav>{['privacy','terms','about','roadmap','volunteer-guide'].map(p=><Link key={p} to={'/'+p}>{p.replace(/-/g,' ')}</Link>)}</nav>{config.contact_email&&<a href={'mailto:'+config.contact_email}>{config.contact_email}</a>}<p>Indicative data · Emergency 112 / 108</p></footer></>;
}

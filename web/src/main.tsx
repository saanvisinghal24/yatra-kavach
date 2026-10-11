import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles/index.css';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Refresh installed applications when an update activates; preserve in-progress forms.
if ('serviceWorker' in navigator) {
 let refreshing=false;
 const check=()=>{if(navigator.onLine)navigator.serviceWorker.getRegistration().then(r=>r?.update()).catch(()=>{});};
 navigator.serviceWorker.ready.then(check);
 window.addEventListener('online',check);
 document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')check();});
 setInterval(check, 5*60*1000);
 navigator.serviceWorker.addEventListener('controllerchange',()=>{
  if(refreshing)return;
  if(document.querySelector('form')||/INPUT|TEXTAREA|SELECT/.test(document.activeElement?.tagName||'')){
   const button=document.createElement('button');button.textContent='Update ready — tap to refresh after saving';button.style.cssText='position:fixed;bottom:12px;left:12px;right:12px;z-index:9999;padding:16px;background:#244b35;color:white';button.onclick=()=>location.reload();document.body.append(button);
  }else{refreshing=true;location.reload();}
 });
}

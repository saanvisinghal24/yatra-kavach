import {useEffect, useRef, useState} from 'react';
import {faqs, Lang, savedAnswer, urgent} from './faq';
import './assistant.css';
type Message={role:'user'|'assistant';text:string;source?:'AI'|'Saved';notice?:string};
export default function YatraAssistant(){
 const [open,setOpen]=useState(false),[lang,setLang]=useState<Lang>('en'),[input,setInput]=useState(''),[busy,setBusy]=useState(false),[online,setOnline]=useState(navigator.onLine),[messages,setMessages]=useState<Message[]>([]);
 const lock=useRef(false),abort=useRef<AbortController|null>(null),bottom=useRef<HTMLDivElement>(null),field=useRef<HTMLInputElement>(null),launcher=useRef<HTMLButtonElement>(null);
 useEffect(()=>{const update=()=>setOnline(navigator.onLine);window.addEventListener('online',update);window.addEventListener('offline',update);return()=>{window.removeEventListener('online',update);window.removeEventListener('offline',update);abort.current?.abort();};},[]);
 useEffect(()=>{bottom.current?.scrollIntoView({block:'nearest'});},[messages,busy]);
 useEffect(()=>{if(open)field.current?.focus();},[open]);
 const close=()=>{setOpen(false);launcher.current?.focus();};
 async function send(question=input){
  const q=question.trim();if(!q||lock.current)return;lock.current=true;setBusy(true);setInput('');
  setMessages(m=>[...m.slice(-39),{role:'user',text:q}]);
  let answer=savedAnswer(q,lang),source:'AI'|'Saved'='Saved',notice='';
  const controller=new AbortController();abort.current=controller;const timer=setTimeout(()=>controller.abort(),65000);
  try{
   if(navigator.onLine&&!urgent(q)){
    const response=await fetch('/api/v1/assistant/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q,language:lang}),signal:controller.signal,cache:'no-store'});
    if(!response.ok)throw Error('HTTP '+response.status);
    const data=await response.json();if(data.mode!=='ai'||typeof data.answer!=='string'||!data.answer.trim())throw Error(data.reason||'invalid_response');
    answer=data.answer;source='AI';
   }
  }catch(error){
   const code=error instanceof Error?error.message:'';
   const reasons:Record<string,string>={not_configured:'AI key is not configured on the server.',provider_auth:'AI provider rejected the server key.',provider_request:'AI provider rejected the request or model settings.',provider_model:'AI model is unavailable for this account.',provider_rate_limit:'AI provider quota or rate limit reached.',provider_timeout:'AI provider timed out.',provider_unavailable:'AI provider is unavailable.','HTTP 404':'Chat endpoint is missing from the deployment.','HTTP 405':'Chat endpoint routing is incorrect.','HTTP 401':'Server rejected this request.','HTTP 403':'Server blocked this request.','HTTP 429':'Too many questions. Please wait a minute.'};
   const reason=reasons[code]||(error instanceof Error&&error.name==='AbortError'?'Server took too long to respond.':'Server connection or response failed.');
   notice=(lang==='hi'?'AI उपलब्ध नहीं है। सेव किया जवाब। ':'AI unavailable. Showing saved guidance. ')+reason;
  }
  finally{clearTimeout(timer);lock.current=false;setBusy(false);}
  setMessages(m=>[...m,{role:'assistant',text:answer,source,notice}]);
 }
 return <aside className="yk-assistant">
  <button ref={launcher} className="yk-launch" aria-expanded={open} aria-controls="yk-chat" onClick={()=>open?close():setOpen(true)}>☏ {lang==='hi'?'यात्रा सहायक':'Yatra Sahayak'}</button>
  {open&&<section id="yk-chat" className="yk-panel" role="dialog" aria-label="Yatra Sahayak" onKeyDown={e=>{if(e.key==='Escape')close();}}>
   <header><div><strong>Yatra Sahayak</strong><small>{online?'Online · AI with saved fallback':'Offline · Saved answers'}</small></div><button aria-label="Close chat" onClick={close}>×</button></header>
   <div className="yk-options"><label>Language <select value={lang} disabled={busy} onChange={e=>setLang(e.target.value as Lang)}><option value="en">English</option><option value="hi">हिन्दी</option></select></label><button disabled={busy} onClick={()=>setMessages([])}>Clear</button></div>
   <p className="yk-info">{lang==='hi'?'ऑनलाइन प्रश्न Groq AI को भेजे जाते हैं। निजी विवरण न लिखें। चैट SOS नहीं भेजती।':'Online questions go to Groq AI. Avoid personal details. Chat does not send SOS requests.'}</p>
   <div className="yk-messages" role="log" aria-live="polite" aria-busy={busy}>
    {!messages.length&&<p>{lang==='hi'?'नमस्ते! ऐप या यात्रा प्रक्रिया के बारे में पूछें।':'Namaste! Ask about the app or journey process.'}</p>}
    {messages.map((m,i)=><div className={'yk-message yk-bubble-'+m.role} key={i}>{m.source&&<small>{m.source==='AI'?'AI answer':'Saved answer'}{m.source==='AI'?' · Check important details with staff':''}</small>}{m.notice&&<small>{m.notice}</small>}<p>{m.text}</p></div>)}
    {busy&&<p>{lang==='hi'?'जवाब खोज रहे हैं…':'Finding an answer…'}</p>}<div ref={bottom}/>
   </div>
   <div className="yk-topics">{faqs.map(f=><button key={f.keys[0]} disabled={busy} onClick={()=>send(f[lang][0])}>{f[lang][0]}</button>)}</div>
   <form onSubmit={e=>{e.preventDefault();void send();}}><input ref={field} aria-label="Your question" maxLength={800} value={input} onChange={e=>setInput(e.target.value)} placeholder={lang==='hi'?'अपना प्रश्न लिखें':'Type your question'} disabled={busy}/><button disabled={busy||!input.trim()} type="submit">{lang==='hi'?'भेजें':'Send'}</button></form>
  </section>}
 </aside>;
}

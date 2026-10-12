export function arrivalTiming(scan:string|undefined,low:number,high:number,now:number){
 if(!scan||!Number.isFinite(low)||!Number.isFinite(high))return null;
 const start=Date.parse(/(?:Z|[+-]\d\d:\d\d)$/.test(scan)?scan:scan+'Z');
 if(!Number.isFinite(start))return null;
 const elapsed=Math.max(0,(now-start)/60000);
 const fmt=(n:number)=>new Intl.DateTimeFormat('en-IN',{timeZone:'Asia/Kolkata',hour:'2-digit',minute:'2-digit'}).format(new Date(n));
 return {arrival:`${fmt(start+low*60000)} – ${fmt(start+high*60000)} IST`,remaining:elapsed>high?'Estimated window passed — check in or contact checkpoint staff.':`${Math.max(0,Math.ceil(low-elapsed))}–${Math.max(0,Math.ceil(high-elapsed))} min remaining`};
}

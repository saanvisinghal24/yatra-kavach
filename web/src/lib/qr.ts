export function checkpointToken(raw:string):{token:string;id:number}{
 let token=raw.trim();if(/^https?:\/\//.test(token))token=new URL(token).searchParams.get('token')||'';
 const match=/^YK1:CP:([1-9]\d*):([0-9a-f]{8})$/i.exec(token);
 if(!match)throw new Error('Invalid checkpoint QR format / अमान्य चौकी क्यूआर');
 return {token,id:Number(match[1])};
}
export function passCode(raw:string):string{let value=raw.trim();if(/^https?:\/\//.test(value)){const url=new URL(value);value=url.searchParams.get('token')||url.pathname.split('/').pop()||'';}const code=value.replace(/^YK1:/,'');if(!/^[23456789ABCDEFGHJKMNPQRSTUVWXYZ]{6}$/.test(code))throw new Error('Invalid group pass');return code;}

import {useRef,useState,useEffect} from 'react';
import QrScanner from 'qr-scanner';
export function CameraScanner({onScan}:{onScan:(value:string)=>void}){
 const video=useRef<HTMLVideoElement>(null);const scanner=useRef<QrScanner>();
 const [error,setError]=useState('');const [scanned,setScanned]=useState(false);
 useEffect(()=>()=>scanner.current?.destroy(),[]);
 const accept=(value:string)=>{scanner.current?.stop();setError('');setScanned(true);onScan(value);};
 return <section><video ref={video} playsInline muted style={{width:'100%',maxHeight:420,objectFit:'contain',display:'block',background:'#17251c'}}/>
 <button type="button" onClick={async()=>{setScanned(false);setError('');try{
 if(!window.isSecureContext)throw new Error('Open the HTTPS website to use the camera');
 scanner.current?.destroy();scanner.current=new QrScanner(video.current!,r=>accept(r.data),{returnDetailedScanResult:true,preferredCamera:'environment',calculateScanRegion:v=>({x:0,y:0,width:v.videoWidth,height:v.videoHeight,downScaledWidth:1024,downScaledHeight:Math.max(1,Math.round(1024*v.videoHeight/v.videoWidth))})});
 await scanner.current.start();
 }catch(e){setError(`${(e as Error).message || 'Camera unavailable'}. Allow camera access, or upload a QR image below.`);}}}>Start camera / कैमरा शुरू करें</button>
 <label>Upload QR image / क्यूआर फोटो चुनें<input type="file" accept="image/*" onChange={async e=>{const file=e.target.files?.[0];if(!file)return;try{const result=await QrScanner.scanImage(file,{returnDetailedScanResult:true});accept(result.data);}catch{setError('QR not found. Choose a clear image containing the complete QR and its white border.');}e.target.value='';}}/></label>
 {scanned&&<p role="status">QR read. Complete the details below and save. / क्यूआर पढ़ लिया गया। विवरण भरकर सहेजें।</p>}{error&&<p role="alert">{error}</p>}</section>;
}

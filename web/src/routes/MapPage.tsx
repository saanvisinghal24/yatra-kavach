import {useEffect,useState} from 'react';
import {Link} from 'react-router-dom';
import {api} from '../lib/api';
import {ControlMap} from '../features/control/ControlMap';
export function MapPage(){const [checkpoints,setCheckpoints]=useState<any[]>([]);useEffect(()=>{api('/yatras/manimahesh').then(y=>setCheckpoints(y.routes[0].checkpoints)).catch(()=>{});},[]);return <main className="page"><span className="eyebrow">CHAMBA · HIMACHAL PRADESH</span><h1>Manimahesh Yatra map</h1><p>From Hadsar to the lake: explore the five proposed checkpoints.</p><ControlMap checkpoints={checkpoints}/><Link className="btn btn-primary" to="/register">Register for this yatra</Link></main>;}

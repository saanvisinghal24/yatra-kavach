import {Login} from '../routes/Login';
import {Navigate,useLocation} from 'react-router-dom';
import {useText} from '../lib/i18n/useText';
import React, { createContext, useContext, useEffect, useState } from 'react';
import { api, post } from '../lib/api';
const StaffContext=createContext<{role:string}|null>(null);
export const useStaff=()=>useContext(StaffContext);
export function StaffGate({children}: {children: React.ReactNode}) {
  const text=useText();const location=useLocation();
  const [staff,setStaff]=useState<any>(); const [ready,setReady]=useState(false);
  useEffect(()=>{api('/auth/me').then(setStaff).catch(()=>{}).finally(()=>setReady(true));},[]);
  if (!ready) return <main className="page">{text("Loading staff session…")}</main>;
  if (staff?.role === "volunteer" && (location.pathname.startsWith("/control") || location.pathname.startsWith("/admin"))) return <Navigate to="/volunteer" replace/>;
  if (staff) return <StaffContext.Provider value={staff}><div className="staff-bar">{text(staff.role)} · {text("Himachal Pradesh demo control room")} <button onClick={()=>post('/auth/logout').then(()=>setStaff(null))}>{text("Sign out")}</button></div>{children}</StaffContext.Provider>;
  return <Login staffOnly onSignedIn={setStaff}/>;
}

import {RoutePack} from './features/trail/RoutePack';
import React, {lazy, Suspense} from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
const RegisterWizard=lazy(()=>import('./features/register/RegisterWizard').then(m=>({default:m.RegisterWizard})));
const PassView=lazy(()=>import('./features/register/PassView').then(m=>({default:m.PassView})));
const TrailView=lazy(()=>import('./features/trail/TrailView').then(m=>({default:m.TrailView})));
const ScanScreen=lazy(()=>import('./features/scan/ScanScreen').then(m=>({default:m.ScanScreen})));
const VolunteerScan=lazy(()=>import('./features/volunteer/VolunteerScan').then(m=>({default:m.VolunteerScan})));
const ControlDashboard = lazy(() => import('./features/control/ControlDashboard').then(m=>({default:m.ControlDashboard})));
import {StaffGate} from './components/StaffGate';
import {Chrome,ErrorBoundary} from './components/Chrome';
import {Login} from './routes/Login';
import {MapPage} from './routes/MapPage';
import {Landing} from './routes/Landing';
const Legal=lazy(()=>import('./routes/PublicPages').then(m=>({default:m.Legal})));
const About=lazy(()=>import('./routes/PublicPages').then(m=>({default:m.About})));
const Roadmap=lazy(()=>import('./routes/PublicPages').then(m=>({default:m.Roadmap})));
const OfflineCheck=lazy(()=>import('./routes/PublicPages').then(m=>({default:m.OfflineCheck})));
const VolunteerGuide=lazy(()=>import('./routes/PublicPages').then(m=>({default:m.VolunteerGuide})));
const NotFound=lazy(()=>import('./routes/PublicPages').then(m=>({default:m.NotFound})));
const Analytics=lazy(()=>import('./routes/Operations').then(m=>({default:m.Analytics})));
const Incidents=lazy(()=>import('./routes/Operations').then(m=>({default:m.Incidents})));
const GroupDetail=lazy(()=>import('./routes/Operations').then(m=>({default:m.GroupDetail})));
const Posters=lazy(()=>import('./routes/Operations').then(m=>({default:m.Posters})));
const HealthScreen=lazy(()=>import('./features/health/HealthScreen').then(m=>({default:m.HealthScreen})));
const SOSScreen=lazy(()=>import('./features/sos/SOSScreen').then(m=>({default:m.SOSScreen})));
const FamilyLink=lazy(()=>import('./features/trail/FamilyLink').then(m=>({default:m.FamilyLink})));

import { LanguageProvider } from './lib/i18n/LanguageContext';
import { Header } from './components/Header';

export const App: React.FC = () => {
  return (
      <LanguageProvider>
        <BrowserRouter>
          <Header /><ErrorBoundary><Suspense fallback={<main className="page">Loading… / लोड हो रहा है…</main>}>
          <Routes>
            <Route path="/" element={<Login />} /><Route path="/login" element={<Login />} /><Route path="/guide" element={<Landing />} /><Route path="/map" element={<MapPage />} />
            <Route path="/register" element={<RegisterWizard />} />
            <Route path="/pass/:code" element={<PassView />} />
            <Route path="/trail/:code" element={<TrailView />} />
            <Route path="/scan/:code" element={<ScanScreen />} />
            <Route path="/health/:code" element={<HealthScreen />} />
            <Route path="/sos/:code" element={<SOSScreen />} />
            <Route path="/share/:token" element={<FamilyLink />} />
            <Route path="/volunteer" element={<StaffGate><VolunteerScan /></StaffGate>} />
            <Route path="/control" element={<StaffGate><ControlDashboard /></StaffGate>} />
            <Route path="/offline-map" element={<main className="page"><RoutePack/></main>}/>
            <Route path="/check-in" element={<ScanScreen/>}/>
            <Route path="/privacy" element={<Legal/>}/><Route path="/terms" element={<Legal/>}/>
            <Route path="/about" element={<About/>}/><Route path="/roadmap" element={<Roadmap/>}/>
            <Route path="/demo/offline-check" element={<OfflineCheck/>}/><Route path="/volunteer-guide" element={<VolunteerGuide/>}/>
            <Route path="/control/analytics" element={<StaffGate><Analytics/></StaffGate>}/>
            <Route path="/control/incidents" element={<StaffGate><Incidents/></StaffGate>}/>
            <Route path="/control/groups/:id" element={<StaffGate><GroupDetail/></StaffGate>}/>
            <Route path="/admin/posters" element={<StaffGate><Posters/></StaffGate>}/>
            <Route path="*" element={<NotFound/>}/>
          </Routes></Suspense></ErrorBoundary><Chrome/>
        </BrowserRouter>
      </LanguageProvider>
  );
};

export default App;

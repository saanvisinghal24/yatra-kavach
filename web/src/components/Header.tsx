import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from '../lib/i18n/LanguageContext';
import { db } from '../lib/db';
import { syncPendingCheckins } from '../lib/sync';
import { RefreshCw, Globe, Shield, Wifi, WifiOff } from 'lucide-react';

export const Header: React.FC = () => {
  const { t, language, toggleLanguage } = useTranslation();
  const location = useLocation();
  const [pendingCount, setPendingCount] = useState<number>(0);
  const [isOnline, setIsOnline] = useState<boolean>(navigator.onLine);
  const [syncing, setSyncing] = useState<boolean>(false);

  useEffect(() => {
    const updateStatus = async () => {
      const count = await db.checkins.where('status').equals('pending').count();
      setPendingCount(count);
    };

    updateStatus();
    const interval = setInterval(updateStatus, 3000);

    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      clearInterval(interval);
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const handleManualSync = async () => {
    setSyncing(true);
    try {
      await syncPendingCheckins();
      const count = await db.checkins.where('status').equals('pending').count();
      setPendingCount(count);
    } catch (e) {

    } finally {
      setSyncing(false);
    }
  };

  return (
    <header style={{ width: '100%', borderBottom: '1px solid var(--border-hairline)', background: 'var(--paper)' }}>
      {/* 2. Main Navigation Bar */}
      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: 'var(--space-2) var(--space-4)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
        
        {/* Brand */}
        <Link to="/" style={{ textDecoration: 'none', color: 'inherit', display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <div style={{ width: '32px', height: '32px', background: 'var(--deodar)', color: 'var(--paper)', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '3px' }}>
            <Shield size={20} />
          </div>
          <div>
            <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1.1rem', letterSpacing: '0.04em', color: 'var(--deodar)' }}>
              {t.appName}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--ink-2)', marginTop: '-2px' }}>
              {t.tagline}
            </div>
          </div>
        </Link>

        {/* Navigation Items */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', fontSize: '0.88rem' }}>
          <Link to="/map">Map</Link><Link to="/login">Sign in</Link>
          <Link 
            to="/register" 
            style={{ 
              textDecoration: 'none', 
              color: location.pathname === '/register' ? 'var(--accent)' : 'var(--ink)',
              fontWeight: location.pathname === '/register' ? 700 : 500,
              padding: '6px 8px'
            }}
          >
            {t.navRegister}
          </Link>
          <Link 
            to="/volunteer" 
            style={{ 
              textDecoration: 'none', 
              color: location.pathname === '/volunteer' ? 'var(--accent)' : 'var(--ink)',
              fontWeight: location.pathname === '/volunteer' ? 700 : 500,
              padding: '6px 8px'
            }}
          >
            {t.navVolunteer}
          </Link>
          <Link 
            to="/control" 
            style={{ 
              textDecoration: 'none', 
              color: location.pathname === '/control' ? 'var(--accent)' : 'var(--ink)',
              fontWeight: location.pathname === '/control' ? 700 : 500,
              padding: '6px 8px'
            }}
          >
            {t.navControl}
          </Link>
        </nav>

        {/* Right Controls: Sync & Language Toggle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          
          {/* Offline/Online Pill & Sync Button */}
          <button
            onClick={handleManualSync}
            disabled={syncing}
            aria-label="Sync offline check-ins"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 10px',
              fontSize: '0.78rem',
              background: pendingCount > 0 ? 'var(--accent)' : 'var(--paper-2)',
              transition: 'none',
              color: pendingCount > 0 ? '#FFFFFF' : 'var(--ink)',
              border: '1px solid var(--border-hairline)',
              borderRadius: '3px',
              cursor: 'pointer'
            }}
          >
            {isOnline ? <Wifi size={14} /> : <WifiOff size={14} />}
            <span>{pendingCount > 0 ? `${pendingCount} ${t.pendingSync}` : (isOnline ? t.online : t.offline)}</span>
            <RefreshCw size={12} className={syncing ? 'animate-spin' : ''} />
          </button>

          {/* Language Switcher */}
          <button
            onClick={toggleLanguage}
            aria-label={language === 'en' ? 'Switch interface language हिन्दी' : 'Switch interface language EN'}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '6px 12px',
              fontSize: '0.85rem',
              fontWeight: 600,
              background: 'var(--paper-2)',
              border: '1px solid var(--border-hairline)',
              borderRadius: '3px',
              cursor: 'pointer',
              color: 'var(--deodar)'
            }}
          >
            <Globe size={14} />
            <span>{language === 'en' ? 'हिन्दी' : 'EN'}</span>
          </button>

        </div>

      </div>
    </header>
  );
};

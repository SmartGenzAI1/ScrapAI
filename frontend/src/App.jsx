import React, { useState, useEffect } from 'react';
import './index.css';
import Dashboard from './components/Dashboard';
import CrawlerInput from './components/CrawlerInput';
import DataVault from './components/DataVault';
import AdvancedTerminal from './components/AdvancedTerminal';
import LiveFeed from './components/LiveFeed';
import { SpiderIcon, ActivityIcon, TargetIcon, DatabaseIcon, TerminalIcon, RadioIcon } from './components/Icons';

const API_BASE = import.meta.env.VITE_API_URL || '';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [stats, setStats] = useState({ pages: 0, queued: 0, chunks: 0, embeddings: 0, total: 0 });
  const [isOnline, setIsOnline] = useState(true);

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/stats`);
      if (res.ok) {
        const data = await res.json();
        setStats(data);
        setIsOnline(true);
      } else {
        setIsOnline(false);
      }
    } catch (e) {
      setIsOnline(false);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="app-layout">
      {/* Sleek Top Navigation Bar */}
      <header className="app-header">
        <div className="brand-container">
          <div className="brand-logo">
            <SpiderIcon size={20} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <span className="brand-text">ScrapAI</span>
              <span className="brand-badge">2.0 Core</span>
            </div>
          </div>
        </div>

        <nav className="nav-tabs">
          <button
            className={`nav-tab ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <ActivityIcon size={16} />
            <span>Telemetry</span>
          </button>
          <button
            className={`nav-tab ${activeTab === 'crawler' ? 'active' : ''}`}
            onClick={() => setActiveTab('crawler')}
          >
            <TargetIcon size={16} />
            <span>Crawler</span>
          </button>
          <button
            className={`nav-tab ${activeTab === 'vault' ? 'active' : ''}`}
            onClick={() => setActiveTab('vault')}
          >
            <DatabaseIcon size={16} />
            <span>Data Vault</span>
          </button>
          <button
            className={`nav-tab ${activeTab === 'terminal' ? 'active' : ''}`}
            onClick={() => setActiveTab('terminal')}
          >
            <TerminalIcon size={16} />
            <span>Terminal CLI</span>
          </button>
          <button
            className={`nav-tab ${activeTab === 'feed' ? 'active' : ''}`}
            onClick={() => setActiveTab('feed')}
          >
            <RadioIcon size={16} />
            <span>Live Feed</span>
          </button>
        </nav>

        <div className="header-meta">
          <div className="status-beacon">
            <div className={`beacon-dot ${!isOnline ? 'offline' : ''}`} style={{ backgroundColor: isOnline ? '#10b981' : '#f43f5e' }} />
            <span>{isOnline ? 'Engine Online • Zero-API' : 'Connecting...'}</span>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', fontSize: '0.8rem' }}>
            <span className="badge badge-blue">Vault: {stats.pages}</span>
            {stats.queued > 0 && <span className="badge badge-amber">Queue: {stats.queued}</span>}
          </div>
        </div>
      </header>

      {/* Main View Container */}
      <main className="main-container">
        {activeTab === 'dashboard' && <Dashboard onNavigate={(tab) => setActiveTab(tab)} />}
        {activeTab === 'crawler' && <CrawlerInput />}
        {activeTab === 'vault' && <DataVault />}
        {activeTab === 'terminal' && <AdvancedTerminal />}
        {activeTab === 'feed' && <LiveFeed />}
      </main>
    </div>
  );
}

export default App;

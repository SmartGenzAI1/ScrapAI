import React, { useEffect, useState } from 'react';
import { FileTextIcon, LayersIcon, CpuIcon, ClockIcon, ZapIcon, PlusIcon, ActivityIcon } from './Icons';

const API_BASE = import.meta.env.VITE_API_URL || '';

const Dashboard = ({ onNavigate }) => {
    const [stats, setStats] = useState({
        queued: 0,
        processing: 0,
        completed: 0,
        failed: 0,
        pages: 0,
        chunks: 0,
        embeddings: 0,
        domains: 0,
        searches: 0,
        total: 0
    });
    const [loading, setLoading] = useState(true);
    const [actionStatus, setActionStatus] = useState('');

    const fetchStats = async () => {
        try {
            const response = await fetch(`${API_BASE}/api/v1/stats`);
            if (response.ok) {
                const data = await response.json();
                setStats(data);
            }
        } catch (err) {
            console.error('Telemetry fetch failed:', err);
        } finally {
            setLoading(false);
        }
    };

    const triggerPipeline = async () => {
        setActionStatus('Executing pipeline cycle...');
        try {
            const res = await fetch(`${API_BASE}/api/v1/pipeline/run`, { method: 'POST' });
            if (res.ok) {
                const data = await res.json();
                setActionStatus(`Pipeline executed: ${data.step_activity.crawled} crawled, ${data.step_activity.chunked} chunked, ${data.step_activity.embedded} embedded`);
                fetchStats();
            }
        } catch (err) {
            setActionStatus(`Error: ${err.message}`);
        } finally {
            setTimeout(() => setActionStatus(''), 4000);
        }
    };

    useEffect(() => {
        fetchStats();
        const interval = setInterval(fetchStats, 3000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {/* Header Banner */}
            <div className="card-panel" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                <div>
                    <h1 style={{ fontSize: '1.5rem', fontWeight: 700, letterSpacing: '-0.02em', color: 'var(--text-main)' }}>
                        System Telemetry & Health
                    </h1>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.2rem' }}>
                        Autonomous ingestion pipeline monitoring, dense vector indices, and search activity.
                    </p>
                </div>
                <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                    {actionStatus && <span style={{ color: 'var(--accent-primary)', fontSize: '0.85rem', fontWeight: 500 }}>{actionStatus}</span>}
                    <button className="btn btn-secondary" onClick={triggerPipeline}>
                        <ZapIcon size={16} color="var(--accent-primary)" />
                        <span>Run Ingestion Cycle</span>
                    </button>
                    <button className="btn btn-primary" onClick={() => onNavigate && onNavigate('crawler')}>
                        <PlusIcon size={16} color="#ffffff" />
                        <span>New Crawl Target</span>
                    </button>
                </div>
            </div>

            {/* Primary Stat Metrics Grid */}
            <div className="grid-12">
                <div className="col-3 card-inner stat-card">
                    <div className="stat-header">
                        <span className="stat-title">Indexed Documents</span>
                        <div className="stat-icon" style={{ background: 'rgba(59, 130, 246, 0.12)', color: 'var(--accent-primary)' }}>
                            <FileTextIcon size={16} />
                        </div>
                    </div>
                    <div className="stat-value">{loading ? '...' : stats.pages}</div>
                    <div className="stat-subtext">Clean extracted web pages in Vault</div>
                </div>

                <div className="col-3 card-inner stat-card">
                    <div className="stat-header">
                        <span className="stat-title">Semantic Chunks</span>
                        <div className="stat-icon" style={{ background: 'rgba(99, 102, 241, 0.12)', color: 'var(--accent-indigo)' }}>
                            <LayersIcon size={16} />
                        </div>
                    </div>
                    <div className="stat-value">{loading ? '...' : stats.chunks}</div>
                    <div className="stat-subtext">Sentence-bounded context units</div>
                </div>

                <div className="col-3 card-inner stat-card">
                    <div className="stat-header">
                        <span className="stat-title">Vector Embeddings</span>
                        <div className="stat-icon" style={{ background: 'rgba(16, 185, 129, 0.12)', color: 'var(--accent-emerald)' }}>
                            <CpuIcon size={16} />
                        </div>
                    </div>
                    <div className="stat-value">{loading ? '...' : stats.embeddings}</div>
                    <div className="stat-subtext">100% Offline Dense Vector Points</div>
                </div>

                <div className="col-3 card-inner stat-card">
                    <div className="stat-header">
                        <span className="stat-title">Active Crawl Queue</span>
                        <div className="stat-icon" style={{ background: 'rgba(245, 158, 11, 0.12)', color: 'var(--accent-amber)' }}>
                            <ClockIcon size={16} />
                        </div>
                    </div>
                    <div className="stat-value">{loading ? '...' : stats.queued}</div>
                    <div className="stat-subtext">Targets awaiting background fetch</div>
                </div>
            </div>

            {/* Detailed System Breakdown */}
            <div className="grid-12">
                {/* Crawl Pipeline Breakdown */}
                <div className="col-6 card-panel">
                    <h2 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '1.25rem' }}>
                        Crawl Execution Status
                    </h2>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Successfully Completed</span>
                            <span className="badge badge-emerald">{stats.completed} processed</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Currently Processing</span>
                            <span className="badge badge-blue">{stats.processing} active</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Failed / Blocked Targets</span>
                            <span className="badge badge-rose">{stats.failed} failed</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Unique Domains Tracked</span>
                            <span style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '0.9rem' }}>{stats.domains} domains</span>
                        </div>
                    </div>
                </div>

                {/* Search & Architecture Specs */}
                <div className="col-6 card-panel">
                    <h2 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '1.25rem' }}>
                        Engine Specifications
                    </h2>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Search Queries Handled</span>
                            <span style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '0.9rem' }}>{stats.searches}</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Vector Embedding Mode</span>
                            <span className="badge badge-emerald">Local Zero-API Subword Vectorizer</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Ranking Engine</span>
                            <span style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '0.9rem' }}>Hybrid BM25 + Dense Cosine</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Reasoning & QA</span>
                            <span className="badge badge-blue">No-LLM Extractive Synthesizer</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;

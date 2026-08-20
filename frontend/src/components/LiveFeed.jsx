import React, { useState, useEffect, useRef } from 'react';
import { RadioIcon, TrashIcon } from './Icons';

const API_BASE = import.meta.env.VITE_API_URL || '';

const LiveFeed = () => {
    const [logs, setLogs] = useState([
        { time: new Date().toLocaleTimeString(), type: 'info', msg: 'Real-time telemetry stream connected. Local Zero-API engine active.' }
    ]);
    const endRef = useRef(null);

    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    useEffect(() => {
        let prevStats = { queued: 0, pages: 0, chunks: 0 };
        const fetchStats = async () => {
            try {
                const response = await fetch(`${API_BASE}/api/v1/stats`);
                if (response.ok) {
                    const data = await response.json();
                    const now = new Date().toLocaleTimeString();

                    if (data.pages > prevStats.pages) {
                        setLogs(p => [...p, { time: now, type: 'success', msg: `[INGESTION] Indexed +${data.pages - prevStats.pages} new page(s) into Data Vault (Total: ${data.pages}).` }]);
                    }
                    if (data.chunks > prevStats.chunks) {
                        setLogs(p => [...p, { time: now, type: 'info', msg: `[CHUNKER] Sliced +${data.chunks - prevStats.chunks} text chunk(s) into sentence boundaries.` }]);
                    }
                    if (data.queued > 0 && data.queued !== prevStats.queued) {
                        setLogs(p => [...p, { time: now, type: 'warning', msg: `[QUEUE] ${data.queued} target(s) actively queued for processing.` }]);
                    }
                    prevStats = data;
                }
            } catch {}
        };

        fetchStats();
        const interval = setInterval(fetchStats, 3000);
        return () => clearInterval(interval);
    }, []);

    const clearFeed = () => {
        setLogs([{ time: new Date().toLocaleTimeString(), type: 'info', msg: 'Feed stream cleared.' }]);
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div className="card-panel" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <RadioIcon size={20} color="var(--accent-primary)" />
                        <span>Real-Time Telemetry & Event Stream</span>
                    </h2>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '0.2rem' }}>
                        Live background supervisor stream tracking autonomous crawlers, chunkers, and embedding workers.
                    </p>
                </div>
                <button className="btn btn-secondary btn-sm" onClick={clearFeed}>
                    <TrashIcon size={14} />
                    <span>Clear Stream</span>
                </button>
            </div>

            <div className="card-panel" style={{ padding: '1.25rem', height: '520px', overflowY: 'auto', background: 'var(--bg-input)' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem', fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>
                    {logs.map((log, i) => (
                        <div key={i} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
                            <span style={{ color: 'var(--text-dim)', minWidth: '85px', fontSize: '0.8rem' }}>[{log.time}]</span>
                            <span style={{
                                color: log.type === 'error' ? 'var(--accent-rose)' : log.type === 'success' ? 'var(--accent-emerald)' : log.type === 'warning' ? 'var(--accent-amber)' : 'var(--accent-primary)',
                                flex: 1,
                                lineHeight: 1.4
                            }}>
                                {log.msg}
                            </span>
                        </div>
                    ))}
                    <div ref={endRef} />
                </div>
            </div>
        </div>
    );
};

export default LiveFeed;

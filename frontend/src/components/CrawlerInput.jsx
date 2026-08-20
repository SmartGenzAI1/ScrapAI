import React, { useState, useEffect } from 'react';
import { PlusIcon, ZapIcon, RefreshIcon, TrashIcon, CheckCircleIcon, XIcon, TargetIcon } from './Icons';

const API_BASE = import.meta.env.VITE_API_URL || '';

const CrawlerInput = () => {
    const [urlInput, setUrlInput] = useState('');
    const [urls, setUrls] = useState([]);
    const [maxDepth, setMaxDepth] = useState(1);
    const [status, setStatus] = useState({ type: '', msg: '' });
    const [loading, setLoading] = useState(false);
    const [queueItems, setQueueItems] = useState([]);

    const fetchQueue = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/v1/queue?limit=50`);
            if (res.ok) {
                const data = await res.json();
                setQueueItems(data);
            }
        } catch (e) {}
    };

    useEffect(() => {
        fetchQueue();
        const int = setInterval(fetchQueue, 3000);
        return () => clearInterval(int);
    }, []);

    const handleAddUrl = (e) => {
        e?.preventDefault();
        if (!urlInput.trim()) return;

        let formatted = urlInput.trim();
        if (!formatted.startsWith('http://') && !formatted.startsWith('https://')) {
            formatted = 'https://' + formatted;
        }

        try {
            new URL(formatted);
            if (!urls.includes(formatted)) {
                setUrls([...urls, formatted]);
                setUrlInput('');
                setStatus({ type: '', msg: '' });
            } else {
                setStatus({ type: 'amber', msg: 'Target URL is already in the batch staging list.' });
            }
        } catch {
            setStatus({ type: 'rose', msg: 'Please enter a valid HTTP/HTTPS URL format.' });
        }
    };

    const submitQueue = async () => {
        if (urls.length === 0) return;
        setLoading(true);
        setStatus({ type: 'blue', msg: 'Enqueuing targets into autonomous crawler engine...' });

        try {
            const response = await fetch(`${API_BASE}/api/v1/crawl`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ urls, max_depth: maxDepth }),
            });

            if (response.ok) {
                const data = await response.json();
                setStatus({ type: 'emerald', msg: `Successfully queued ${urls.length} target(s).` });
                setUrls([]);
                fetchQueue();
            } else {
                setStatus({ type: 'rose', msg: 'Engine rejected the target batch.' });
            }
        } catch (err) {
            setStatus({ type: 'rose', msg: `Connection error: ${err.message}` });
        } finally {
            setLoading(false);
            setTimeout(() => setStatus({ type: '', msg: '' }), 5000);
        }
    };

    const handleDirectCrawl = async (targetUrl) => {
        setLoading(true);
        setStatus({ type: 'blue', msg: `Executing immediate scrape on ${targetUrl}...` });
        try {
            const res = await fetch(`${API_BASE}/api/v1/crawl/direct`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: targetUrl })
            });
            if (res.ok) {
                const data = await res.json();
                setStatus({ type: 'emerald', msg: `Direct scrape complete: "${data.title || targetUrl}" (${data.word_count || 0} words extracted)` });
                fetchQueue();
            } else {
                setStatus({ type: 'rose', msg: 'Direct scrape failed or blocked by robots.txt.' });
            }
        } catch (e) {
            setStatus({ type: 'rose', msg: `Error: ${e.message}` });
        } finally {
            setLoading(false);
            setTimeout(() => setStatus({ type: '', msg: '' }), 6000);
        }
    };

    const handleClearQueue = async () => {
        if (!window.confirm('Clear all pending targets in the queue?')) return;
        try {
            await fetch(`${API_BASE}/api/v1/queue/clear`, { method: 'POST' });
            fetchQueue();
        } catch (e) {}
    };

    return (
        <div className="grid-12">
            {/* Target Input Form */}
            <div className="col-5 card-panel">
                <h2 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '0.35rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <TargetIcon size={18} color="var(--accent-primary)" />
                    <span>Target Acquisition</span>
                </h2>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '1.5rem' }}>
                    Inject URLs for autonomous extraction, robots.txt check, link discovery, and indexing.
                </p>

                <form onSubmit={handleAddUrl} style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem' }}>
                    <input
                        type="text"
                        className="input-base"
                        placeholder="https://news.ycombinator.com"
                        value={urlInput}
                        onChange={(e) => setUrlInput(e.target.value)}
                        disabled={loading}
                    />
                    <button type="submit" className="btn btn-secondary" disabled={loading}>
                        <PlusIcon size={16} />
                        <span>Add</span>
                    </button>
                </form>

                {/* Depth Selection Controls */}
                <div style={{ marginBottom: '1.5rem' }}>
                    <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.5rem' }}>
                        Crawl Traversal Depth:
                    </label>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                        {[
                            { value: 0, label: 'Single Page' },
                            { value: 1, label: '+1 Hop Links (Recommended)' },
                            { value: 2, label: '2-Hop Recursive' }
                        ].map((opt) => (
                            <button
                                key={opt.value}
                                type="button"
                                className={`btn btn-sm ${maxDepth === opt.value ? 'btn-primary' : 'btn-secondary'}`}
                                onClick={() => setMaxDepth(opt.value)}
                            >
                                {opt.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Feedback status banner */}
                {status.msg && (
                    <div style={{
                        padding: '0.75rem 1rem',
                        borderRadius: 'var(--radius-sm)',
                        background: status.type === 'emerald' ? 'var(--accent-emerald-bg)' : status.type === 'rose' ? 'var(--accent-rose-bg)' : 'rgba(59, 130, 246, 0.1)',
                        color: status.type === 'emerald' ? 'var(--accent-emerald)' : status.type === 'rose' ? 'var(--accent-rose)' : 'var(--accent-primary)',
                        border: `1px solid ${status.type === 'emerald' ? 'rgba(16, 185, 129, 0.2)' : status.type === 'rose' ? 'rgba(244, 63, 94, 0.2)' : 'rgba(59, 130, 246, 0.2)'}`,
                        fontSize: '0.85rem',
                        marginBottom: '1.25rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem'
                    }}>
                        {status.type === 'emerald' ? <CheckCircleIcon size={16} /> : <ZapIcon size={16} />}
                        <span>{status.msg}</span>
                    </div>
                )}

                {/* Staged Batch List */}
                <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                        <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                            Staged Batch ({urls.length})
                        </span>
                        {urls.length > 0 && (
                            <button className="btn btn-primary btn-sm" onClick={submitQueue} disabled={loading}>
                                <ZapIcon size={14} color="#ffffff" />
                                <span>Execute Batch</span>
                            </button>
                        )}
                    </div>

                    {urls.length === 0 ? (
                        <div style={{ textAlign: 'center', padding: '1.5rem 0', color: 'var(--text-dim)', fontSize: '0.85rem' }}>
                            No URLs staged. Enter a target URL above to stage.
                        </div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', maxHeight: '200px', overflowY: 'auto' }}>
                            {urls.map((u, i) => (
                                <div key={i} className="card-inner" style={{ padding: '0.6rem 0.85rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span style={{ fontSize: '0.85rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '65%' }}>
                                        {u}
                                    </span>
                                    <div style={{ display: 'flex', gap: '0.4rem' }}>
                                        <button
                                            className="btn btn-secondary btn-sm"
                                            onClick={() => handleDirectCrawl(u)}
                                            style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}
                                        >
                                            <ZapIcon size={12} color="var(--accent-primary)" />
                                            <span>Scrape</span>
                                        </button>
                                        <button
                                            style={{ background: 'transparent', border: 'none', color: 'var(--accent-rose)', cursor: 'pointer', padding: '0 0.3rem', display: 'flex', alignItems: 'center' }}
                                            onClick={() => setUrls(urls.filter((_, idx) => idx !== i))}
                                        >
                                            <XIcon size={14} />
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Live Queue Monitor Table */}
            <div className="col-7 card-panel">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
                    <div>
                        <h2 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-main)' }}>
                            Active Ingestion Queue
                        </h2>
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                            {queueItems.length} total entries tracked
                        </span>
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button className="btn btn-secondary btn-sm" onClick={fetchQueue}>
                            <RefreshIcon size={14} />
                            <span>Refresh</span>
                        </button>
                        {queueItems.length > 0 && (
                            <button className="btn btn-secondary btn-sm" style={{ color: 'var(--accent-rose)' }} onClick={handleClearQueue}>
                                <TrashIcon size={14} />
                                <span>Clear</span>
                            </button>
                        )}
                    </div>
                </div>

                {queueItems.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: '3rem 0', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                        Queue is idle. Add targets on the left to start crawling.
                    </div>
                ) : (
                    <div className="table-container" style={{ maxHeight: '450px', overflowY: 'auto' }}>
                        <table className="clean-table">
                            <thead>
                                <tr>
                                    <th>Target URL</th>
                                    <th>Depth</th>
                                    <th>Status</th>
                                    <th>Scheduled</th>
                                </tr>
                            </thead>
                            <tbody>
                                {queueItems.map((item) => (
                                    <tr key={item.id}>
                                        <td style={{ maxWidth: '280px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                            <span style={{ fontWeight: 500 }}>{item.url}</span>
                                            {item.error_message && (
                                                <div style={{ fontSize: '0.75rem', color: 'var(--accent-rose)' }}>
                                                    {item.error_message}
                                                </div>
                                            )}
                                        </td>
                                        <td style={{ color: 'var(--text-secondary)' }}>
                                            d={item.depth}
                                        </td>
                                        <td>
                                            <span className={`badge ${
                                                item.status === 'completed' ? 'badge-emerald' :
                                                item.status === 'processing' ? 'badge-blue' :
                                                item.status === 'failed' ? 'badge-rose' : 'badge-amber'
                                            }`}>
                                                {item.status}
                                            </span>
                                        </td>
                                        <td style={{ color: 'var(--text-dim)', fontSize: '0.8rem' }}>
                                            {item.scheduled_at ? new Date(item.scheduled_at).toLocaleTimeString() : '–'}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
};

export default CrawlerInput;

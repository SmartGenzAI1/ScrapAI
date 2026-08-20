import React, { useState, useEffect } from 'react';
import { SearchIcon, CpuIcon, DownloadIcon, ExternalLinkIcon, TrashIcon, RefreshIcon, XIcon, FileTextIcon, LayersIcon, ZapIcon } from './Icons';

const API_BASE = import.meta.env.VITE_API_URL || '';

const DataVault = () => {
    const [query, setQuery] = useState('');
    const [mode, setMode] = useState('search'); // 'search' or 'qa'
    const [results, setResults] = useState([]);
    const [answerData, setAnswerData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [hasSearched, setHasSearched] = useState(false);
    const [inspectedDoc, setInspectedDoc] = useState(null);
    const [inspectTab, setInspectTab] = useState('overview'); // 'overview', 'content', 'chunks'

    const fetchInitialData = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE}/api/v1/search?q=&limit=24`);
            if (res.ok) {
                const data = await res.json();
                setResults(data);
            }
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchInitialData();
    }, []);

    const handleSearch = async (e) => {
        e?.preventDefault();
        if (!query.trim()) {
            fetchInitialData();
            return;
        }

        setLoading(true);
        setHasSearched(true);

        if (mode === 'qa') {
            try {
                const res = await fetch(`${API_BASE}/api/v1/query/answer`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query, limit: 10 })
                });
                if (res.ok) {
                    const data = await res.json();
                    setAnswerData(data);
                    if (data.results) setResults(data.results);
                }
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        } else {
            setAnswerData(null);
            try {
                const res = await fetch(`${API_BASE}/api/v1/search?q=${encodeURIComponent(query)}&limit=20`);
                if (res.ok) {
                    const data = await res.json();
                    setResults(data);
                }
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        }
    };

    const inspectDocument = async (pageId) => {
        try {
            const res = await fetch(`${API_BASE}/api/v1/pages/${pageId}`);
            if (res.ok) {
                const data = await res.json();
                setInspectedDoc(data);
                setInspectTab('overview');
            }
        } catch (e) {
            console.error(e);
        }
    };

    const deleteDocument = async (pageId) => {
        if (!window.confirm('Delete this record and all associated vector chunks from the Vault?')) return;
        try {
            const res = await fetch(`${API_BASE}/api/v1/pages/${pageId}`, { method: 'DELETE' });
            if (res.ok) {
                setResults(results.filter(r => (r.id !== pageId && r.page_id !== pageId)));
                if (inspectedDoc?.id === pageId) setInspectedDoc(null);
            }
        } catch (e) {
            console.error(e);
        }
    };

    const handleExport = (fmt) => {
        window.open(`${API_BASE}/api/v1/export?format=${fmt}`, '_blank');
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {/* Search Header Panel */}
            <div className="card-panel" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', padding: '2rem 1.5rem' }}>
                <h1 style={{ fontSize: '1.6rem', fontWeight: 700, letterSpacing: '-0.02em', color: 'var(--text-main)', marginBottom: '0.4rem' }}>
                    Knowledge Vault & Semantic Search
                </h1>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', maxWidth: '650px', marginBottom: '1.5rem' }}>
                    Multi-signal hybrid retrieval blending local dense vector embeddings with Okapi BM25 keyword ranking.
                </p>

                {/* Mode Selector */}
                <div style={{ display: 'flex', background: 'var(--bg-input)', padding: '3px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', marginBottom: '1.25rem', gap: '3px' }}>
                    <button
                        type="button"
                        className={`nav-tab ${mode === 'search' ? 'active' : ''}`}
                        onClick={() => setMode('search')}
                        style={{ padding: '0.4rem 1rem' }}
                    >
                        <ZapIcon size={15} color={mode === 'search' ? 'var(--accent-primary)' : 'currentColor'} />
                        <span>Hybrid Search</span>
                    </button>
                    <button
                        type="button"
                        className={`nav-tab ${mode === 'qa' ? 'active' : ''}`}
                        onClick={() => setMode('qa')}
                        style={{ padding: '0.4rem 1rem' }}
                    >
                        <CpuIcon size={15} color={mode === 'qa' ? 'var(--accent-primary)' : 'currentColor'} />
                        <span>Ask Extractive QA</span>
                    </button>
                </div>

                {/* Unified Search Input Form */}
                <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.75rem', width: '100%', maxWidth: '780px' }}>
                    <input
                        type="text"
                        className="input-base"
                        placeholder={mode === 'qa' ? "Ask a question (e.g. 'What is the system architecture?')..." : "Search indexed documents, keywords, or topics..."}
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        style={{ fontSize: '0.95rem', padding: '0.85rem 1.25rem' }}
                    />
                    <button type="submit" className="btn btn-primary" disabled={loading} style={{ minWidth: '130px' }}>
                        {loading ? (
                            <span>Processing...</span>
                        ) : mode === 'qa' ? (
                            <>
                                <CpuIcon size={16} color="#ffffff" />
                                <span>Ask QA</span>
                            </>
                        ) : (
                            <>
                                <SearchIcon size={16} color="#ffffff" />
                                <span>Search</span>
                            </>
                        )}
                    </button>
                </form>

                {/* Actions & Export Row */}
                <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.25rem', alignItems: 'center' }}>
                    <button className="btn btn-secondary btn-sm" onClick={() => handleExport('json')}>
                        <DownloadIcon size={14} />
                        <span>Export JSON</span>
                    </button>
                    <button className="btn btn-secondary btn-sm" onClick={() => handleExport('csv')}>
                        <DownloadIcon size={14} />
                        <span>Export CSV</span>
                    </button>
                    <button className="btn btn-secondary btn-sm" onClick={fetchInitialData}>
                        <RefreshIcon size={14} />
                        <span>Reset / Refresh</span>
                    </button>
                </div>
            </div>

            {/* Extractive AI Answer Synthesizer Panel */}
            {answerData && (
                <div className="ai-answer-box">
                    <div className="ai-answer-header">
                        <div className="ai-answer-title">
                            <CpuIcon size={18} color="var(--accent-primary)" />
                            <span>Synthesized Answer</span>
                            <span className="badge badge-emerald" style={{ marginLeft: '0.5rem' }}>
                                {Math.round(answerData.confidence * 100)}% Confidence
                            </span>
                        </div>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Zero-API Extractive Reasoning</span>
                    </div>

                    <p style={{ color: 'var(--text-main)', fontSize: '0.98rem', lineHeight: 1.7, marginBottom: '1.25rem' }}>
                        {answerData.answer}
                    </p>

                    {answerData.sources && answerData.sources.length > 0 && (
                        <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 500 }}>Verified Citations:</span>
                            {answerData.sources.map((s, idx) => (
                                <a
                                    key={idx}
                                    href={s.url}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="citation-chip"
                                >
                                    [{s.citation_id}] {s.title || s.url}
                                    <ExternalLinkIcon size={11} style={{ marginLeft: '3px' }} />
                                </a>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* Document Cards Grid */}
            <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', padding: '0 0.25rem' }}>
                    <h2 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-main)' }}>
                        Retrieved Documents ({results.length})
                    </h2>
                </div>

                {results.length === 0 ? (
                    <div className="card-panel" style={{ padding: '3.5rem', textAlign: 'center' }}>
                        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                            {hasSearched ? 'No matching documents found in Vault.' : 'Knowledge Vault is empty. Ingest targets using the Crawler tab.'}
                        </p>
                    </div>
                ) : (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(370px, 1fr))', gap: '1.25rem' }}>
                        {results.map((item, index) => {
                            const pageId = item.id || item.page_id;
                            return (
                                <div key={index} className="card-inner" style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.75rem' }}>
                                        <div style={{ flex: 1, minWidth: 0 }}>
                                            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-main)', margin: '0 0 0.25rem 0', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                                {item.title || 'Untitled Document'}
                                            </h3>
                                            <a href={item.url} target="_blank" rel="noreferrer" style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '3px' }}>
                                                <span>{item.domain || item.url}</span>
                                                <ExternalLinkIcon size={10} />
                                            </a>
                                        </div>
                                        {item.score !== undefined && (
                                            <span className="badge badge-emerald" style={{ flexShrink: 0 }}>
                                                {typeof item.score === 'number' ? (item.score * 100).toFixed(0) + '%' : item.score}
                                            </span>
                                        )}
                                    </div>

                                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', lineHeight: 1.5, flex: 1, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical' }}>
                                        {item.snippet || item.content || 'No text snippet available.'}
                                    </p>

                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto', paddingTop: '0.75rem', borderTop: '1px solid var(--border-subtle)' }}>
                                        <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                                            HASH: {(item.hash || item.content_hash || '').substring(0, 8)}
                                        </span>
                                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                                            <button
                                                className="btn btn-secondary btn-sm"
                                                onClick={() => inspectDocument(pageId)}
                                            >
                                                Inspect
                                            </button>
                                            <button
                                                className="btn btn-secondary btn-sm"
                                                style={{ color: 'var(--accent-rose)', padding: '0.35rem 0.6rem' }}
                                                onClick={() => deleteDocument(pageId)}
                                                title="Delete from Vault"
                                            >
                                                <TrashIcon size={14} />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>

            {/* Document Inspection Modal Dialog */}
            {inspectedDoc && (
                <div className="modal-overlay" onClick={() => setInspectedDoc(null)}>
                    <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <div>
                                <h3 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-main)' }}>
                                    {inspectedDoc.title || 'Document Inspection'}
                                </h3>
                                <a href={inspectedDoc.url} target="_blank" rel="noreferrer" style={{ fontSize: '0.8rem', color: 'var(--accent-primary)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                    <span>{inspectedDoc.url}</span>
                                    <ExternalLinkIcon size={12} />
                                </a>
                            </div>
                            <button className="modal-close" onClick={() => setInspectedDoc(null)}>
                                <XIcon size={20} />
                            </button>
                        </div>

                        {/* Modal Tabs */}
                        <div style={{ display: 'flex', borderBottom: '1px solid var(--border-subtle)', padding: '0 1.75rem', background: 'var(--bg-card)', gap: '1rem' }}>
                            <button
                                className={`nav-tab ${inspectTab === 'overview' ? 'active' : ''}`}
                                onClick={() => setInspectTab('overview')}
                                style={{ borderRadius: '0', borderBottom: inspectTab === 'overview' ? '2px solid var(--accent-primary)' : 'none' }}
                            >
                                <FileTextIcon size={14} />
                                <span>Metadata</span>
                            </button>
                            <button
                                className={`nav-tab ${inspectTab === 'content' ? 'active' : ''}`}
                                onClick={() => setInspectTab('content')}
                                style={{ borderRadius: '0', borderBottom: inspectTab === 'content' ? '2px solid var(--accent-primary)' : 'none' }}
                            >
                                <FileTextIcon size={14} />
                                <span>Extracted Text</span>
                            </button>
                            <button
                                className={`nav-tab ${inspectTab === 'chunks' ? 'active' : ''}`}
                                onClick={() => setInspectTab('chunks')}
                                style={{ borderRadius: '0', borderBottom: inspectTab === 'chunks' ? '2px solid var(--accent-primary)' : 'none' }}
                            >
                                <LayersIcon size={14} />
                                <span>Chunks ({inspectedDoc.chunks?.length || 0})</span>
                            </button>
                        </div>

                        <div className="modal-body">
                            {inspectTab === 'overview' && (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', fontSize: '0.875rem' }}>
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
                                        <div className="card-inner">
                                            <span style={{ color: 'var(--text-secondary)', display: 'block', fontSize: '0.8rem' }}>Domain</span>
                                            <span style={{ fontWeight: 600 }}>{inspectedDoc.domain}</span>
                                        </div>
                                        <div className="card-inner">
                                            <span style={{ color: 'var(--text-secondary)', display: 'block', fontSize: '0.8rem' }}>Word Count</span>
                                            <span style={{ fontWeight: 600 }}>{inspectedDoc.word_count} words</span>
                                        </div>
                                        <div className="card-inner">
                                            <span style={{ color: 'var(--text-secondary)', display: 'block', fontSize: '0.8rem' }}>Crawl Timestamp</span>
                                            <span style={{ fontWeight: 600 }}>{inspectedDoc.crawl_time}</span>
                                        </div>
                                        <div className="card-inner">
                                            <span style={{ color: 'var(--text-secondary)', display: 'block', fontSize: '0.8rem' }}>Content SHA-256</span>
                                            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>{inspectedDoc.hash}</span>
                                        </div>
                                    </div>
                                    {inspectedDoc.meta_description && (
                                        <div>
                                            <span style={{ color: 'var(--text-secondary)', display: 'block', marginBottom: '0.35rem', fontSize: '0.8rem' }}>Meta Description</span>
                                            <p style={{ color: 'var(--text-main)', background: 'var(--bg-card)', padding: '0.75rem', borderRadius: 'var(--radius-sm)' }}>
                                                {inspectedDoc.meta_description}
                                            </p>
                                        </div>
                                    )}
                                </div>
                            )}

                            {inspectTab === 'content' && (
                                <div style={{ background: 'var(--bg-input)', padding: '1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)', whiteSpace: 'pre-wrap', fontSize: '0.85rem', color: 'var(--text-main)', maxHeight: '350px', overflowY: 'auto', lineHeight: 1.6 }}>
                                    {inspectedDoc.content}
                                </div>
                            )}

                            {inspectTab === 'chunks' && (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                    {inspectedDoc.chunks?.map((c) => (
                                        <div key={c.id} className="card-inner" style={{ fontSize: '0.85rem' }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                                                <span style={{ fontWeight: 600, color: 'var(--accent-primary)' }}>Chunk #{c.index + 1}</span>
                                                <span style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>ID: {c.id}</span>
                                            </div>
                                            <p style={{ color: 'var(--text-main)', lineHeight: 1.5 }}>{c.text}</p>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default DataVault;

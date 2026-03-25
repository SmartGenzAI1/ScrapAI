import React, { useState } from 'react';

const CrawlerInput = () => {
    const [urlInput, setUrlInput] = useState('');
    const [urls, setUrls] = useState([]);
    const [status, setStatus] = useState('');
    const [loading, setLoading] = useState(false);

    const handleAddUrl = (e) => {
        e.preventDefault();
        if (!urlInput) return;

        // Simple validation
        try {
            new URL(urlInput);
            if (!urls.includes(urlInput)) {
                setUrls([...urls, urlInput]);
                setUrlInput('');
            } else {
                setStatus('URL already in queue');
                setTimeout(() => setStatus(''), 3000);
            }
        } catch {
            setStatus('Please enter a valid URL (starting with http:// or https://)');
            setTimeout(() => setStatus(''), 3000);
        }
    };

    const submitQueue = async () => {
        if (urls.length === 0) return;
        setLoading(true);
        setStatus('Transmitting targets to execution engine...');

        try {
            const response = await fetch('http://localhost:8000/api/v1/crawl', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ urls }),
            });

            if (response.ok) {
                const data = await response.json();
                setStatus(`Success: ${data.message}`);
                setUrls([]);
            } else {
                setStatus('Engine response: Target ingestion failed.');
            }
        } catch (err) {
            console.error(err);
            setStatus('Connection lost: Unable to reach target execution engine.');
        } finally {
            setLoading(false);
            setTimeout(() => setStatus(''), 5000);
        }
    };

    const removeUrl = (index) => {
        setUrls(urls.filter((_, i) => i !== index));
    };

    return (
        <div className="grid-dashboard animate-fade-in" style={{ gap: '2rem' }}>

            {/* Input Section */}
            <div className="col-span-12 glass-panel" style={{ padding: '2.5rem' }}>
                <h2 className="text-h2 text-gradient-cyan" style={{ marginBottom: '0.5rem' }}>Target Acquisition</h2>
                <p className="text-secondary" style={{ marginBottom: '2rem' }}>Input URLs to queue for extraction and analysis.</p>

                <form onSubmit={handleAddUrl} style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem' }}>
                    <input
                        type="text"
                        className="input-glass"
                        placeholder="https://example.com"
                        value={urlInput}
                        onChange={(e) => setUrlInput(e.target.value)}
                        disabled={loading}
                    />
                    <button type="submit" className="btn btn-secondary" disabled={loading}>
                        Add Target
                    </button>
                </form>

                {status && (
                    <div className="animate-fade-in" style={{
                        padding: '1rem',
                        borderRadius: '8px',
                        background: status.includes('Success') ? 'rgba(0, 255, 136, 0.1)' : 'rgba(255, 51, 102, 0.1)',
                        color: status.includes('Success') ? '#00ff88' : '#ff3366',
                        border: `1px solid ${status.includes('Success') ? 'rgba(0, 255, 136, 0.2)' : 'rgba(255, 51, 102, 0.2)'}`,
                        marginBottom: '1rem'
                    }}>
                        {status}
                    </div>
                )}
            </div>

            {/* Queue Section */}
            <div className="col-span-12 glass-panel" style={{ padding: '2.5rem', minHeight: '300px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                    <h3 className="text-h3">Awaiting Transmission ({urls.length})</h3>
                    <button
                        className="btn btn-primary"
                        onClick={submitQueue}
                        disabled={urls.length === 0 || loading}
                    >
                        {loading ? 'Transmitting...' : 'Execute Targets'}
                    </button>
                </div>

                {urls.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: '3rem 0', color: 'var(--text-muted)' }}>
                        No targets acquired yet.
                    </div>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                        {urls.map((url, index) => (
                            <div key={index} className="glass-card animate-fade-in" style={{ padding: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.01)' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', overflow: 'hidden' }}>
                                    <span style={{ color: 'var(--accent-cyan)', fontWeight: 'bold' }}>{(index + 1).toString().padStart(2, '0')}</span>
                                    <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', color: 'var(--text-primary)' }}>{url}</span>
                                </div>
                                <button
                                    style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1.2rem', padding: '0 0.5rem' }}
                                    onClick={() => removeUrl(index)}
                                    disabled={loading}
                                >
                                    &times;
                                </button>
                            </div>
                        ))}
                    </div>
                )}
            </div>

        </div>
    );
};

export default CrawlerInput;

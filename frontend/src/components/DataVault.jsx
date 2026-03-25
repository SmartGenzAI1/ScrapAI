import React, { useState, useEffect } from 'react';

const DataVault = () => {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [hasSearched, setHasSearched] = useState(false);

    const fetchInitialData = async () => {
        setLoading(true);
        try {
            // Empty query gets all data in this simple backend
            const response = await fetch('http://localhost:8000/api/v1/search?q=');
            if (response.ok) {
                const data = await response.json();
                setResults(data);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchInitialData();
    }, []);

    const handleSearch = async (e) => {
        e.preventDefault();
        setLoading(true);
        setHasSearched(true);

        try {
            const response = await fetch(`http://localhost:8000/api/v1/search?q=${encodeURIComponent(query)}`);
            if (response.ok) {
                const data = await response.json();
                setResults(data);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="grid-dashboard animate-fade-in" style={{ gap: '2rem' }}>

            {/* Search Bar */}
            <div className="col-span-12 glass-panel" style={{ padding: '2.5rem', textAlign: 'center' }}>
                <h2 className="text-h2" style={{ color: '#00ff88', marginBottom: '1rem' }}>Extract Data Vault</h2>
                <p className="text-secondary" style={{ marginBottom: '2rem' }}>Search across all acquired intelligent data points.</p>

                <form onSubmit={handleSearch} style={{ display: 'flex', gap: '1rem', maxWidth: '800px', margin: '0 auto' }}>
                    <input
                        type="text"
                        className="input-glass"
                        placeholder="Enter keywords or RegEx queries..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        style={{ padding: '1.25rem' }}
                    />
                    <button type="submit" className="btn btn-primary" style={{ padding: '0 2rem' }}>
                        {loading ? 'Searching...' : 'Scan Vault'}
                    </button>
                </form>
            </div>

            {/* Results Grid */}
            <div className="col-span-12">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', padding: '0 1rem' }}>
                    <h3 className="text-h3">{results.length} Records Found</h3>
                    <button className="btn btn-secondary" onClick={fetchInitialData}>Refresh All</button>
                </div>

                {results.length === 0 ? (
                    <div className="glass-panel" style={{ padding: '4rem', textAlign: 'center' }}>
                        <p className="text-secondary" style={{ fontSize: '1.2rem' }}>
                            {hasSearched ? 'No matching telemetry records found.' : 'Vault is currently empty.'}
                        </p>
                    </div>
                ) : (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '1.5rem' }}>
                        {results.map((result, index) => (
                            <div key={index} className="glass-card animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                                <div style={{ borderBottom: '1px solid var(--border-glass)', paddingBottom: '0.5rem', marginBottom: '0.5rem' }}>
                                    <h4 className="text-gradient-cyan" style={{ fontSize: '1.1rem', margin: '0 0 0.25rem 0', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                        {result.title || 'Untitled Document'}
                                    </h4>
                                    <a href={result.url} target="_blank" rel="noreferrer" style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                        {result.url}
                                    </a>
                                </div>

                                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.6, flexGrow: 1, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 4, WebkitBoxOrient: 'vertical' }}>
                                    {result.content || 'No content parsed.'}
                                </p>

                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto', paddingTop: '1rem', borderTop: '1px dashed var(--border-glass)' }}>
                                    <span style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: '#8a2be2' }}>
                                        HASH: {result.hash?.substring(0, 12)}...
                                    </span>
                                    <button className="btn btn-secondary" style={{ padding: '0.25rem 0.75rem', fontSize: '0.8rem' }} onClick={() => alert('Full view not implemented in demo')}>
                                        Inspect
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

        </div>
    );
};

export default DataVault;

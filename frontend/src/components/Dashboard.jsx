import React, { useEffect, useState } from 'react';

const Dashboard = () => {
    const [stats, setStats] = useState({ queued: 0, pages: 0, total: 0 });
    const [loading, setLoading] = useState(true);

    const fetchStats = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/v1/stats');
            if (response.ok) {
                const data = await response.json();
                setStats(data);
            }
        } catch (err) {
            console.error('Failed to fetch stats:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStats();
        // Poll every 3 seconds for live dashboard feel
        const interval = setInterval(fetchStats, 3000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>

            <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center' }}>
                <h2 className="text-h1" style={{ marginBottom: '0.5rem' }}>Overview</h2>
                <p className="text-secondary">Real-time telemetry and extraction statistics</p>
            </div>

            <div className="grid-dashboard">

                <div className="col-span-4 glass-card" style={{ textAlign: 'center' }}>
                    <h3 className="text-h3 text-secondary" style={{ marginBottom: '1rem' }}>Active Tasks</h3>
                    <div className="text-gradient-cyan" style={{ fontSize: '4rem', fontWeight: '800', lineHeight: 1 }}>
                        {loading ? '...' : stats.queued}
                    </div>
                    <p className="text-muted" style={{ marginTop: '1rem' }}>URLs currently queued</p>
                </div>

                <div className="col-span-4 glass-card" style={{ textAlign: 'center' }}>
                    <h3 className="text-h3 text-secondary" style={{ marginBottom: '1rem' }}>Total Processed</h3>
                    <div className="text-gradient-purple" style={{ fontSize: '4rem', fontWeight: '800', lineHeight: 1 }}>
                        {loading ? '...' : stats.total}
                    </div>
                    <p className="text-muted" style={{ marginTop: '1rem' }}>All-time URLs processed</p>
                </div>

                <div className="col-span-4 glass-card" style={{ textAlign: 'center' }}>
                    <h3 className="text-h3 text-secondary" style={{ marginBottom: '1rem' }}>Data Entities</h3>
                    <div style={{ fontSize: '4rem', fontWeight: '800', lineHeight: 1, color: '#00ff88', textShadow: '0 0 20px rgba(0,255,136,0.3)' }}>
                        {loading ? '...' : stats.pages}
                    </div>
                    <p className="text-muted" style={{ marginTop: '1rem' }}>Extracted documents in Vault</p>
                </div>

            </div>

        </div>
    );
};

export default Dashboard;

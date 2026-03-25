import React, { useState, useEffect, useRef } from 'react';

const LiveFeed = () => {
    const [logs, setLogs] = useState([
        { time: new Date().toLocaleTimeString(), type: 'info', msg: 'System initialized. Awaiting commands...' }
    ]);
    const endRef = useRef(null);

    // Auto-scroll to bottom of terminal
    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    // Simulate incoming logs (since the python backend doesn't have a ws endpoint yet)
    useEffect(() => {
        const fetchStats = async () => {
            try {
                const response = await fetch('http://localhost:8000/api/v1/stats');
                if (response.ok) {
                    const data = await response.json();
                    if (data.queued > 0) {
                        setLogs(prev => [...prev, { time: new Date().toLocaleTimeString(), type: 'info', msg: `[ENGINE] Detected ${data.queued} targets in queue. Processing...` }]);
                    }
                }
            } catch {
                // fail silently for logs
            }
        };

        fetchStats();
        const interval = setInterval(fetchStats, 5000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="grid-dashboard animate-fade-in" style={{ gap: '2rem' }}>

            <div className="col-span-12 glass-panel" style={{ padding: '0', overflow: 'hidden' }}>

                <div className="terminal-header">
                    <div className="terminal-dot term-red"></div>
                    <div className="terminal-dot term-yellow"></div>
                    <div className="terminal-dot term-green"></div>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginLeft: '1rem', fontFamily: 'monospace' }}>bash - root@scrap-engine:~</span>
                </div>

                <div className="terminal-body">
                    {logs.map((log, i) => (
                        <div key={i} className="log-line">
                            <span className="log-time">[{log.time}]</span>
                            <span className={log.type === 'error' ? 'log-error' : log.type === 'success' ? 'log-success' : 'log-info'}>
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

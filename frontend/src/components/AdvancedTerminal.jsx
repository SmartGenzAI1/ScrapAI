import React, { useState, useEffect, useRef } from 'react';
import '../index.css';

const MAX_LOGS = 200;

export default function AdvancedTerminal() {
    const [inputVal, setInputVal] = useState('');
    const [logs, setLogs] = useState([]);
    const [stats, setStats] = useState({ queued: 0, pages: 0, total: 0 });
    const inputRef = useRef(null);
    const logsRef = useRef(null);

    // Real-time metric loop (runs extremely fast for that "milli seconds" feel)
    useEffect(() => {
        const fetchFastStats = async () => {
            try {
                const res = await fetch('http://localhost:8000/api/v1/stats');
                if (res.ok) {
                    const data = await res.json();
                    setStats(data);
                    // If the queue is processing, simulate high speed logs
                    if (data.queued > 0) {
                        sysLog(`[ENGINE] Processing queue... Targets remaining: ${data.queued}`, 'exe');
                    }
                }
            } catch (e) {
                // silent fail on loop
            }
        };

        // fetch every 1000ms, but we can animate faster in UI if desired
        const int = setInterval(fetchFastStats, 1000);
        return () => clearInterval(int);
    }, []);

    // Ensure input always has focus
    useEffect(() => {
        const focusInput = () => inputRef.current?.focus();
        document.addEventListener('click', focusInput);
        focusInput();
        return () => document.removeEventListener('click', focusInput);
    }, []);

    // Auto-scroll logs
    useEffect(() => {
        if (logsRef.current) {
            logsRef.current.scrollTop = logsRef.current.scrollHeight;
        }
    }, [logs]);

    // Boot sequence
    useEffect(() => {
        const boot = async () => {
            sysLog("Initializing ScrapAI Master Terminal v2.0...", "sys");
            await new Promise(r => setTimeout(r, 100));
            sysLog("Establishing secured connection to backend engine [127.0.0.1:8000]...", "sys");
            await new Promise(r => setTimeout(r, 200));
            sysLog("Connection ESTABLISHED. Terminal ready for high-velocity payload injection.", "sys");
            sysLog("Type 'help' for command directory.", "sys");
        };
        boot();
    }, []);

    const addLog = (msg, tag = 'sys', rawHTML = false) => {
        const ts = new Date().toISOString().substring(11, 23); // e.g., 14:22:15.123
        setLogs(prev => {
            const newLogs = [...prev, { id: Math.random(), ts, tag, msg, rawHTML }];
            return newLogs.slice(-MAX_LOGS);
        });
    };

    const sysLog = (msg, tag = 'sys') => addLog(msg, tag);

    const handleCommand = async (e) => {
        if (e.key === 'Enter') {
            const cmd = inputVal.trim();
            setInputVal(''); // instant clear

            if (!cmd) return;

            addLog(`$ ${cmd}`, 'usr');
            const parts = cmd.split(' ');
            const base = parts[0].toLowerCase();

            switch (base) {
                case 'help':
                    addLog("Available directives:", "sys");
                    addLog("  status      - Display real-time telemetry from the ingestion engine", "sys");
                    addLog("  target <url> - Inject a URL into the high-speed extraction queue", "sys");
                    addLog("  scan <query> - Sweep the Data Vault for matching records", "sys");
                    addLog("  clear       - Purge local terminal cache", "sys");
                    break;
                case 'clear':
                    setLogs([]);
                    sysLog("Terminal cache purged.", "sys");
                    break;
                case 'status':
                    sysLog(`TELEMETRY: [QUEUED: ${stats.queued}] [EXTRACTED: ${stats.pages}] [TOTAL PROCESSED: ${stats.total}]`, "exe");
                    break;
                case 'target':
                    const t = parts.slice(1).join(' ');
                    if (!t) {
                        addLog("ERR: Target parameter missing. Usage: target <url>", "err");
                        break;
                    }
                    if (!t.startsWith('http')) {
                        addLog("ERR: Invalid protocol. Require HTTP/HTTPS format.", "err");
                        break;
                    }
                    addLog(`Queueing target payload: ${t}`, "sys");
                    try {
                        const start = performance.now();
                        const res = await fetch('http://localhost:8000/api/v1/crawl', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ urls: [t] })
                        });
                        const ms = (performance.now() - start).toFixed(1);
                        if (res.ok) {
                            const data = await res.json();
                            addLog(`Target injected successfully in ${ms}ms. Queue length: ${data.queued}`, "exe");
                        } else {
                            addLog(`API REJECTED injected payload. Status: ${res.status}`, "err");
                        }
                    } catch (err) {
                        addLog(`FATAL: Connection to execution engine severed. > ${err.message}`, "err");
                    }
                    break;
                case 'scan':
                    const q = parts.slice(1).join(' ');
                    addLog(`Initiating Vault sweep for pattern: [${q || '*'}]...`, "sys");
                    try {
                        const start = performance.now();
                        const res = await fetch(`http://localhost:8000/api/v1/search?q=${encodeURIComponent(q)}`);
                        const ms = (performance.now() - start).toFixed(1);
                        if (res.ok) {
                            const data = await res.json();
                            addLog(`Sweep complete in ${ms}ms. Hits: ${data.length}`, "exe");
                            if (data.length > 0) {
                                // Table output
                                let table = `<table class="data-table"><tr><th>URL</th><th>TITLE / HASH</th></tr>`;
                                data.forEach(d => {
                                    table += `<tr><td>${d.url}</td><td>${d.title || 'NULL'} <span class="cyan">(${d.hash?.substring(0, 8)})</span></td></tr>`;
                                });
                                table += `</table>`;
                                addLog(table, "sys", true);
                            }
                        }
                    } catch (err) {
                        addLog(`Sweep failed: ${err.message}`, "err");
                    }
                    break;
                default:
                    addLog(`ERR: Unrecognized directive '${base}'. Try 'help'.`, "err");
            }
        }
    };

    return (
        <div className="terminal-container">

            {/* Header Info */}
            <div className="terminal-header">
                <h1 className="cyan" style={{ fontSize: '1.5rem', marginBottom: '0.2rem' }}>ScrapAI // MASTER TERMINAL [v2.0-HT]</h1>
                <div style={{ display: 'flex', gap: '2rem', fontSize: '0.9rem' }}>
                    <span>NODE: <span className="bold" style={{ color: '#fff' }}>local-alpha</span></span>
                    <span>NET: <span className="bold cyan">ONLINE</span></span>
                    <span>LATENCY: <span className="bold">1ms</span></span>
                    <span>ENCRYPTION: <span className="bold" style={{ color: '#fff' }}>AES-256</span></span>
                </div>
                <div style={{ display: 'flex', gap: '2rem', marginTop: '0.5rem', borderTop: '1px solid var(--term-border)', paddingTop: '0.5rem', fontSize: '0.85rem' }}>
                    <span className="dim">VAULT ENTITIES: <span className="purple bold">{stats.pages}</span></span>
                    <span className="dim">ACTIVE TARGETS: <span className="warning bold">{stats.queued}</span></span>
                    <span className="dim">LIFETIME CYCLES: <span className="cyan bold">{stats.total}</span></span>
                </div>
            </div>

            <div className="terminal-logs" ref={logsRef}>
                {logs.map(log => (
                    <div key={log.id} className="log-entry">
                        <span className="log-ts">{log.ts}</span>
                        <span className={`log-tag tag-${log.tag}`}>[{log.tag}]</span>
                        {log.rawHTML ? (
                            <span style={{ flex: 1 }} dangerouslySetInnerHTML={{ __html: log.msg }} />
                        ) : (
                            <span style={{ flex: 1 }} className={log.tag === 'err' ? 'error' : log.tag === 'exe' ? 'cyan' : ''}>
                                {log.msg}
                            </span>
                        )}
                    </div>
                ))}

                {/* Dynamic Prompt Line */}
                <div className="terminal-prompt">
                    <span className="prompt-prefix">root@scrap-ai:~$</span>
                    <span className="prompt-text">
                        {inputVal}<span className="blink">█</span>
                    </span>
                </div>
            </div>

            <input
                type="text"
                className="terminal-input"
                ref={inputRef}
                value={inputVal}
                onChange={(e) => setInputVal(e.target.value)}
                onKeyDown={handleCommand}
                autoComplete="off"
                spellCheck="false"
            />
        </div>
    );
}

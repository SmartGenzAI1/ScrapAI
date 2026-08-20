import React, { useState, useEffect, useRef } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || '';
const MAX_LOGS = 250;

export default function AdvancedTerminal() {
    const [inputVal, setInputVal] = useState('');
    const [logs, setLogs] = useState([]);
    const [stats, setStats] = useState({ queued: 0, pages: 0, chunks: 0, total: 0 });
    const inputRef = useRef(null);
    const logsRef = useRef(null);

    const fetchStats = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/v1/stats`);
            if (res.ok) {
                const data = await res.json();
                setStats(data);
            }
        } catch (e) {}
    };

    useEffect(() => {
        fetchStats();
        const int = setInterval(fetchStats, 3000);
        return () => clearInterval(int);
    }, []);

    useEffect(() => {
        if (logsRef.current) {
            logsRef.current.scrollTop = logsRef.current.scrollHeight;
        }
    }, [logs]);

    useEffect(() => {
        const boot = async () => {
            sysLog("ScrapAI Developer CLI [v2.0-HT] Initialized", "sys");
            sysLog("Local Dense Vector Space & Okapi BM25 Ready [Zero-API Offline Mode Active]", "exe");
            sysLog("Type 'help' to view available commands.", "sys");
        };
        boot();
    }, []);

    const addLog = (msg, tag = 'sys', rawHTML = false) => {
        const ts = new Date().toISOString().substring(11, 19);
        setLogs(prev => {
            const newLogs = [...prev, { id: Math.random(), ts, tag, msg, rawHTML }];
            return newLogs.slice(-MAX_LOGS);
        });
    };

    const sysLog = (msg, tag = 'sys') => addLog(msg, tag);

    const handleCommand = async (e) => {
        if (e.key === 'Enter') {
            const cmd = inputVal.trim();
            setInputVal('');
            if (!cmd) return;

            addLog(`$ ${cmd}`, 'usr');
            const parts = cmd.split(' ');
            const base = parts[0].toLowerCase();
            const rest = parts.slice(1).join(' ').trim();

            switch (base) {
                case 'help':
                    addLog("Available CLI Commands:", "sys");
                    addLog("  status              - Show real-time system counters & queue stats", "sys");
                    addLog("  target <url>        - Enqueue target URL for recursive ingestion", "sys");
                    addLog("  crawl-direct <url>  - Immediately scrape and index target URL", "sys");
                    addLog("  scan <query>        - Execute hybrid semantic search across Vault", "sys");
                    addLog("  answer <question>   - Extractive QA reasoning with verified source citations", "sys");
                    addLog("  pages               - List indexed Vault document records", "sys");
                    addLog("  pipeline            - Trigger an immediate pipeline cycle (crawl -> chunk -> embed)", "sys");
                    addLog("  clear               - Clear terminal log output", "sys");
                    break;

                case 'clear':
                    setLogs([]);
                    sysLog("Terminal log display cleared.", "sys");
                    break;

                case 'status':
                    sysLog(`TELEMETRY: [Documents: ${stats.pages}] [Chunks: ${stats.chunks || 0}] [Queued: ${stats.queued}] [Processed: ${stats.total}]`, "exe");
                    break;

                case 'target':
                    if (!rest) {
                        addLog("Error: Target URL required. Usage: target <url>", "err");
                        break;
                    }
                    let targetUrl = rest.startsWith('http') ? rest : 'https://' + rest;
                    addLog(`Enqueuing target: ${targetUrl}...`, "sys");
                    try {
                        const res = await fetch(`${API_BASE}/api/v1/crawl`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ urls: [targetUrl], max_depth: 1 })
                        });
                        if (res.ok) {
                            const data = await res.json();
                            addLog(`Target accepted into queue. Active queue: ${data.queued}`, "exe");
                        } else {
                            addLog(`API error: Status ${res.status}`, "err");
                        }
                    } catch (err) {
                        addLog(`Connection failed: ${err.message}`, "err");
                    }
                    break;

                case 'crawl-direct':
                    if (!rest) {
                        addLog("Error: Target URL required. Usage: crawl-direct <url>", "err");
                        break;
                    }
                    let directUrl = rest.startsWith('http') ? rest : 'https://' + rest;
                    addLog(`Executing immediate scrape for ${directUrl}...`, "sys");
                    try {
                        const res = await fetch(`${API_BASE}/api/v1/crawl/direct`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ url: directUrl })
                        });
                        if (res.ok) {
                            const data = await res.json();
                            addLog(`Direct scrape success: "${data.title || directUrl}" (${data.word_count || 0} words)`, "exe");
                        } else {
                            addLog(`Direct scrape failed: HTTP ${res.status}`, "err");
                        }
                    } catch (err) {
                        addLog(`Scrape error: ${err.message}`, "err");
                    }
                    break;

                case 'scan':
                    addLog(`Executing hybrid search for: "${rest || '*'}"...`, "sys");
                    try {
                        const res = await fetch(`${API_BASE}/api/v1/search?q=${encodeURIComponent(rest)}&limit=8`);
                        if (res.ok) {
                            const data = await res.json();
                            addLog(`Search completed: ${data.length} document(s) retrieved`, "exe");
                            data.forEach((d, i) => {
                                addLog(`  [${i+1}] ${d.title || d.url} (Score: ${d.score})`, "sys");
                                addLog(`      Snippet: ${(d.snippet || d.content || '').substring(0, 110)}...`, "sys");
                            });
                        }
                    } catch (err) {
                        addLog(`Search failed: ${err.message}`, "err");
                    }
                    break;

                case 'answer':
                case 'ask':
                    if (!rest) {
                        addLog("Error: Question prompt required. Usage: answer <question>", "err");
                        break;
                    }
                    addLog(`Synthesizing extractive answer for: "${rest}"...`, "sys");
                    try {
                        const res = await fetch(`${API_BASE}/api/v1/query/answer`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ query: rest, limit: 8 })
                        });
                        if (res.ok) {
                            const data = await res.json();
                            addLog(`Extractive Answer (Confidence: ${Math.round(data.confidence * 100)}%):`, "exe");
                            addLog(`  ${data.answer}`, "sys");
                            if (data.sources && data.sources.length) {
                                const srcStr = data.sources.map(s => `[${s.citation_id}] ${s.title || s.url}`).join(' | ');
                                addLog(`  Sources: ${srcStr}`, "sys");
                            }
                        }
                    } catch (err) {
                        addLog(`QA synthesis failed: ${err.message}`, "err");
                    }
                    break;

                case 'pages':
                    try {
                        const res = await fetch(`${API_BASE}/api/v1/pages?limit=10`);
                        if (res.ok) {
                            const pages = await res.json();
                            addLog(`Recent Vault Documents (${pages.length}):`, "exe");
                            pages.forEach(p => {
                                addLog(`  #${p.id} | ${p.title || 'Untitled'} | ${p.domain} | Words: ${p.word_count}`, "sys");
                            });
                        }
                    } catch (e) {
                        addLog(`Error: ${e.message}`, "err");
                    }
                    break;

                case 'pipeline':
                    addLog("Executing pipeline cycle (crawl -> chunk -> embed)...", "sys");
                    try {
                        const res = await fetch(`${API_BASE}/api/v1/pipeline/run`, { method: 'POST' });
                        if (res.ok) {
                            const d = await res.json();
                            addLog(`Pipeline step finished: ${d.step_activity.crawled} crawled, ${d.step_activity.chunked} chunked, ${d.step_activity.embedded} embedded`, "exe");
                        }
                    } catch (e) {
                        addLog(`Pipeline error: ${e.message}`, "err");
                    }
                    break;

                default:
                    addLog(`Unrecognized command '${base}'. Type 'help' for directory.`, "err");
            }
        }
    };

    return (
        <div className="terminal-window">
            <div className="terminal-titlebar">
                <div className="traffic-dots">
                    <div className="dot dot-red" />
                    <div className="dot dot-yellow" />
                    <div className="dot dot-green" />
                </div>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                    scrapai-cli – bash – 80x24
                </span>
                <span className="badge badge-emerald" style={{ fontSize: '0.7rem' }}>
                    Zero-API Active
                </span>
            </div>

            <div className="terminal-body" ref={logsRef} onClick={() => inputRef.current?.focus()}>
                {logs.map(log => (
                    <div key={log.id} className="term-line">
                        <span className="term-time">[{log.ts}]</span>
                        <span className={`term-tag ${log.tag}`}>
                            {log.tag === 'sys' ? 'SYS' : log.tag === 'usr' ? 'IN' : log.tag === 'exe' ? 'OUT' : 'ERR'}
                        </span>
                        <span style={{
                            color: log.tag === 'err' ? 'var(--accent-rose)' : log.tag === 'exe' ? 'var(--accent-emerald)' : log.tag === 'usr' ? 'var(--text-main)' : 'var(--text-secondary)',
                            fontWeight: log.tag === 'usr' ? 600 : 400
                        }}>
                            {log.msg}
                        </span>
                    </div>
                ))}
            </div>

            <div className="term-input-row">
                <span className="term-prompt">scrapai:~$</span>
                <input
                    type="text"
                    className="term-text-input"
                    ref={inputRef}
                    value={inputVal}
                    onChange={(e) => setInputVal(e.target.value)}
                    onKeyDown={handleCommand}
                    placeholder="Type command ('help', 'status', 'scan <query>', 'answer <question>')..."
                    autoFocus
                    spellCheck="false"
                />
            </div>
        </div>
    );
}

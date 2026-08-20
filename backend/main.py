import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from backend.config import config
from backend.api.routes import router as api_router
from workers.pipeline_manager import pipeline_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("scrapai")

# Background worker loop task
_background_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start unified background pipeline manager if enabled
    global _background_task
    if config.server.enable_background_workers:
        logger.info("⚡ Launching integrated ScrapAI background pipeline task...")
        _background_task = asyncio.create_task(
            pipeline_manager.run_pipeline_loop(poll_interval=float(config.server.worker_interval))
        )
    yield
    # Shutdown: Stop pipeline manager
    if _background_task:
        logger.info("🛑 Stopping background pipeline task...")
        pipeline_manager.stop()
        _background_task.cancel()
        try:
            await _background_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="ScrapAI",
    description="Autonomous Web Crawling, Chunking, Embedding & Semantic Search Platform (100% Offline / Zero-API Ready)",
    version="2.0-HT",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(api_router)

# Mount frontend dist static files if built
frontend_dist_path = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist_path.exists() and (frontend_dist_path / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist_path / "assets")), name="assets")

    @app.get("/", response_class=FileResponse)
    async def serve_react_app():
        return FileResponse(str(frontend_dist_path / "index.html"))
else:
    @app.get("/", response_class=HTMLResponse)
    async def root_view():
        """Cyberpunk Unified Web UI fallback if frontend is not built"""
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ScrapAI // Cyber Master Terminal</title>
            <style>
                :root {
                    --bg: #07090e;
                    --panel: #0d121d;
                    --border: #1a253b;
                    --cyan: #00f2fe;
                    --green: #00ff88;
                    --purple: #8a2be2;
                    --text: #e2e8f0;
                    --muted: #64748b;
                }
                * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; }
                body { background: var(--bg); color: var(--text); padding: 2rem; min-height: 100vh; }
                .header { max-width: 1100px; margin: 0 auto 2rem; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 1rem; }
                .title { font-size: 1.6rem; font-weight: 800; color: var(--cyan); letter-spacing: 1px; }
                .badges { display: flex; gap: 1rem; font-size: 0.85rem; font-family: monospace; }
                .badge { background: var(--panel); border: 1px solid var(--border); padding: 0.35rem 0.75rem; border-radius: 4px; }
                .badge span { font-weight: bold; color: var(--green); }
                .container { max-width: 1100px; margin: 0 auto; display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
                .card { background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 1.5rem; }
                .full-width { grid-column: span 2; }
                h2 { font-size: 1.15rem; margin-bottom: 1rem; color: var(--cyan); display: flex; align-items: center; gap: 0.5rem; }
                input, textarea { width: 100%; background: #05070a; border: 1px solid var(--border); color: var(--text); padding: 0.75rem 1rem; border-radius: 6px; font-size: 0.95rem; margin-bottom: 1rem; outline: none; }
                input:focus, textarea:focus { border-color: var(--cyan); box-shadow: 0 0 10px rgba(0,242,254,0.15); }
                button { background: linear-gradient(135deg, #00f2fe, #4facfe); border: none; color: #000; font-weight: bold; padding: 0.75rem 1.5rem; border-radius: 6px; cursor: pointer; transition: all 0.2s; }
                button:hover { opacity: 0.9; transform: translateY(-1px); }
                .answer-box { background: rgba(0, 242, 254, 0.04); border: 1px solid rgba(0, 242, 254, 0.2); border-radius: 6px; padding: 1rem; margin-top: 1rem; font-size: 0.95rem; line-height: 1.6; }
                .answer-box strong { color: var(--green); }
                .results-list { margin-top: 1rem; display: flex; flex-direction: column; gap: 0.75rem; max-height: 400px; overflow-y: auto; }
                .result-item { background: #080c14; border: 1px solid var(--border); padding: 1rem; border-radius: 6px; }
                .result-item h3 { font-size: 1rem; color: var(--cyan); margin-bottom: 0.25rem; }
                .result-item small { color: var(--muted); display: block; margin-bottom: 0.5rem; font-family: monospace; }
                .result-item p { font-size: 0.88rem; color: #94a3b8; }
                .score-pill { display: inline-block; background: rgba(0, 255, 136, 0.1); color: var(--green); font-size: 0.75rem; padding: 2px 6px; border-radius: 4px; margin-left: 6px; }
                .terminal-log { background: #030407; font-family: monospace; font-size: 0.85rem; padding: 1rem; border-radius: 6px; max-height: 180px; overflow-y: auto; border: 1px solid var(--border); color: #38bdf8; }
            </style>
        </head>
        <body>
            <div class="header">
                <div>
                    <div class="title">🕷️ ScrapAI // HYBRID INTELLIGENCE</div>
                    <p style="color: var(--muted); font-size: 0.85rem; margin-top: 0.25rem;">Autonomous Web Crawling, Chunking, Local Semantic Search & Extractive QA</p>
                </div>
                <div class="badges">
                    <div class="badge">PAGES: <span id="stat-pages">0</span></div>
                    <div class="badge">QUEUED: <span id="stat-queue">0</span></div>
                    <div class="badge">CHUNKS: <span id="stat-chunks">0</span></div>
                    <div class="badge">ENGINE: <span>OFFLINE-READY</span></div>
                </div>
            </div>

            <div class="container">
                <!-- Target Acquisition -->
                <div class="card">
                    <h2>🎯 Target Ingestion</h2>
                    <input type="url" id="crawl-url" placeholder="https://example.com" />
                    <div style="display: flex; gap: 0.5rem;">
                        <button onclick="queueTarget()">Enqueue Target</button>
                        <button onclick="crawlDirect()" style="background: transparent; border: 1px solid var(--cyan); color: var(--cyan);">Instant Crawl</button>
                    </div>
                    <div id="crawl-status" style="margin-top: 1rem; font-size: 0.85rem; color: var(--green);"></div>
                </div>

                <!-- Live Pipeline Telemetry -->
                <div class="card">
                    <h2>📡 Pipeline Telemetry</h2>
                    <div class="terminal-log" id="telemetry-log">
                        [INIT] ScrapAI Execution Engine v2.0 Active<br>
                        [READY] Local Vectorizer & BM25 Ready<br>
                        [READY] Standalone Zero-API Mode Armed
                    </div>
                    <div style="margin-top: 0.75rem; display: flex; gap: 0.5rem;">
                        <button onclick="triggerPipeline()" style="padding: 0.4rem 0.8rem; font-size: 0.8rem;">Run Pipeline Step</button>
                        <button onclick="fetchStats()" style="padding: 0.4rem 0.8rem; font-size: 0.8rem; background: transparent; border: 1px solid var(--border); color: var(--muted);">Refresh</button>
                    </div>
                </div>

                <!-- Semantic Search & Reasoning -->
                <div class="card full-width">
                    <h2>🔍 Hybrid Semantic Search & Extractive QA</h2>
                    <div style="display: flex; gap: 0.5rem;">
                        <input type="text" id="search-query" placeholder="Ask a question or enter keywords (e.g. 'What is the main topic?')..." />
                        <button onclick="executeSearch()" style="white-space: nowrap;">Search Vault</button>
                        <button onclick="executeAsk()" style="white-space: nowrap; background: linear-gradient(135deg, #00ff88, #00f2fe);">AI Answer</button>
                    </div>

                    <div id="answer-container" style="display: none;" class="answer-box">
                        <strong>🤖 Synthesized Extractive Answer:</strong>
                        <div id="answer-text" style="margin-top: 0.5rem;"></div>
                        <div id="answer-sources" style="margin-top: 0.75rem; font-size: 0.8rem; color: var(--muted);"></div>
                    </div>

                    <div class="results-list" id="results-list"></div>
                </div>
            </div>

            <script>
                function log(msg) {
                    const el = document.getElementById('telemetry-log');
                    const ts = new Date().toISOString().substring(11, 19);
                    el.innerHTML += `<div>[${ts}] ${msg}</div>`;
                    el.scrollTop = el.scrollHeight;
                }

                async function fetchStats() {
                    try {
                        const res = await fetch('/api/v1/stats');
                        if (res.ok) {
                            const data = await res.json();
                            document.getElementById('stat-pages').textContent = data.pages || 0;
                            document.getElementById('stat-queue').textContent = data.queued || 0;
                            document.getElementById('stat-chunks').textContent = data.chunks || 0;
                        }
                    } catch(e) {}
                }

                async function queueTarget() {
                    const input = document.getElementById('crawl-url');
                    const url = input.value.trim();
                    if (!url) return alert('Enter a URL');
                    log(`Enqueueing target: ${url}`);
                    try {
                        const res = await fetch('/api/v1/crawl', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({ urls: [url], max_depth: 1 })
                        });
                        const data = await res.json();
                        document.getElementById('crawl-status').textContent = data.message;
                        input.value = '';
                        log(`Target accepted into queue`);
                        fetchStats();
                    } catch(e) {
                        log(`Error: ${e.message}`);
                    }
                }

                async function crawlDirect() {
                    const input = document.getElementById('crawl-url');
                    const url = input.value.trim();
                    if (!url) return alert('Enter a URL');
                    log(`Executing direct crawl: ${url}...`);
                    try {
                        const res = await fetch('/api/v1/crawl/direct', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({ url })
                        });
                        const data = await res.json();
                        log(`Direct crawl complete: ${data.title || url} (${data.word_count || 0} words)`);
                        input.value = '';
                        fetchStats();
                    } catch(e) {
                        log(`Direct crawl error: ${e.message}`);
                    }
                }

                async function triggerPipeline() {
                    log('Triggering pipeline processing step...');
                    try {
                        const res = await fetch('/api/v1/pipeline/run', { method: 'POST' });
                        const data = await res.json();
                        log(`Pipeline cycle: Crawled: ${data.step_activity.crawled}, Chunked: ${data.step_activity.chunked}, Embedded: ${data.step_activity.embedded}`);
                        fetchStats();
                    } catch(e) {
                        log(`Pipeline trigger error: ${e.message}`);
                    }
                }

                async function executeSearch() {
                    const q = document.getElementById('search-query').value.trim();
                    if (!q) return;
                    log(`Searching: "${q}"...`);
                    document.getElementById('answer-container').style.display = 'none';
                    try {
                        const res = await fetch(`/api/v1/search?q=${encodeURIComponent(q)}`);
                        const results = await res.json();
                        renderResults(results);
                        log(`Search returned ${results.length} ranked records`);
                    } catch(e) {
                        log(`Search error: ${e.message}`);
                    }
                }

                async function executeAsk() {
                    const q = document.getElementById('search-query').value.trim();
                    if (!q) return;
                    log(`Synthesizing extractive reasoning for: "${q}"...`);
                    try {
                        const res = await fetch('/api/v1/query/answer', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({ query: q })
                        });
                        const data = await res.json();
                        
                        document.getElementById('answer-container').style.display = 'block';
                        document.getElementById('answer-text').innerHTML = data.answer;
                        
                        let sourcesHtml = 'Sources: ';
                        if (data.sources && data.sources.length) {
                            sourcesHtml += data.sources.map(s => `<a href="${s.url}" target="_blank" style="color: var(--cyan); margin-right: 8px;">[${s.citation_id}] ${s.title || s.url}</a>`).join('');
                        } else {
                            sourcesHtml += 'No sources found.';
                        }
                        document.getElementById('answer-sources').innerHTML = sourcesHtml;
                        
                        renderResults(data.results || []);
                        log(`Answer synthesized with ${data.sources?.length || 0} citations`);
                    } catch(e) {
                        log(`QA error: ${e.message}`);
                    }
                }

                function renderResults(results) {
                    const list = document.getElementById('results-list');
                    list.innerHTML = '';
                    if (!results || !results.length) {
                        list.innerHTML = '<div style="color: var(--muted); padding: 1rem; text-align: center;">No matching documents in Vault. Crawl some pages first.</div>';
                        return;
                    }
                    results.forEach(r => {
                        const item = document.createElement('div');
                        item.className = 'result-item';
                        item.innerHTML = `
                            <h3>${r.title || 'Untitled Document'} <span class="score-pill">Score: ${r.score}</span></h3>
                            <small>${r.url}</small>
                            <p>${r.snippet || r.content || ''}</p>
                        `;
                        list.appendChild(item);
                    });
                }

                setInterval(fetchStats, 3000);
                fetchStats();
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=config.server.host,
        port=config.server.port,
        reload=False
    )

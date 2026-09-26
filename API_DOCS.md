# ScrapAI API & Integration Reference

Comprehensive REST API and Telegram Bot documentation for **ScrapAI**.

Base URL: `http://localhost:8000/api/v1`

---

## 1. REST API Endpoints

### Health & Telemetry

#### `GET /api/v1/health`
Returns service status, version, and feature capabilities.
```json
{
  "status": "online",
  "service": "ScrapAI Platform",
  "version": "2.0-HT",
  "features": {
    "zero_api_semantic_search": true,
    "hybrid_ranking": true,
    "flashrank_neural_reranking": true,
    "flashrank_model": "ms-marco-TinyBERT-L-2-v2",
    "extractive_qa_reasoning": true,
    "autonomous_crawler": true
  }
}
```

#### `GET /api/v1/stats`
Returns live system metrics.
```json
{
  "queued": 0,
  "processing": 0,
  "completed": 12,
  "failed": 1,
  "pages": 12,
  "chunks": 48,
  "embeddings": 48,
  "domains": 4,
  "searches": 15,
  "total": 24
}
```

---

### Ingestion & Crawling

#### `POST /api/v1/crawl`
Enqueues a batch of URLs for background recursive crawling.
- **Request Body**:
```json
{
  "urls": ["https://news.ycombinator.com"],
  "priority": 0,
  "max_depth": 1
}
```
- **Response**:
```json
{
  "success": true,
  "message": "Accepted 1 target(s) into autonomous crawl queue",
  "queued": 1
}
```

#### `POST /api/v1/crawl/direct`
Immediately scrapes, parses, and indexes a single URL synchronously.
- **Request Body**:
```json
{
  "url": "https://example.com"
}
```

#### `GET /api/v1/queue`
Retrieves pending and processing crawl queue targets. Query params: `status` (`queued`, `processing`, `completed`, `failed`), `limit`.

#### `POST /api/v1/queue/clear`
Purges all entries from the crawl queue.

---

### Search & Extractive QA

#### `GET /api/v1/search?q={query}&limit={limit}&domain={domain}&rerank={true|false}`
Executes hybrid multi-signal search across indexed Vault documents with optional **FlashRank local neural cross-encoder re-ranking**.
- **Response**:
```json
[
  {
    "id": 1,
    "page_id": 1,
    "title": "Introduction to Artificial Intelligence",
    "url": "https://example.com/ai",
    "domain": "example.com",
    "snippet": "Artificial intelligence leverages machine learning models...",
    "score": 0.94,
    "flashrank_score": 0.98,
    "reranked": true,
    "semantic_score": 0.92,
    "bm25_score": 0.81,
    "hash": "e3b0c442..."
  }
]
```

#### `POST /api/v1/search/rerank`
Directly re-ranks a custom list of candidate passages against a query using local FlashRank ONNX in sub-15ms.
- **Request Body**:
```json
{
  "query": "vector databases",
  "candidates": [
    {"id": "doc1", "text": "Cooking delicious pasta recipes."},
    {"id": "doc2", "text": "Vector databases store dense embeddings for high-dimensional semantic search."}
  ],
  "blend_scores": false
}
```
- **Response**:
```json
{
  "query": "vector databases",
  "count": 2,
  "model": "ms-marco-TinyBERT-L-2-v2",
  "results": [
    {
      "id": "doc2",
      "text": "Vector databases store dense embeddings...",
      "flashrank_score": 0.9982,
      "score": 0.9982,
      "reranked": true
    },
    {
      "id": "doc1",
      "text": "Cooking delicious pasta recipes.",
      "flashrank_score": 0.0001,
      "score": 0.0001,
      "reranked": true
    }
  ]
}
```

#### `POST /api/v1/query/answer`
Performs extractive question answering with verified source citations.
- **Request Body**:
```json
{
  "query": "What is the core architecture of ScrapAI?",
  "limit": 10
}
```
- **Response**:
```json
{
  "query": "What is the core architecture of ScrapAI?",
  "answer": "ScrapAI is an autonomous web crawling, chunking, and dense vector indexing platform. [1]",
  "confidence": 0.86,
  "citations": ["[1]"],
  "sources": [
    {
      "citation_id": 1,
      "url": "https://example.com/architecture",
      "title": "Architecture Overview"
    }
  ]
}
```

---

### Documents & Data Export

#### `GET /api/v1/pages`
Returns paginated list of indexed documents. Query params: `skip`, `limit`, `domain`.

#### `GET /api/v1/pages/{id}`
Returns full document content, metadata, and sliced semantic chunks.

#### `DELETE /api/v1/pages/{id}`
Deletes a document, its chunks, and vector embeddings from the Vault.

#### `GET /api/v1/export?format={json|csv}`
Exports all indexed data in JSON or CSV format.

#### `POST /api/v1/pipeline/run`
Triggers an immediate background processing cycle (crawl $\rightarrow$ chunk $\rightarrow$ embed).

---

## 2. Telegram Bot Directives

Run with: `TELEGRAM_BOT_TOKEN="your_token" python telegram_bot.py`

| Directive | Description |
|---|---|
| `/start` | Welcome and interactive commands list |
| `/crawl <url>` | Enqueue target URL for ingestion |
| `/search <query>` | Execute hybrid search across Vault |
| `/answer <question>` | Ask natural language question with citations |
| `/stats` | View real-time system metrics |
| `/help` | Detailed help documentation |

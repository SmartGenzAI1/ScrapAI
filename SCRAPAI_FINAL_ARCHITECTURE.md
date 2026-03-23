# ScrapAI – Final Architecture, System Design & Flash Cards

## Semantic Search Engine + AI Retrieval Backend

This document contains the final professional architecture, Mermaid diagrams, system flows, and flash-card style summaries for ScrapAI.

---

1. System Overview

ScrapAI is a semantic search engine that:

- Crawls websites
- Extracts content
- Stores pages
- Splits content into chunks
- Generates embeddings
- Indexes vectors
- Provides semantic search API
- Returns ranked results
- Can be connected to an AI application

---

2. Final System Architecture (Mermaid Diagram)

flowchart TD
    A[User / Main AI App] --> B[FastAPI API Layer]

    B --> C[Search Endpoint]
    B --> D[Crawl Endpoint]
    B --> E[Stats Endpoint]

    D --> F[Crawl Queue]
    F --> G[Crawler Worker]
    G --> H[Download HTML]
    H --> I[Extract Content]
    I --> J[SQLite Database]

    J --> K[Chunking Worker]
    K --> L[Embedding Worker]
    L --> M[FAISS Vector Index]

    C --> N[Query Embedding]
    N --> M
    M --> O[Vector Search Results]
    O --> P[Ranking Engine]
    P --> Q[Results Builder]
    Q --> A

---

3. Data Pipeline Diagram

flowchart LR
    A[Internet] --> B[Crawler]
    B --> C[HTML]
    C --> D[Content Extraction]
    D --> E[Clean Text]
    E --> F[SQLite Database]
    F --> G[Chunk Text]
    G --> H[Embeddings]
    H --> I[FAISS Index]
    I --> J[Search]
    J --> K[Ranking]
    K --> L[Results]

---

4. Search Flow Diagram

flowchart TD
    A[User Query] --> B[Query Embedding]
    B --> C[Vector Search]
    C --> D[Top Chunks]
    D --> E[Map to Pages]
    E --> F[Ranking]
    F --> G[Build Results]
    G --> H[Return Results]

---

5. Crawl Flow Diagram

flowchart TD
    A[URL] --> B[Add to Queue]
    B --> C[Crawler Worker]
    C --> D[Download Page]
    D --> E[Extract Text]
    E --> F[Store Page]
    F --> G[Chunk Text]
    G --> H[Generate Embeddings]
    H --> I[Store in FAISS]

---

6. System Layers

Layer| Component
Layer 1| Crawler
Layer 2| Content Extraction
Layer 3| Database
Layer 4| Chunking
Layer 5| Embeddings
Layer 6| Vector Index
Layer 7| Search
Layer 8| Ranking
Layer 9| API
Layer 10| Main AI App

---

7. Database Schema

Pages Table

- id
- url
- title
- content
- domain
- created_at
- hash

Chunks Table

- id
- page_id
- chunk_text
- chunk_index

Embeddings Table

- id
- chunk_id
- vector

Crawl Queue Table

- id
- url
- status
- retries
- created_at

Search Logs

- id
- query
- timestamp
- results_count

---

8. Flash Cards – Components

Flash Card: Crawler

Downloads webpages from the internet and sends them for processing.

Flash Card: Extractor

Removes HTML tags and extracts readable text content.

Flash Card: Database

Stores pages, chunks, embeddings, queue, and logs.

Flash Card: Chunking

Splits large text into smaller pieces for embedding.

Flash Card: Embeddings

Converts text into vectors representing semantic meaning.

Flash Card: Vector Database

Stores embeddings and performs similarity search.

Flash Card: Search Engine

Finds relevant content based on query similarity.

Flash Card: Ranking Engine

Sorts search results by relevance score.

Flash Card: API Layer

Provides endpoints for crawl, search, and stats.

Flash Card: Main AI App

Uses ScrapAI search results for answering questions.

---

9. Flash Cards – Pipelines

Flash Card: Full Pipeline

Crawl → Extract → Store → Chunk → Embed → Index → Search → Rank → Return

Flash Card: Crawl Pipeline

URL → Queue → Crawl → Extract → Store → Chunk → Embed → Index

Flash Card: Search Pipeline

Query → Embedding → Vector Search → Rank → Results

---

10. API Endpoints

Endpoint| Method| Purpose
/api/crawl| POST| Add URL to crawl
/api/search| GET| Search content
/api/stats| GET| System stats
/api/page| GET| Get page content
/api/queue| GET| Queue status

---

11. Final Architecture Summary Diagram

flowchart TD
    A[Internet] --> B[Crawler]
    B --> C[Extractor]
    C --> D[Database]
    D --> E[Chunking]
    E --> F[Embeddings]
    F --> G[FAISS Index]
    G --> H[Search Engine]
    H --> I[Ranking]
    I --> J[API]
    J --> K[Main AI App]

---

12. Final One-Line System Architecture

Crawler → Database → Chunking → Embeddings → Vector Index → Search → Ranking → API → AI App

---

13. System Purpose

ScrapAI will act as:

- Semantic Search Engine
- Website Search Engine
- Knowledge Retrieval System
- Backend for AI Assistant
- Research Engine
- Document Search Engine
- Personal Knowledge Index
- Data Indexing Engine

---

14. Development Roadmap Summary

Phase 1

- SQLite database
- Page storage
- Crawl queue
- Basic crawler

Phase 2

- Chunking
- Embeddings
- FAISS index

Phase 3

- Search endpoint
- Ranking
- Snippets

Phase 4

- Recrawling
- Scheduler
- Logs
- Deployment

Phase 5

- Connect to AI app
- Multi-domain crawling
- Topic search
- Similar pages

---

15. Final System Pipeline (Most Important)

Internet
   ↓
Crawler
   ↓
Extractor
   ↓
Database
   ↓
Chunking
   ↓
Embeddings
   ↓
Vector Index
   ↓
Search
   ↓
Ranking
   ↓
API
   ↓
AI Application

This is the complete ScrapAI system architecture.

# System Design – ScrapAI

## Overview
ScrapAI is a distributed web crawling, content extraction, embedding, and semantic search platform designed to evolve into a production-grade AI search and knowledge indexing system.

The system follows a pipeline architecture where content flows through multiple processing stages: crawling, extraction, storage, embedding, indexing, and search.

---

# High Level Architecture
User
                 │
                 ▼
            API Gateway
                 │
    ┌────────────┼────────────┐
    │                           │
    ▼                           ▼
Crawl Queue                 Search Service │                           │ ▼                           ▼ Crawler Workers            Vector Search │                           │ ▼                           ▼ Content Storage            Embedding DB │ ▼ Embedding Workers │ ▼ Vector Database

---

# System Components

## 1. API Server
Responsible for:
- Accepting crawl requests
- Managing crawl queue
- Providing search endpoints
- Returning system stats
- Serving as central coordinator

## 2. Crawl Queue
Queue system stores:
- URLs to crawl
- Crawl priority
- Retry count
- Crawl status
- Scheduled crawl time

Queue ensures distributed crawling and prevents duplicate crawling.

## 3. Crawler Workers
Crawler workers:
- Fetch web pages
- Parse HTML
- Remove scripts/styles
- Extract readable text
- Generate metadata
- Send results to storage

Crawler workers should be horizontally scalable.

## 4. Content Storage
Stores:
- URL
- Title
- Content
- Metadata
- Crawl timestamp
- Content hash
- Embedding status

Future storage should use PostgreSQL or MongoDB.

## 5. Embedding Workers
Embedding workers:
- Fetch pages without embeddings
- Split content into chunks
- Generate embeddings
- Store embeddings in vector database
- Mark pages as processed

## 6. Vector Database
Stores embeddings for:
- Semantic search
- Similarity search
- Document retrieval
- AI question answering

Examples:
- Chroma
- FAISS
- Weaviate
- Pinecone

## 7. Search Service
Search service:
- Converts user query to embedding
- Searches vector database
- Retrieves relevant content
- Returns ranked results

## 8. Future AI Layer
Future system will include:
- Retrieval Augmented Generation (RAG)
- LLM answer generation
- Source citation
- Multi-document summarization

---

# Data Flow Pipeline
URL ↓ Queue ↓ Crawler ↓ Content Extraction ↓ Database ↓ Chunking ↓ Embeddings ↓ Vector Database ↓ Search ↓ AI Answer (Future)

---

# Database Design (Future)

## Pages Table
- id
- url
- title
- content
- hash
- created_at
- embedded

## Embeddings Table
- id
- page_id
- chunk_text
- embedding_vector

## Crawl Queue Table
- id
- url
- status
- retries
- scheduled_at

---

# Design Goals
- Scalable crawling
- Distributed workers
- Modular architecture
- Semantic search
- AI integration ready
- Production deployable
- Fault tolerant
- Queue-based processing

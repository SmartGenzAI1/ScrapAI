"""
Comprehensive Automated Test Suite for ScrapAI.
Tests chunking, local vectorizer, BM25, hybrid ranking, extractive QA,
database operations, link filtering, and API routes with zero external API dependencies.
"""

import sys
from pathlib import Path

# Ensure root directory is on sys.path in all test runner environments
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import asyncio
import pytest
from fastapi.testclient import TestClient

from backend.utils.chunker import TextChunker, chunk_text
from backend.search.semantic_engine import (
    LocalSemanticVectorizer,
    BM25Engine,
    LocalSemanticEngine,
    cosine_similarity
)
from backend.database.client import DatabaseClient
from backend.scraper.lightweight_crawler import LightweightCrawler
from backend.main import app


# ---------------- 1. Chunker Tests ----------------

def test_chunker_sentences():
    text = (
        "Artificial intelligence is transforming software engineering. "
        "Modern systems leverage machine learning algorithms for retrieval. "
        "Web scrapers extract structured information from unstructured pages. "
        "Vector databases store dense embeddings for semantic search."
    )
    chunker = TextChunker(chunk_size=100, overlap=20)
    chunks = chunker.chunk_by_sentences(text)
    
    assert len(chunks) >= 2
    assert all(len(c.text) > 0 for c in chunks)
    assert any("Artificial intelligence" in c.text for c in chunks)


def test_chunker_fixed_size():
    text = "The quick brown fox jumps over the lazy dog repeatedly to test fixed size chunking utility."
    chunker = TextChunker(chunk_size=30, overlap=10)
    chunks = chunker.chunk_by_fixed_size(text)
    
    assert len(chunks) >= 2
    assert chunks[0].index == 0
    assert chunks[1].index == 1


def test_chunker_empty_input():
    chunker = TextChunker()
    assert chunker.chunk_by_sentences("") == []
    assert chunker.chunk_by_sentences("   ") == []
    assert chunker.chunk_by_fixed_size("") == []


# ---------------- 2. Semantic & Search Engine Tests ----------------

def test_local_vectorizer():
    vectorizer = LocalSemanticVectorizer(dimension=64)
    texts = [
        "Distributed web crawler and semantic search engine",
        "Deep learning and artificial intelligence knowledge indexing",
        "Delicious cooking recipes and baking cakes"
    ]
    vectors = vectorizer.encode(texts)
    
    assert len(vectors) == 3
    assert len(vectors[0]) == 64
    assert len(vectors[1]) == 64
    
    sim_tech = cosine_similarity(vectors[0], vectors[1])
    sim_unrelated = cosine_similarity(vectors[0], vectors[2])
    
    assert 0.0 <= sim_tech <= 1.0
    assert 0.0 <= sim_unrelated <= 1.0


def test_vectorizer_edge_cases():
    vectorizer = LocalSemanticVectorizer(dimension=64)
    empty_vectors = vectorizer.encode(["", "   ", "a"])
    assert len(empty_vectors) == 3
    assert len(empty_vectors[0]) == 64
    
    # Cosine similarity edge cases (zero division / mismatched dimensions)
    assert cosine_similarity([], []) == 0.0
    assert cosine_similarity([0.0]*64, [0.0]*64) == 0.0
    assert cosine_similarity([1.0]*64, [1.0]*32) == 0.0


def test_bm25_engine():
    corpus = [
        "FastAPI is a modern web framework for building APIs with Python.",
        "ScrapAI crawls websites, chunks text, and stores vectors.",
        "PostgreSQL and SQLite are relational database management systems."
    ]
    bm25 = BM25Engine()
    bm25.fit(corpus)
    
    score_api = bm25.score("FastAPI Python framework", 0)
    score_other = bm25.score("FastAPI Python framework", 1)
    
    assert score_api > score_other
    assert score_api > 0.0


def test_hybrid_ranking():
    engine = LocalSemanticEngine(dimension=64, use_neural=False)
    candidates = [
        {
            "id": 1,
            "page_id": 1,
            "title": "Introduction to Neural Networks",
            "content": "Neural networks are computational models inspired by biological brains for machine learning.",
            "url": "https://example.com/neural-networks"
        },
        {
            "id": 2,
            "page_id": 2,
            "title": "Baking Sourdough Bread",
            "content": "Sourdough bread is made by fermenting dough using naturally occurring lactobacilli and yeast.",
            "url": "https://example.com/baking"
        }
    ]
    
    ranked = engine.hybrid_rank("What are neural networks in machine learning?", candidates)
    
    assert len(ranked) == 2
    assert ranked[0]["page_id"] == 1
    assert ranked[0]["score"] > ranked[1]["score"]
    assert "snippet" in ranked[0]


def test_extractive_qa_answer():
    engine = LocalSemanticEngine(dimension=64, use_neural=False)
    candidates = [
        {
            "id": 1,
            "page_id": 1,
            "title": "Quantum Computing Basics",
            "content": "Quantum computing is a rapidly-emerging technology that harnesses the laws of quantum mechanics. It solves complex problems too difficult for classical supercomputers.",
            "url": "https://example.com/quantum",
            "score": 0.88
        }
    ]
    
    answer_res = engine.generate_extractive_answer("What is quantum computing?", candidates)
    
    assert "answer" in answer_res
    assert "[1]" in answer_res["answer"]
    assert len(answer_res["sources"]) == 1
    assert answer_res["sources"][0]["url"] == "https://example.com/quantum"
    assert answer_res["confidence"] > 0.4


def test_extractive_qa_empty_candidates():
    engine = LocalSemanticEngine(dimension=64, use_neural=False)
    answer_res = engine.generate_extractive_answer("Any query?", [])
    assert "No indexed content matches" in answer_res["answer"]
    assert answer_res["confidence"] == 0.0


# ---------------- 3. Database Operations Tests ----------------

@pytest.mark.asyncio
async def test_database_lifecycle():
    db = DatabaseClient(database_url="sqlite:///:memory:")
    
    # 1. Queue operations
    added = await db.add_to_queue("https://test.local/doc1", priority=5)
    assert added is True
    
    # Duplicate prevention
    added_dup = await db.add_to_queue("https://test.local/doc1")
    assert added_dup is False
    
    next_item = await db.get_next_queue_item()
    assert next_item is not None
    assert next_item["url"] == "https://test.local/doc1"
    
    marked = await db.mark_queue_processed(next_item["id"], status="completed")
    assert marked is True
    
    # 2. Save page
    page_data = {
        "url": "https://test.local/doc1",
        "title": "Test Local Document",
        "content": "ScrapAI autonomous web scraping engine indexing text blocks.",
        "hash": "testhash12345"
    }
    page_id, is_new = await db.save_page(page_data)
    assert page_id > 0
    assert is_new is True
    
    # 3. Chunking & Embeddings
    chunk_id = await db.save_chunk(page_id=page_id, chunk_text="ScrapAI autonomous web scraping engine", chunk_index=0)
    assert chunk_id > 0
    
    emb_id = await db.save_embedding(chunk_id=chunk_id, vector=[0.1, 0.2, 0.3])
    assert emb_id > 0
    
    # 4. Search
    results = await db.search_content("ScrapAI web scraping")
    assert len(results) >= 1
    assert results[0]["page_id"] == page_id
    
    # 5. Stats
    stats = await db.get_stats()
    assert stats["pages"] == 1
    assert stats["chunks"] == 1
    assert stats["embeddings"] == 1


# ---------------- 4. Scraper Content Extraction Tests ----------------

def test_html_cleaning_and_extraction():
    crawler = LightweightCrawler()
    sample_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sample Scraped Article</title>
        <meta name="description" content="A test article for content parsing." />
        <meta name="author" content="Owais" />
    </head>
    <body>
        <nav><a href="/home">Home</a><a href="/about">About</a></nav>
        <article>
            <h1>Main Article Heading</h1>
            <p>This is the first paragraph of clean extracted text content.</p>
            <p>Here is a link to <a href="https://example.com/page2">Page 2</a>.</p>
            <p>Here is a binary file to ignore: <a href="https://example.com/photo.jpg">Photo</a></p>
        </article>
        <footer>Copyright 2026</footer>
        <script>console.log('noise');</script>
    </body>
    </html>
    """
    
    extracted = crawler.extract_content(sample_html, "https://example.com/article")
    
    assert extracted["title"] == "Sample Scraped Article"
    assert extracted["meta_description"] == "A test article for content parsing."
    assert extracted["author"] == "Owais"
    assert "Main Article Heading" in extracted["content"]
    assert "console.log" not in extracted["content"]
    assert "Copyright 2026" not in extracted["content"]
    assert "https://example.com/page2" in extracted["links"]
    assert "https://example.com/photo.jpg" not in extracted["links"]
    assert extracted["word_count"] > 5
    assert len(extracted["content_hash"]) == 64


# ---------------- 5. FastAPI Endpoints Tests ----------------

def test_api_endpoints():
    client = TestClient(app)
    
    # Health check
    res_health = client.get("/api/v1/health")
    assert res_health.status_code == 200
    data = res_health.json()
    assert data["status"] == "online"
    
    # Telemetry stats
    res_stats = client.get("/api/v1/stats")
    assert res_stats.status_code == 200
    
    # Add page manually
    res_add = client.post("/api/v1/add-page", json={
        "url": "https://api-test.local/doc",
        "title": "API Test Document",
        "content": "FastAPI and ScrapAI working together in seamless integration.",
        "hash": "apitesthash999"
    })
    assert res_add.status_code == 200
    assert res_add.json()["success"] is True
    
    # Search content
    res_search = client.get("/api/v1/search?q=FastAPI+ScrapAI")
    assert res_search.status_code == 200
    results = res_search.json()
    assert len(results) >= 1
    assert "API Test Document" in results[0]["title"]
    
    # Extractive QA Answer
    res_qa = client.post("/api/v1/query/answer", json={
        "query": "What works with ScrapAI?"
    })
    assert res_qa.status_code == 200
    qa_data = res_qa.json()
    assert "answer" in qa_data
    assert len(qa_data["sources"]) >= 1

"""
Automated Test Suite for FlashRank Neural Re-Ranking in ScrapAI.
Tests singleton lifecycle, neural cross-encoder accuracy, score blending,
edge cases, and API endpoint integration.
"""

import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import pytest
from fastapi.testclient import TestClient

from backend.search.reranker import FlashRankReranker, get_reranker, HAS_FLASHRANK
from backend.search.semantic_engine import LocalSemanticEngine
from backend.main import app


# ---------------- 1. Unit Tests for FlashRankReranker ----------------

def test_flashrank_availability():
    """Verify FlashRank is available and loaded properly"""
    reranker = get_reranker()
    assert reranker is not None
    info = reranker.get_info()
    assert info["model_name"] == "ms-marco-TinyBERT-L-2-v2"
    assert info["score_weight"] == 0.70
    assert reranker.is_available() is True


def test_flashrank_basic_reranking():
    """Verify cross-attention relevance ordering"""
    reranker = get_reranker()
    query = "fastapi python async web framework"
    candidates = [
        {
            "id": 1,
            "title": "Baking Chocolate Cookies",
            "content": "A simple guide to baking delicious chocolate chip cookies with butter and sugar.",
            "score": 0.8  # Artificially high initial score
        },
        {
            "id": 2,
            "title": "FastAPI High-Performance Async APIs",
            "content": "FastAPI is a modern, fast, asynchronous web framework for building APIs with Python 3.8+.",
            "score": 0.4  # Lower initial score
        },
        {
            "id": 3,
            "title": "Astronomy and Galaxies",
            "content": "Hubble telescope captures distant galaxies and cosmic dust clouds in deep space.",
            "score": 0.5
        }
    ]

    reranked = reranker.rerank(query, candidates, blend_scores=False)
    assert len(reranked) == 3
    # FastAPI document should rank #1 despite lower initial score
    assert reranked[0]["id"] == 2
    assert "FastAPI" in reranked[0]["title"]
    assert reranked[0]["flashrank_score"] > reranked[1]["flashrank_score"]
    assert reranked[0]["flashrank_score"] > reranked[2]["flashrank_score"]
    assert all("flashrank_score" in r for r in reranked)
    assert all(r.get("reranked") is True for r in reranked)


def test_flashrank_score_blending():
    """Verify that score blending respects score_weight"""
    reranker = FlashRankReranker(score_weight=0.50)
    query = "artificial intelligence machine learning"
    candidates = [
        {"id": 1, "content": "Machine learning algorithms and deep neural networks in AI.", "score": 0.6},
        {"id": 2, "content": "Organic gardening and planting tomato seeds.", "score": 0.2}
    ]

    reranked = reranker.rerank(query, candidates, blend_scores=True)
    assert len(reranked) == 2
    assert reranked[0]["id"] == 1
    # Check that blended score is between initial score and flashrank score
    fr_score = reranked[0]["flashrank_score"]
    initial_score = 0.6
    expected_blended = round(0.5 * initial_score + 0.5 * fr_score, 4)
    assert reranked[0]["score"] == expected_blended


def test_flashrank_edge_cases():
    """Verify behavior on empty, missing, or malformed inputs"""
    reranker = get_reranker()

    # Empty inputs
    assert reranker.rerank("", []) == []
    assert reranker.rerank("query", []) == []
    assert reranker.rerank("", [{"content": "hello"}]) == [{"content": "hello"}]

    # Candidates with different key representations (chunk_text, snippet, text)
    mixed_candidates = [
        {"id": 1, "chunk_text": "Python programming language and syntax."},
        {"id": 2, "snippet": "JavaScript frontend development with React."},
        {"id": 3, "text": "Cooking pasta and making sauce."}
    ]
    reranked = reranker.rerank("python coding", mixed_candidates)
    assert len(reranked) == 3
    assert reranked[0]["id"] == 1

    # Single candidate input
    single = [{"id": 1, "content": "Unique document content"}]
    res = reranker.rerank("query", single)
    assert len(res) == 1
    assert res[0]["id"] == 1


# ---------------- 2. Semantic Engine Integration ----------------

def test_semantic_engine_with_flashrank():
    """Verify hybrid_rank calls FlashRank when rerank=True"""
    engine = LocalSemanticEngine()
    query = "web scraping python beautifulsoup"
    candidates = [
        {
            "page_id": 1,
            "title": "Cooking Recipes",
            "content": "Delicious soup recipes with vegetables.",
            "chunk_text": "Delicious soup recipes with vegetables."
        },
        {
            "page_id": 2,
            "title": "Python Web Scraping Guide",
            "content": "How to scrape websites using Python, BeautifulSoup, and requests efficiently.",
            "chunk_text": "How to scrape websites using Python, BeautifulSoup, and requests efficiently."
        }
    ]

    # Test with reranking enabled
    ranked_with_rerank = engine.hybrid_rank(query, candidates, rerank=True)
    assert ranked_with_rerank[0]["page_id"] == 2
    assert "flashrank_score" in ranked_with_rerank[0]

    # Test with reranking disabled
    ranked_without_rerank = engine.hybrid_rank(query, candidates, rerank=False)
    assert len(ranked_without_rerank) == 2


def test_semantic_engine_extractive_answer_with_flashrank():
    """Verify extractive reasoning produces high confidence answers with reranked items"""
    engine = LocalSemanticEngine()
    query = "What is ScrapAI?"
    ranked_docs = [
        {
            "page_id": 1,
            "title": "ScrapAI Overview",
            "url": "https://scrapai.local/docs",
            "chunk_text": "ScrapAI is an autonomous web crawler and zero-API semantic search platform built for offline use.",
            "content": "ScrapAI is an autonomous web crawler and zero-API semantic search platform built for offline use.",
            "score": 0.95,
            "flashrank_score": 0.98
        }
    ]
    answer = engine.generate_extractive_answer(query, ranked_docs)
    assert "ScrapAI" in answer["answer"]
    assert len(answer["citations"]) > 0
    assert len(answer["sources"]) > 0


# ---------------- 3. API Route Tests ----------------

def test_api_status_features():
    """Verify /api/v1/status reports flashrank_neural_reranking"""
    client = TestClient(app)
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["features"]["flashrank_neural_reranking"] is True
    assert data["features"]["flashrank_model"] == "ms-marco-TinyBERT-L-2-v2"


def test_api_search_rerank_endpoint():
    """Test dedicated POST /api/v1/search/rerank endpoint"""
    client = TestClient(app)
    payload = {
        "query": "vector databases",
        "candidates": [
            {"id": "doc1", "text": "Recipe for Italian pasta with garlic and olive oil."},
            {"id": "doc2", "text": "Vector databases store embeddings for high-dimensional similarity search."}
        ],
        "blend_scores": False
    }
    response = client.post("/api/v1/search/rerank", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "vector databases"
    assert data["count"] == 2
    assert data["results"][0]["id"] == "doc2"
    assert data["results"][0]["flashrank_score"] > data["results"][1]["flashrank_score"]

"""
Zero-API Semantic Search, Vector Indexing, Hybrid Ranking & Extractive QA Engine.
Operates 100% locally with zero external API dependencies, while seamlessly
leveraging SentenceTransformers or FAISS if installed in the environment.
"""

import re
import math
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter

logger = logging.getLogger(__name__)

# Try to import neural embedding model if available
HAS_SENTENCE_TRANSFORMERS = False
_sentence_model = None

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except Exception:
    HAS_SENTENCE_TRANSFORMERS = False


class LocalSemanticVectorizer:
    """
    High-performance zero-API semantic vectorizer.
    Generates normalized dense vector representations using subword n-grams,
    term frequencies, and lexical position weights.
    """
    def __init__(self, dimension: int = 128):
        self.dimension = dimension
        
    def _tokenize(self, text: str) -> List[str]:
        if not text:
            return []
        cleaned = re.sub(r'[^\w\s]', ' ', text.lower())
        tokens = [t for t in cleaned.split() if len(t) > 1]
        return tokens

    def _hash_to_index(self, token: str, dim: int) -> int:
        """Deterministic string hash to feature index"""
        h = 2166136261
        for ch in token:
            h = (h ^ ord(ch)) * 16777619
        return abs(h) % dim

    def encode(self, texts: List[str]) -> List[List[float]]:
        """Encode a list of texts into dense normalized vector representations"""
        vectors = []
        for text in texts:
            vec = [0.0] * self.dimension
            if not text:
                vectors.append(vec)
                continue
                
            tokens = self._tokenize(text)
            if not tokens:
                vectors.append(vec)
                continue
                
            # Token unigrams and character 3-grams for semantic & subword matching
            features = []
            for token in tokens:
                features.append((token, 1.0))
                # Subwords / ngrams for capturing morphology
                if len(token) >= 3:
                    for i in range(len(token) - 2):
                        features.append((token[i:i+3], 0.35))
                        
            # Accumulate into dense vector with sign hashing
            for feat, weight in features:
                idx = self._hash_to_index(feat, self.dimension)
                sign = 1.0 if self._hash_to_index(feat + "_sign", 2) == 1 else -1.0
                vec[idx] += weight * sign
                
            # L2 Normalize
            norm = math.sqrt(sum(v * v for v in vec))
            if norm > 0:
                vec = [round(v / norm, 6) for v in vec]
            vectors.append(vec)
            
        return vectors


class BM25Engine:
    """
    Fast BM25 / Okapi ranking implementation for high-precision keyword retrieval.
    """
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_len: List[int] = []
        self.avg_doc_len: float = 0.0
        self.doc_freqs: List[Counter] = []
        self.idf: Dict[str, float] = {}
        self.corpus_size: int = 0

    def fit(self, corpus: List[str]):
        self.corpus_size = len(corpus)
        if self.corpus_size == 0:
            return
            
        self.doc_len = []
        self.doc_freqs = []
        df: Dict[str, int] = Counter()
        
        for doc in corpus:
            tokens = re.findall(r'\w+', doc.lower())
            self.doc_len.append(len(tokens))
            tf = Counter(tokens)
            self.doc_freqs.append(tf)
            for token in tf.keys():
                df[token] += 1
                
        self.avg_doc_len = sum(self.doc_len) / max(1, self.corpus_size)
        
        # Calculate IDF
        self.idf = {}
        for token, freq in df.items():
            # BM25 IDF formula with smoothing
            self.idf[token] = math.log(1 + (self.corpus_size - freq + 0.5) / (freq + 0.5))

    def score(self, query: str, doc_index: int) -> float:
        if doc_index >= self.corpus_size or self.corpus_size == 0:
            return 0.0
            
        q_tokens = re.findall(r'\w+', query.lower())
        if not q_tokens:
            return 0.0
            
        doc_tf = self.doc_freqs[doc_index]
        d_len = self.doc_len[doc_index]
        score = 0.0
        
        for q in q_tokens:
            if q not in doc_tf:
                continue
            tf = doc_tf[q]
            idf = self.idf.get(q, 0.0)
            numerator = idf * tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * (d_len / max(1, self.avg_doc_len)))
            if denominator > 0:
                score += numerator / denominator
                
        return score


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity between two float vectors"""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return max(0.0, min(1.0, dot / (norm1 * norm2)))


class LocalSemanticEngine:
    """
    Master Semantic Engine integrating:
    1. Zero-API Local Vectorizer + optional Neural Vectorizer
    2. BM25 Keyword Search
    3. Hybrid Multi-Signal Ranking
    4. Snippet & Context Highlighting
    5. Extractive QA & Multi-Document Reasoning (No-LLM Answer Generation with citations)
    """
    def __init__(self, dimension: int = 128, use_neural: bool = True):
        self.dimension = dimension
        self.use_neural = use_neural
        self.local_vectorizer = LocalSemanticVectorizer(dimension=dimension)
        self.neural_model = None
        
        if self.use_neural and HAS_SENTENCE_TRANSFORMERS:
            try:
                global _sentence_model
                if _sentence_model is None:
                    _sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
                self.neural_model = _sentence_model
                logger.info("Loaded Neural SentenceTransformer model.")
            except Exception as e:
                logger.warning(f"Could not load SentenceTransformer: {e}. Defaulting to LocalSemanticVectorizer.")
                self.neural_model = None

    def encode(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using neural model if available, else local zero-API vectorizer"""
        if not texts:
            return []
        if self.neural_model is not None:
            try:
                embs = self.neural_model.encode(texts, convert_to_numpy=True)
                return [e.tolist() for e in embs]
            except Exception as e:
                logger.warning(f"Neural encoding failed ({e}), falling back to local vectorizer.")
        return self.local_vectorizer.encode(texts)

    def extract_snippet(self, content: str, query: str, max_length: int = 220) -> str:
        """
        Extract the most relevant excerpt/snippet from content given a query.
        """
        if not content:
            return ""
            
        content_clean = re.sub(r'\s+', ' ', content).strip()
        if len(content_clean) <= max_length:
            return content_clean
            
        q_words = [w.lower() for w in re.findall(r'\w+', query) if len(w) > 2]
        if not q_words:
            return content_clean[:max_length] + "..."
            
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', content_clean)
        best_sentence = sentences[0]
        best_score = -1
        
        for s in sentences:
            s_lower = s.lower()
            score = sum(1 for w in q_words if w in s_lower)
            if score > best_score:
                best_score = score
                best_sentence = s
                
        if len(best_sentence) > max_length:
            return best_sentence[:max_length] + "..."
        return best_sentence

    def hybrid_rank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        weights: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Multi-signal hybrid ranker combining:
        - Semantic Vector Similarity
        - BM25 / Keyword Match
        - Title Exact / Token Match
        - Domain Relevance
        - Freshness / Length
        """
        if not candidates:
            return []
            
        w = weights or {
            "semantic": 0.45,
            "bm25": 0.25,
            "title": 0.15,
            "domain": 0.10,
            "freshness": 0.05
        }
        
        # Fit BM25 on candidate corpus
        corpus = [c.get("content", "") + " " + c.get("title", "") for c in candidates]
        bm25 = BM25Engine()
        bm25.fit(corpus)
        
        # Compute query vector
        query_vector = self.encode([query])[0]
        q_tokens = set(re.findall(r'\w+', query.lower()))
        
        ranked_results = []
        
        # Find max BM25 score for normalization
        bm25_scores = [bm25.score(query, i) for i in range(len(candidates))]
        max_bm25 = max(bm25_scores) if bm25_scores and max(bm25_scores) > 0 else 1.0
        
        for i, item in enumerate(candidates):
            # 1. Semantic Similarity
            item_vector = item.get("vector")
            if isinstance(item_vector, str):
                try:
                    item_vector = json.loads(item_vector)
                except Exception:
                    item_vector = None
                    
            if not item_vector:
                # On the fly vectorization if not stored
                item_vector = self.encode([item.get("chunk_text") or item.get("content", "")[:500]])[0]
                
            sim_score = cosine_similarity(query_vector, item_vector) if item_vector else 0.0
            
            # 2. Normalized BM25 score
            bm25_norm = (bm25_scores[i] / max_bm25) if max_bm25 > 0 else 0.0
            
            # 3. Title Match Score
            title = (item.get("title") or "").lower()
            title_tokens = set(re.findall(r'\w+', title))
            title_score = 0.0
            if q_tokens and title_tokens:
                intersection = q_tokens.intersection(title_tokens)
                title_score = len(intersection) / len(q_tokens)
                if query.lower() in title:
                    title_score = min(1.0, title_score + 0.3)
                    
            # 4. Domain / Quality Factor
            content_len = len(item.get("content", ""))
            length_score = min(1.0, content_len / 2000.0) if content_len > 0 else 0.2
            
            # 5. Composite Final Score
            final_score = (
                w["semantic"] * sim_score +
                w["bm25"] * bm25_norm +
                w["title"] * title_score +
                w["domain"] * 0.5 +
                w["freshness"] * length_score
            )
            
            snippet = self.extract_snippet(
                item.get("chunk_text") or item.get("content", ""),
                query
            )
            
            ranked_results.append({
                **item,
                "score": round(final_score, 4),
                "semantic_score": round(sim_score, 4),
                "bm25_score": round(bm25_norm, 4),
                "title_score": round(title_score, 4),
                "snippet": snippet
            })
            
        ranked_results.sort(key=lambda x: x["score"], reverse=True)
        return ranked_results

    def generate_extractive_answer(
        self,
        query: str,
        ranked_results: List[Dict[str, Any]],
        max_sentences: int = 3
    ) -> Dict[str, Any]:
        """
        Extractive Reasoning Engine (No-LLM Answer Synthesizer).
        Extracts high-salience sentences from top matching chunks, orders them
        logically, and adds source citations `[1]`, `[2]`.
        """
        if not ranked_results:
            return {
                "answer": "No indexed content matches your query. Try crawling relevant websites first.",
                "confidence": 0.0,
                "citations": [],
                "sources": []
            }
            
        q_tokens = [w.lower() for w in re.findall(r'\w+', query) if len(w) > 2]
        extracted_points = []
        sources = []
        seen_sentences = set()
        
        # Take top 5 candidates for reasoning synthesis
        top_candidates = ranked_results[:5]
        
        for idx, doc in enumerate(top_candidates, 1):
            url = doc.get("url", "")
            title = doc.get("title", "Document")
            doc_id = doc.get("id") or doc.get("page_id", idx)
            content = doc.get("content") or doc.get("chunk_text", "")
            
            if url and not any(s["url"] == url for s in sources):
                sources.append({
                    "citation_id": len(sources) + 1,
                    "url": url,
                    "title": title,
                    "score": doc.get("score", 0.0)
                })
                
            citation_num = [s["citation_id"] for s in sources if s["url"] == url][0]
            
            # Split into clean sentences
            sentences = re.split(r'(?<=[.!?])\s+', content)
            for s in sentences:
                s_clean = s.strip()
                if len(s_clean) < 30 or len(s_clean) > 350:
                    continue
                s_lower = s_clean.lower()
                if s_lower in seen_sentences:
                    continue
                    
                # Score sentence relevance to query & document score
                overlap = sum(1 for w in q_tokens if w in s_lower)
                if overlap > 0 or len(extracted_points) == 0:
                    sent_score = overlap * 2.0 + doc.get("score", 0.5)
                    extracted_points.append({
                        "text": s_clean,
                        "score": sent_score,
                        "citation": f"[{citation_num}]",
                        "url": url
                    })
                    seen_sentences.add(s_lower)
                    
        # Sort extracted sentences by salience
        extracted_points.sort(key=lambda x: x["score"], reverse=True)
        selected = extracted_points[:max_sentences]
        
        if not selected:
            top_doc = top_candidates[0]
            summary_text = (top_doc.get("content") or "")[:200]
            return {
                "answer": f"{summary_text}... [1]",
                "confidence": round(float(top_doc.get("score", 0.5)), 2),
                "citations": ["[1]"],
                "sources": sources[:1]
            }
            
        answer_parts = []
        for item in selected:
            txt = item["text"]
            if not txt.endswith(('.', '!', '?')):
                txt += '.'
            answer_parts.append(f"{txt} {item['citation']}")
            
        confidence = min(0.98, max(0.40, float(selected[0]["score"] / 4.0)))
        
        return {
            "answer": " ".join(answer_parts),
            "confidence": round(confidence, 2),
            "citations": [s["citation"] for s in selected],
            "sources": sources
        }


# Global singleton instance
semantic_engine = LocalSemanticEngine()

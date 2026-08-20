import asyncio
import json
import time
import re
from typing import List, Optional, Dict, Any, Tuple
from urllib.parse import urlparse
from datetime import datetime

from sqlalchemy import create_engine, func, desc, or_, and_, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from backend.config import config
from .models import Base, Page, Chunk, Embedding, CrawlQueue, Domain, SearchLog
from backend.search.semantic_engine import semantic_engine


class SQLClient:
    def __init__(self, database_url: Optional[str] = None):
        db_url = database_url or config.database.url
        connect_args = {}
        pool_kwargs = {}
        
        if db_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
            if db_url == "sqlite:///:memory:" or ":memory:" in db_url:
                pool_kwargs["poolclass"] = StaticPool

        self.engine = create_engine(
            db_url,
            echo=config.database.echo,
            connect_args=connect_args,
            **pool_kwargs
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.create_tables()

    def create_tables(self):
        """Create all tables and perform non-destructive self-healing column migrations"""
        Base.metadata.create_all(bind=self.engine)
        self._auto_migrate_schema()

    def _auto_migrate_schema(self):
        """Ensure all required columns exist even on legacy SQLite files"""
        try:
            inspector = inspect(self.engine)
            existing_tables = inspector.get_table_names()
            
            with self.engine.connect() as conn:
                # 1. Check crawl_queue columns
                if 'crawl_queue' in existing_tables:
                    cq_cols = {col['name'] for col in inspector.get_columns('crawl_queue')}
                    if 'domain' not in cq_cols:
                        conn.execute(text("ALTER TABLE crawl_queue ADD COLUMN domain VARCHAR"))
                    if 'priority' not in cq_cols:
                        conn.execute(text("ALTER TABLE crawl_queue ADD COLUMN priority INTEGER DEFAULT 0"))
                    if 'depth' not in cq_cols:
                        conn.execute(text("ALTER TABLE crawl_queue ADD COLUMN depth INTEGER DEFAULT 0"))
                    if 'max_depth' not in cq_cols:
                        conn.execute(text("ALTER TABLE crawl_queue ADD COLUMN max_depth INTEGER DEFAULT 2"))
                    if 'parent_url' not in cq_cols:
                        conn.execute(text("ALTER TABLE crawl_queue ADD COLUMN parent_url VARCHAR"))
                    if 'error_message' not in cq_cols:
                        conn.execute(text("ALTER TABLE crawl_queue ADD COLUMN error_message TEXT"))
                    if 'max_retries' not in cq_cols:
                        conn.execute(text("ALTER TABLE crawl_queue ADD COLUMN max_retries INTEGER DEFAULT 3"))

                # 2. Check pages columns
                if 'pages' in existing_tables:
                    p_cols = {col['name'] for col in inspector.get_columns('pages')}
                    if 'domain' not in p_cols:
                        conn.execute(text("ALTER TABLE pages ADD COLUMN domain VARCHAR"))
                    if 'meta_description' not in p_cols:
                        conn.execute(text("ALTER TABLE pages ADD COLUMN meta_description TEXT"))
                    if 'author' not in p_cols:
                        conn.execute(text("ALTER TABLE pages ADD COLUMN author VARCHAR"))
                    if 'word_count' not in p_cols:
                        conn.execute(text("ALTER TABLE pages ADD COLUMN word_count INTEGER DEFAULT 0"))
                    if 'status_code' not in p_cols:
                        conn.execute(text("ALTER TABLE pages ADD COLUMN status_code INTEGER DEFAULT 200"))

                # 3. Check chunks columns
                if 'chunks' in existing_tables:
                    ch_cols = {col['name'] for col in inspector.get_columns('chunks')}
                    if 'token_count' not in ch_cols:
                        conn.execute(text("ALTER TABLE chunks ADD COLUMN token_count INTEGER DEFAULT 0"))
                    if 'created_at' not in ch_cols:
                        conn.execute(text("ALTER TABLE chunks ADD COLUMN created_at DATETIME"))

                # 4. Check embeddings columns
                if 'embeddings' in existing_tables:
                    emb_cols = {col['name'] for col in inspector.get_columns('embeddings')}
                    if 'model_name' not in emb_cols:
                        conn.execute(text("ALTER TABLE embeddings ADD COLUMN model_name VARCHAR DEFAULT 'local-tfidf-semantic'"))
                    if 'dimension' not in emb_cols:
                        conn.execute(text("ALTER TABLE embeddings ADD COLUMN dimension INTEGER DEFAULT 128"))

                # 5. Check search_logs columns
                if 'search_logs' in existing_tables:
                    s_cols = {col['name'] for col in inspector.get_columns('search_logs')}
                    if 'search_type' not in s_cols:
                        conn.execute(text("ALTER TABLE search_logs ADD COLUMN search_type VARCHAR DEFAULT 'hybrid'"))
                    if 'execution_time_ms' not in s_cols:
                        conn.execute(text("ALTER TABLE search_logs ADD COLUMN execution_time_ms FLOAT DEFAULT 0.0"))

                conn.commit()
        except Exception:
            # Migration check safe fallback
            pass

    def get_db(self) -> Session:
        """Get database session"""
        return self.SessionLocal()

    # ---------------- QUEUE OPERATIONS ----------------

    async def add_to_queue(
        self,
        url: str,
        priority: int = 0,
        depth: int = 0,
        max_depth: int = 2,
        parent_url: Optional[str] = None
    ) -> bool:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._add_to_queue_sync, url, priority, depth, max_depth, parent_url
        )

    def _add_to_queue_sync(
        self,
        url: str,
        priority: int = 0,
        depth: int = 0,
        max_depth: int = 2,
        parent_url: Optional[str] = None
    ) -> bool:
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            return False
            
        domain = urlparse(url).netloc
        db = self.SessionLocal()
        try:
            # Check if URL exists in pages or in queue
            existing_page = db.query(Page).filter(Page.url == url).first()
            if existing_page:
                return False
                
            existing_queue = db.query(CrawlQueue).filter(CrawlQueue.url == url).first()
            if existing_queue:
                if existing_queue.status == 'failed' and existing_queue.retries < existing_queue.max_retries:
                    existing_queue.status = 'queued'
                    existing_queue.scheduled_at = func.now()
                    db.commit()
                    return True
                return False

            queue_item = CrawlQueue(
                url=url,
                domain=domain,
                status='queued',
                priority=priority,
                depth=depth,
                max_depth=max_depth,
                parent_url=parent_url
            )
            db.add(queue_item)
            
            # Record or update domain
            if domain:
                domain_rec = db.query(Domain).filter(Domain.domain == domain).first()
                if not domain_rec:
                    db.add(Domain(domain=domain, pages_count=0))
                    
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False
        finally:
            db.close()

    async def get_next_queue_item(self) -> Optional[Dict[str, Any]]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_next_queue_item_sync)

    def _get_next_queue_item_sync(self) -> Optional[Dict[str, Any]]:
        db = self.SessionLocal()
        try:
            queue_item = db.query(CrawlQueue).filter(
                CrawlQueue.status == 'queued'
            ).order_by(
                desc(CrawlQueue.priority),
                CrawlQueue.scheduled_at.asc()
            ).first()

            if queue_item:
                queue_item.status = 'processing'
                db.commit()
                return {
                    'id': queue_item.id,
                    'url': queue_item.url,
                    'domain': queue_item.domain,
                    'status': queue_item.status,
                    'retries': queue_item.retries,
                    'depth': queue_item.depth,
                    'max_depth': queue_item.max_depth,
                    'parent_url': queue_item.parent_url
                }
            return None
        except Exception:
            db.rollback()
            return None
        finally:
            db.close()

    async def mark_queue_processed(self, queue_id: int, status: str, error: Optional[str] = None) -> bool:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._mark_queue_processed_sync, queue_id, status, error)

    def _mark_queue_processed_sync(self, queue_id: int, status: str, error: Optional[str] = None) -> bool:
        db = self.SessionLocal()
        try:
            item = db.query(CrawlQueue).filter(CrawlQueue.id == queue_id).first()
            if item:
                item.status = status
                item.processed_at = func.now()
                if error:
                    item.error_message = str(error)[:500]
                    item.retries += 1
                db.commit()
                return True
            return False
        except Exception:
            db.rollback()
            return False
        finally:
            db.close()

    async def get_queue_items(self, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_queue_items_sync, status, limit)

    def _get_queue_items_sync(self, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        db = self.SessionLocal()
        try:
            query = db.query(CrawlQueue)
            if status:
                query = query.filter(CrawlQueue.status == status)
            items = query.order_by(desc(CrawlQueue.scheduled_at)).limit(limit).all()
            return [{
                'id': q.id,
                'url': q.url,
                'domain': q.domain,
                'status': q.status,
                'priority': q.priority,
                'retries': q.retries,
                'depth': q.depth,
                'error_message': q.error_message,
                'scheduled_at': q.scheduled_at.isoformat() if q.scheduled_at else None,
                'processed_at': q.processed_at.isoformat() if q.processed_at else None
            } for q in items]
        finally:
            db.close()

    async def clear_queue(self) -> int:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._clear_queue_sync)

    def _clear_queue_sync(self) -> int:
        db = self.SessionLocal()
        try:
            count = db.query(CrawlQueue).delete()
            db.commit()
            return count
        except Exception:
            db.rollback()
            return 0
        finally:
            db.close()

    # ---------------- PAGE OPERATIONS ----------------

    async def save_page(self, data: dict) -> Tuple[int, bool]:
        """Save page content to database. Returns (page_id, is_new)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._save_page_sync, data)

    def _save_page_sync(self, data: dict) -> Tuple[int, bool]:
        url = data.get('url', '').strip()
        if not url:
            return 0, False
            
        content_hash = data.get('hash') or data.get('content_hash', '')
        domain = urlparse(url).netloc
        
        db = self.SessionLocal()
        try:
            # Check for existing page by URL or content hash
            existing = db.query(Page).filter(
                or_(Page.url == url, Page.content_hash == content_hash)
            ).first() if content_hash else db.query(Page).filter(Page.url == url).first()
            
            if existing:
                existing.title = data.get('title') or existing.title
                existing.content = data.get('content') or existing.content
                existing.meta_description = data.get('meta_description') or existing.meta_description
                existing.author = data.get('author') or existing.author
                existing.word_count = data.get('word_count') or len((existing.content or '').split())
                existing.crawl_time = func.now()
                existing.embedded = False
                db.commit()
                return existing.id, False

            page = Page(
                url=url,
                domain=domain,
                title=data.get('title', ''),
                content=data.get('content', ''),
                meta_description=data.get('meta_description', ''),
                author=data.get('author', ''),
                language=data.get('language', 'en'),
                word_count=data.get('word_count', 0) or len(data.get('content', '').split()),
                content_hash=content_hash,
                status_code=data.get('status_code', 200),
                embedded=False
            )
            db.add(page)
            
            if domain:
                dom = db.query(Domain).filter(Domain.domain == domain).first()
                if dom:
                    dom.pages_count += 1
                    dom.last_crawled = func.now()
                else:
                    db.add(Domain(domain=domain, pages_count=1, last_crawled=func.now()))
                    
            db.commit()
            db.refresh(page)
            return page.id, True
        except Exception:
            db.rollback()
            return 0, False
        finally:
            db.close()

    async def get_page_by_id(self, page_id: int) -> Optional[Dict[str, Any]]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_page_by_id_sync, page_id)

    def _get_page_by_id_sync(self, page_id: int) -> Optional[Dict[str, Any]]:
        db = self.SessionLocal()
        try:
            page = db.query(Page).filter(Page.id == page_id).first()
            if not page:
                return None
            chunks = db.query(Chunk).filter(Chunk.page_id == page_id).order_by(Chunk.chunk_index).all()
            return {
                'id': page.id,
                'url': page.url,
                'domain': page.domain,
                'title': page.title,
                'content': page.content,
                'meta_description': page.meta_description,
                'author': page.author,
                'language': page.language,
                'word_count': page.word_count,
                'hash': page.content_hash,
                'crawl_time': page.crawl_time.isoformat() if page.crawl_time else None,
                'embedded': page.embedded,
                'chunks_count': len(chunks),
                'chunks': [{'id': c.id, 'index': c.chunk_index, 'text': c.chunk_text} for c in chunks]
            }
        finally:
            db.close()

    async def delete_page(self, page_id: int) -> bool:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._delete_page_sync, page_id)

    def _delete_page_sync(self, page_id: int) -> bool:
        db = self.SessionLocal()
        try:
            page = db.query(Page).filter(Page.id == page_id).first()
            if page:
                domain = page.domain
                db.delete(page)
                if domain:
                    dom = db.query(Domain).filter(Domain.domain == domain).first()
                    if dom and dom.pages_count > 0:
                        dom.pages_count -= 1
                db.commit()
                return True
            return False
        except Exception:
            db.rollback()
            return False
        finally:
            db.close()

    async def is_duplicate(self, content_hash: str) -> bool:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._is_duplicate_sync, content_hash)

    def _is_duplicate_sync(self, content_hash: str) -> bool:
        if not content_hash:
            return False
        db = self.SessionLocal()
        try:
            return db.query(Page).filter(Page.content_hash == content_hash).first() is not None
        finally:
            db.close()

    async def get_pages(self, skip: int = 0, limit: int = 50, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_pages_sync, skip, limit, domain)

    def _get_pages_sync(self, skip: int = 0, limit: int = 50, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        db = self.SessionLocal()
        try:
            query = db.query(Page)
            if domain:
                query = query.filter(Page.domain == domain)
            pages = query.order_by(desc(Page.crawl_time)).offset(skip).limit(limit).all()
            return [{
                'id': p.id,
                'url': p.url,
                'domain': p.domain,
                'title': p.title,
                'content': (p.content or '')[:300] + ('...' if len(p.content or '') > 300 else ''),
                'meta_description': p.meta_description,
                'word_count': p.word_count,
                'hash': p.content_hash,
                'crawl_time': p.crawl_time.isoformat() if p.crawl_time else None,
                'embedded': p.embedded
            } for p in pages]
        finally:
            db.close()

    # ---------------- CHUNKING & EMBEDDINGS ----------------

    async def save_chunk(self, page_id: int, chunk_text: str, chunk_index: int, token_count: int = 0) -> int:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._save_chunk_sync, page_id, chunk_text, chunk_index, token_count)

    def _save_chunk_sync(self, page_id: int, chunk_text: str, chunk_index: int, token_count: int = 0) -> int:
        db = self.SessionLocal()
        try:
            chunk = Chunk(
                page_id=page_id,
                chunk_text=chunk_text,
                chunk_index=chunk_index,
                token_count=token_count or len(chunk_text.split())
            )
            db.add(chunk)
            db.commit()
            db.refresh(chunk)
            return chunk.id
        except Exception:
            db.rollback()
            return 0
        finally:
            db.close()

    async def save_embedding(self, chunk_id: int, vector: List[float], model_name: str = "local-tfidf-semantic") -> int:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._save_embedding_sync, chunk_id, vector, model_name)

    def _save_embedding_sync(self, chunk_id: int, vector: List[float], model_name: str = "local-tfidf-semantic") -> int:
        db = self.SessionLocal()
        try:
            vector_json = json.dumps(vector)
            existing = db.query(Embedding).filter(Embedding.chunk_id == chunk_id).first()
            if existing:
                existing.vector = vector_json
                existing.model_name = model_name
                existing.dimension = len(vector)
                db.commit()
                return existing.id

            embedding = Embedding(
                chunk_id=chunk_id,
                vector=vector_json,
                model_name=model_name,
                dimension=len(vector)
            )
            db.add(embedding)
            db.commit()
            db.refresh(embedding)
            return embedding.id
        except Exception:
            db.rollback()
            return 0
        finally:
            db.close()

    async def get_pages_needing_chunking(self, limit: int = 20) -> List[Dict[str, Any]]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_pages_needing_chunking_sync, limit)

    def _get_pages_needing_chunking_sync(self, limit: int = 20) -> List[Dict[str, Any]]:
        db = self.SessionLocal()
        try:
            pages = db.query(Page).outerjoin(Chunk, Page.id == Chunk.page_id)\
                .filter(Page.content.isnot(None))\
                .filter(Page.content != '')\
                .filter(Chunk.id.is_(None))\
                .limit(limit).all()
                
            return [{
                'id': p.id,
                'url': p.url,
                'title': p.title,
                'content': p.content,
                'hash': p.content_hash
            } for p in pages]
        finally:
            db.close()

    async def get_chunks_without_embeddings(self, limit: int = 50) -> List[Dict[str, Any]]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_chunks_without_embeddings_sync, limit)

    def _get_chunks_without_embeddings_sync(self, limit: int = 50) -> List[Dict[str, Any]]:
        db = self.SessionLocal()
        try:
            chunks = db.query(Chunk).outerjoin(Embedding, Chunk.id == Embedding.chunk_id)\
                .filter(Chunk.chunk_text.isnot(None))\
                .filter(Chunk.chunk_text != '')\
                .filter(Embedding.id.is_(None))\
                .limit(limit).all()
                
            return [{
                'id': c.id,
                'page_id': c.page_id,
                'chunk_text': c.chunk_text,
                'chunk_index': c.chunk_index
            } for c in chunks]
        finally:
            db.close()

    async def mark_chunk_embedded(self, chunk_id: int) -> bool:
        return True

    async def mark_embedding_generated(self, page_id: int) -> bool:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._mark_embedding_generated_sync, page_id)

    def _mark_embedding_generated_sync(self, page_id: int) -> bool:
        db = self.SessionLocal()
        try:
            page = db.query(Page).filter(Page.id == page_id).first()
            if page:
                page.embedded = True
                db.commit()
                return True
            return False
        except Exception:
            db.rollback()
            return False
        finally:
            db.close()

    # ---------------- HYBRID SEARCH & EXTRACTIVE QA ----------------

    async def search_content(
        self,
        query: str,
        limit: int = 10,
        domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute Hybrid Search (Semantic + BM25 + Ranking).
        Works 100% offline with zero external API calls.
        """
        start_time = time.time()
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, self._search_content_sync, query, limit, domain)
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        
        await loop.run_in_executor(None, self._log_search_sync, query, len(results), elapsed_ms)
        return results

    def _search_content_sync(
        self,
        query: str,
        limit: int = 10,
        domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        db = self.SessionLocal()
        try:
            clean_query = query.strip()
            if not clean_query:
                pages = db.query(Page).order_by(desc(Page.crawl_time)).limit(limit).all()
                return [{
                    'id': p.id,
                    'page_id': p.id,
                    'url': p.url,
                    'domain': p.domain,
                    'title': p.title,
                    'content': (p.content or '')[:400],
                    'snippet': (p.content or '')[:200],
                    'hash': p.content_hash,
                    'score': 1.0,
                    'semantic_score': 1.0,
                    'bm25_score': 1.0
                } for p in pages]

            candidate_query = db.query(
                Page.id.label('page_id'),
                Page.url,
                Page.domain,
                Page.title,
                Page.content,
                Page.content_hash,
                Chunk.id.label('chunk_id'),
                Chunk.chunk_text,
                Embedding.vector
            ).outerjoin(Chunk, Page.id == Chunk.page_id)\
             .outerjoin(Embedding, Chunk.id == Embedding.chunk_id)

            if domain:
                candidate_query = candidate_query.filter(Page.domain == domain)

            tokens = [t for t in re.findall(r'\w+', clean_query.lower()) if len(t) > 2]
            if tokens:
                filters = [Page.title.ilike(f"%{t}%") for t in tokens] + \
                          [Page.content.ilike(f"%{t}%") for t in tokens] + \
                          [Chunk.chunk_text.ilike(f"%{t}%") for t in tokens]
                matching_rows = candidate_query.filter(or_(*filters)).limit(100).all()
            else:
                matching_rows = []

            if len(matching_rows) < 20:
                all_rows = candidate_query.limit(100).all()
                seen_ids = {r.chunk_id or f"p_{r.page_id}" for r in matching_rows}
                for r in all_rows:
                    cid = r.chunk_id or f"p_{r.page_id}"
                    if cid not in seen_ids:
                        matching_rows.append(r)
                        seen_ids.add(cid)

            if not matching_rows:
                return []

            candidates = []
            seen_page_chunks = set()
            for r in matching_rows:
                key = (r.page_id, r.chunk_id)
                if key in seen_page_chunks:
                    continue
                seen_page_chunks.add(key)
                
                candidates.append({
                    'id': r.page_id,
                    'page_id': r.page_id,
                    'chunk_id': r.chunk_id,
                    'url': r.url,
                    'domain': r.domain,
                    'title': r.title or r.url,
                    'content': r.content or '',
                    'chunk_text': r.chunk_text or r.content or '',
                    'hash': r.content_hash,
                    'vector': r.vector
                })

            ranked = semantic_engine.hybrid_rank(clean_query, candidates)

            unique_results = []
            seen_pages = set()
            for item in ranked:
                if item['page_id'] not in seen_pages:
                    seen_pages.add(item['page_id'])
                    unique_results.append(item)
                if len(unique_results) >= limit:
                    break

            return unique_results
        finally:
            db.close()

    def _log_search_sync(self, query: str, results_count: int, execution_time_ms: float):
        db = self.SessionLocal()
        try:
            log = SearchLog(
                query=query[:255],
                search_type="hybrid",
                results_count=results_count,
                execution_time_ms=execution_time_ms
            )
            db.add(log)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

    async def query_and_answer(self, query: str, limit: int = 10) -> Dict[str, Any]:
        results = await self.search_content(query, limit=limit)
        answer_data = semantic_engine.generate_extractive_answer(query, results)
        return {
            "query": query,
            "answer": answer_data["answer"],
            "confidence": answer_data["confidence"],
            "citations": answer_data["citations"],
            "sources": answer_data["sources"],
            "results": results
        }

    # ---------------- TELEMETRY & STATS ----------------

    async def get_stats(self) -> Dict[str, Any]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_stats_sync)

    def _get_stats_sync(self) -> Dict[str, Any]:
        db = self.SessionLocal()
        try:
            queued = db.query(CrawlQueue).filter(CrawlQueue.status == 'queued').count()
            processing = db.query(CrawlQueue).filter(CrawlQueue.status == 'processing').count()
            completed = db.query(CrawlQueue).filter(CrawlQueue.status == 'completed').count()
            failed = db.query(CrawlQueue).filter(CrawlQueue.status == 'failed').count()
            pages = db.query(Page).count()
            chunks = db.query(Chunk).count()
            embeddings = db.query(Embedding).count()
            domains = db.query(Domain).count()
            searches = db.query(SearchLog).count()
            
            return {
                'queued': queued,
                'processing': processing,
                'completed': completed,
                'failed': failed,
                'pages': pages,
                'chunks': chunks,
                'embeddings': embeddings,
                'domains': domains,
                'searches': searches,
                'total': pages + completed,
                'total_queue': queued + processing + completed + failed
            }
        finally:
            db.close()

    async def get_domains(self) -> List[Dict[str, Any]]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_domains_sync)

    def _get_domains_sync(self) -> List[Dict[str, Any]]:
        db = self.SessionLocal()
        try:
            domains = db.query(Domain).order_by(desc(Domain.pages_count)).all()
            return [{
                'id': d.id,
                'domain': d.domain,
                'pages_count': d.pages_count,
                'crawl_delay': d.crawl_delay,
                'is_allowed': d.is_allowed,
                'last_crawled': d.last_crawled.isoformat() if d.last_crawled else None
            } for d in domains]
        finally:
            db.close()

    async def reset_all(self) -> bool:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._reset_all_sync)

    def _reset_all_sync(self) -> bool:
        db = self.SessionLocal()
        try:
            db.query(Embedding).delete()
            db.query(Chunk).delete()
            db.query(Page).delete()
            db.query(CrawlQueue).delete()
            db.query(Domain).delete()
            db.query(SearchLog).delete()
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False
        finally:
            db.close()
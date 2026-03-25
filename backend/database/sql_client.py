from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from typing import List, Optional, Dict, Any
import asyncio
import json
from datetime import datetime

from .models import Base, Page, Chunk, Embedding, CrawlQueue, SearchLog

Base = declarative_base()

class Page(Base):
    __tablename__ = 'pages'
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True, nullable=False)
    title = Column(String)
    content = Column(Text)
    content_hash = Column(String, unique=True, index=True)
    language = Column(String)
    crawl_time = Column(DateTime, default=func.now())
    embedded = Column(Boolean, default=False)
    
    # Indexes for better search performance
    __table_args__ = (
        Index('idx_url', 'url'),
        Index('idx_content_hash', 'content_hash'),
        Index('idx_embedded', 'embedded'),
    )

class Chunk(Base):
    __tablename__ = 'chunks'
    
    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, index=True, nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_page_id', 'page_id'),
        Index('idx_chunk_text', 'chunk_text'),
    )

class Embedding(Base):
    __tablename__ = 'embeddings'
    
    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(Integer, index=True, nullable=False)
    vector = Column(Text)  # Storing as JSON for simplicity, could use specialized vector types
    created_at = Column(DateTime, default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_chunk_id', 'chunk_id'),
    )

class CrawlQueue(Base):
    __tablename__ = 'crawl_queue'
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, index=True, nullable=False)
    status = Column(String, default='queued')  # queued, processing, completed, failed
    retries = Column(Integer, default=0)
    priority = Column(Integer, default=0)
    scheduled_at = Column(DateTime, default=func.now())
    processed_at = Column(DateTime, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_url_status', 'url', 'status'),
        Index('idx_status', 'status'),
        Index('idx_priority', 'priority'),
    )

class SearchLog(Base):
    __tablename__ = 'search_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, index=True)
    results_count = Column(Integer, default=0)
    timestamp = Column(DateTime, default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_query', 'query'),
        Index('idx_timestamp', 'timestamp'),
    )

class SQLClient:
    def __init__(self, database_url: str = "sqlite:///./scrapai.db"):
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_db(self) -> Session:
        """Get database session"""
        db = self.SessionLocal()
        try:
            return db
        finally:
            pass  # Caller should close the session
    
    async def add_to_queue(self, url: str) -> bool:
        """Add URL to crawl queue"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._add_to_queue_sync, url)
    
    def _add_to_queue_sync(self, url: str) -> bool:
        db = self.SessionLocal()
        try:
            # Check if URL already exists in queue
            existing = db.query(CrawlQueue).filter(CrawlQueue.url == url).first()
            if existing:
                return False
            
            queue_item = CrawlQueue(url=url)
            db.add(queue_item)
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False
        finally:
            db.close()
    
    async def get_next_queue_item(self) -> Optional[Dict[str, Any]]:
        """Get next item from queue for processing"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_next_queue_item_sync)
    
    def _get_next_queue_item_sync(self) -> Optional[Dict[str, Any]]:
        db = self.SessionLocal()
        try:
            # Get oldest queued item
            queue_item = db.query(CrawlQueue).filter(
                CrawlQueue.status == 'queued'
            ).order_by(CrawlQueue.scheduled_at.asc()).first()
            
            if queue_item:
                # Mark as processing
                queue_item.status = 'processing'
                db.commit()
                
                return {
                    'id': queue_item.id,
                    'url': queue_item.url,
                    'status': queue_item.status,
                    'retries': queue_item.retries
                }
            return None
        except Exception:
            db.rollback()
            return None
        finally:
            db.close()
    
    async def save_page(self, data: dict) -> int:
        """Save page content to database"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._save_page_sync, data)
    
    def _save_page_sync(self, data: dict) -> int:
        db = self.SessionLocal()
        try:
            # Check for duplicate content hash
            if 'hash' in data and data['hash']:
                existing = db.query(Page).filter(Page.content_hash == data['hash']).first()
                if existing:
                    return existing.id
            
            page = Page(
                url=data.get('url', ''),
                title=data.get('title', ''),
                content=data.get('content', ''),
                content_hash=data.get('hash', ''),
                language=data.get('language', 'en')
            )
            db.add(page)
            db.commit()
            db.refresh(page)
            return page.id
        except Exception:
            db.rollback()
            return 0
        finally:
            db.close()
    
    async def is_duplicate(self, content_hash: str) -> bool:
        """Check if content already exists"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._is_duplicate_sync, content_hash)
    
    def _is_duplicate_sync(self, content_hash: str) -> bool:
        db = self.SessionLocal()
        try:
            return db.query(Page).filter(Page.content_hash == content_hash).first() is not None
        finally:
            db.close()
    
    async def mark_queue_processed(self, queue_id: int, status: str) -> bool:
        """Mark queue item as processed"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._mark_queue_processed_sync, queue_id, status)
    
    def _mark_queue_processed_sync(self, queue_id: int, status: str) -> bool:
        db = self.SessionLocal()
        try:
            queue_item = db.query(CrawlQueue).filter(CrawlQueue.id == queue_id).first()
            if queue_item:
                queue_item.status = status
                queue_item.processed_at = func.now()
                db.commit()
                return True
            return False
        except Exception:
            db.rollback()
            return False
        finally:
            db.close()
    
    async def save_chunk(self, page_id: int, chunk_text: str, chunk_index: int) -> int:
        """Save text chunk associated with a page"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._save_chunk_sync, page_id, chunk_text, chunk_index)
    
    def _save_chunk_sync(self, page_id: int, chunk_text: str, chunk_index: int) -> int:
        db = self.SessionLocal()
        try:
            chunk = Chunk(
                page_id=page_id,
                chunk_text=chunk_text,
                chunk_index=chunk_index
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
    
    async def save_embedding(self, chunk_id: int, vector: List[float]) -> int:
        """Save embedding vector for a chunk"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._save_embedding_sync, chunk_id, vector)
    
    def _save_embedding_sync(self, chunk_id: int, vector: List[float]) -> int:
        db = self.SessionLocal()
        try:
            # Store vector as JSON string
            vector_json = json.dumps(vector)
            embedding = Embedding(
                chunk_id=chunk_id,
                vector=vector_json
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
    
    async def get_pages_without_embeddings(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get pages that don't have embeddings yet"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_pages_without_embeddings_sync, limit)
    
    def _get_pages_without_embeddings_sync(self, limit: int = 10) -> List[Dict[str, Any]]:
        db = self.SessionLocal()
        try:
            # Get pages that have chunks but no embeddings
            pages = db.query(Page).join(Chunk, Page.id == Chunk.page_id, isouter=True)\
                .outerjoin(Embedding, Chunk.id == Embedding.chunk_id)\
                .filter(Page.embedded == False)\
                .filter(Embedding.id.is_(None))\
                .limit(limit)\
                .all()
            
            result = []
            for page in pages:
                result.append({
                    'id': page.id,
                    'url': page.url,
                    'title': page.title,
                    'content': page.content,
                    'hash': page.content_hash
                })
            return result
        finally:
            db.close()
            
    async def get_pages_needing_chunking(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get pages that have content but no chunks"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_pages_needing_chunking_sync, limit)
    
    def _get_pages_needing_chunking_sync(self, limit: int = 10) -> List[Dict[str, Any]]:
        db = self.SessionLocal()
        try:
            # Get pages that have content but no chunks
            pages = db.query(Page).outerjoin(Chunk, Page.id == Chunk.page_id)\
                .filter(Page.content.isnot(None))\
                .filter(Page.content != '')\
                .filter(Chunk.id.is_(None))\
                .limit(limit)\
                .all()
            
            result = []
            for page in pages:
                result.append({
                    'id': page.id,
                    'url': page.url,
                    'title': page.title,
                    'content': page.content,
                    'hash': page.content_hash
                })
            return result
        finally:
            db.close()
            
    async def get_chunks_without_embeddings(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get chunks that don't have embeddings yet"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_chunks_without_embeddings_sync, limit)
    
    def _get_chunks_without_embeddings_sync(self, limit: int = 10) -> List[Dict[str, Any]]:
        db = self.SessionLocal()
        try:
            # Get chunks that don't have embeddings
            chunks = db.query(Chunk).outerjoin(Embedding, Chunk.id == Embedding.chunk_id)\
                .filter(Chunk.chunk_text.isnot(None))\
                .filter(Chunk.chunk_text != '')\
                .filter(Embedding.id.is_(None))\
                .limit(limit)\
                .all()
            
            result = []
            for chunk in chunks:
                result.append({
                    'id': chunk.id,
                    'page_id': chunk.page_id,
                    'chunk_text': chunk.chunk_text,
                    'chunk_index': chunk.chunk_index
                })
            return result
        finally:
            db.close()
            
    async def mark_chunk_embedded(self, chunk_id: int) -> bool:
        """Mark chunk as having embeddings generated"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._mark_chunk_embedded_sync, chunk_id)
    
    def _mark_chunk_embedded_sync(self, chunk_id: int) -> bool:
        db = self.SessionLocal()
        try:
            chunk = db.query(Chunk).filter(Chunk.id == chunk_id).first()
            if chunk:
                # We don't have a specific embedded flag on chunks, but we can check if embedding exists
                # For now, we'll just return True if the chunk exists
                return True
            return False
        except Exception:
            db.rollback()
            return False
        finally:
            db.close()
    
    async def mark_embedding_generated(self, page_id: int) -> bool:
        """Mark page as having embeddings generated"""
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
    
    async def search_content(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search content using text search (fallback until vector search is implemented)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._search_content_sync, query, limit)
    
    def _search_content_sync(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        db = self.SessionLocal()
        try:
            # Simple text search for now - will be enhanced with vector search
            results = db.query(Page).filter(
                (Page.title.contains(query)) | 
                (Page.content.contains(query))
            ).limit(limit).all()
            
            # Log search
            search_log = SearchLog(query=query, results_count=len(results))
            db.add(search_log)
            db.commit()
            
            result = []
            for page in results:
                result.append({
                    'id': page.id,
                    'url': page.url,
                    'title': page.title,
                    'content': page.content[:500],  # Truncate for response
                    'hash': page.content_hash
                })
            return result
        except Exception:
            db.rollback()
            return []
        finally:
            db.close()
    
    async def get_pages(self, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Get pages with pagination"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_pages_sync, skip, limit)
    
    def _get_pages_sync(self, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        db = self.SessionLocal()
        try:
            pages = db.query(Page).offset(skip).limit(limit).all()
            
            result = []
            for page in pages:
                result.append({
                    'id': page.id,
                    'url': page.url,
                    'title': page.title,
                    'content': page.content,
                    'hash': page.content_hash,
                    'crawl_time': page.crawl_time.isoformat() if page.crawl_time else None,
                    'embedded': page.embedded
                })
            return result
        finally:
            db.close()
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
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
            
            return {
                'queued': queued,
                'processing': processing,
                'completed': completed,
                'failed': failed,
                'pages': pages,
                'chunks': chunks,
                'embeddings': embeddings,
                'total_queue': queued + processing + completed + failed
            }
        finally:
            db.close()
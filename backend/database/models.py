from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Index, ForeignKey, Float
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class Page(Base):
    __tablename__ = 'pages'
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True, nullable=False)
    domain = Column(String, index=True, nullable=True)
    title = Column(String, nullable=True)
    content = Column(Text, nullable=True)
    meta_description = Column(Text, nullable=True)
    author = Column(String, nullable=True)
    language = Column(String, default="en")
    word_count = Column(Integer, default=0)
    content_hash = Column(String, unique=True, index=True, nullable=False)
    status_code = Column(Integer, default=200)
    crawl_time = Column(DateTime, default=func.now())
    embedded = Column(Boolean, default=False)
    
    # Relationships
    chunks = relationship("Chunk", back_populates="page", cascade="all, delete-orphan", lazy="select")
    
    # Indexes for fast search and domain queries
    __table_args__ = (
        Index('idx_url', 'url'),
        Index('idx_domain', 'domain'),
        Index('idx_content_hash', 'content_hash'),
        Index('idx_embedded', 'embedded'),
        Index('idx_crawl_time', 'crawl_time'),
    )

class Chunk(Base):
    __tablename__ = 'chunks'
    
    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey('pages.id', ondelete='CASCADE'), index=True, nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    token_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    page = relationship("Page", back_populates="chunks")
    embedding = relationship("Embedding", back_populates="chunk", uselist=False, cascade="all, delete-orphan", lazy="select")
    
    # Indexes
    __table_args__ = (
        Index('idx_page_id', 'page_id'),
        Index('idx_chunk_page_index', 'page_id', 'chunk_index'),
    )

class Embedding(Base):
    __tablename__ = 'embeddings'
    
    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(Integer, ForeignKey('chunks.id', ondelete='CASCADE'), index=True, nullable=False)
    vector = Column(Text, nullable=False)  # JSON-encoded float list for portability
    model_name = Column(String, default="local-tfidf-semantic")
    dimension = Column(Integer, default=128)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    chunk = relationship("Chunk", back_populates="embedding")
    
    # Indexes
    __table_args__ = (
        Index('idx_chunk_id', 'chunk_id'),
        Index('idx_model_name', 'model_name'),
    )

class CrawlQueue(Base):
    __tablename__ = 'crawl_queue'
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True, nullable=False)
    domain = Column(String, index=True, nullable=True)
    status = Column(String, default='queued', index=True)  # queued, processing, completed, failed
    priority = Column(Integer, default=0, index=True)
    retries = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    depth = Column(Integer, default=0)
    max_depth = Column(Integer, default=2)
    parent_url = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    scheduled_at = Column(DateTime, default=func.now())
    processed_at = Column(DateTime, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_url_status', 'url', 'status'),
        Index('idx_status_priority', 'status', 'priority', 'scheduled_at'),
    )

class Domain(Base):
    __tablename__ = 'domains'
    
    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String, unique=True, index=True, nullable=False)
    pages_count = Column(Integer, default=0)
    crawl_delay = Column(Float, default=1.0)
    is_allowed = Column(Boolean, default=True)
    last_crawled = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())

class SearchLog(Base):
    __tablename__ = 'search_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, index=True, nullable=False)
    search_type = Column(String, default="hybrid")
    results_count = Column(Integer, default=0)
    execution_time_ms = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_query', 'query'),
        Index('idx_timestamp', 'timestamp'),
    )

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Index, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

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
    
    # Relationships
    chunks = relationship("Chunk", back_populates="page", cascade="all, delete-orphan")
    
    # Indexes for better search performance
    __table_args__ = (
        Index('idx_url', 'url'),
        Index('idx_content_hash', 'content_hash'),
        Index('idx_embedded', 'embedded'),
    )

class Chunk(Base):
    __tablename__ = 'chunks'
    
    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey('pages.id'), index=True, nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    
    # Relationships
    page = relationship("Page", back_populates="chunks")
    embedding = relationship("Embedding", back_populates="chunk", uselist=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_page_id', 'page_id'),
        Index('idx_chunk_text', 'chunk_text'),
    )

class Embedding(Base):
    __tablename__ = 'embeddings'
    
    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(Integer, ForeignKey('chunks.id'), index=True, nullable=False)
    vector = Column(Text)  # Storing as JSON for simplicity
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    chunk = relationship("Chunk", back_populates="embedding")
    
    # Indexes
    __table_args__ = (
        Index('idx_chunk_id', 'chunk_id'),
    )

class CrawlQueue(Base):
    __tablename__ = 'crawl_queue'
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, index=True, nullable=False)
    status = Column(String, default='queued')
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

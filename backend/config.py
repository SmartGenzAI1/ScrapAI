import os
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class CrawlerConfig:
    user_agent: str = os.getenv("CRAWLER_USER_AGENT", "Mozilla/5.0 (compatible; ScrapAI-Bot/2.0; +https://scrapai.local)")
    request_delay: float = float(os.getenv("REQUEST_DELAY", "1.0"))
    max_concurrent: int = int(os.getenv("MAX_CONCURRENT", "5"))
    respect_robots: bool = os.getenv("RESPECT_ROBOTS", "true").lower() in ("true", "1", "yes")
    timeout_seconds: int = int(os.getenv("CRAWLER_TIMEOUT", "15"))
    max_depth: int = int(os.getenv("MAX_CRAWL_DEPTH", "2"))
    max_pages_per_domain: int = int(os.getenv("MAX_PAGES_PER_DOMAIN", "50"))

@dataclass
class EmbeddingConfig:
    model: str = os.getenv("EMBEDDING_MODEL", "local-tfidf-semantic")
    batch_size: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
    dimension: int = int(os.getenv("EMBEDDING_DIMENSION", "128"))
    use_neural_if_available: bool = os.getenv("USE_NEURAL_EMBEDDINGS", "true").lower() in ("true", "1", "yes")

@dataclass
class ChunkingConfig:
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "500"))
    overlap: int = int(os.getenv("CHUNK_OVERLAP", "50"))
    batch_size: int = int(os.getenv("CHUNKING_BATCH_SIZE", "20"))
    method: str = os.getenv("CHUNKING_METHOD", "sentences")

@dataclass
class SearchConfig:
    weight_semantic: float = float(os.getenv("WEIGHT_SEMANTIC", "0.45"))
    weight_bm25: float = float(os.getenv("WEIGHT_BM25", "0.25"))
    weight_title: float = float(os.getenv("WEIGHT_TITLE", "0.15"))
    weight_domain: float = float(os.getenv("WEIGHT_DOMAIN", "0.10"))
    weight_freshness: float = float(os.getenv("WEIGHT_FRESHNESS", "0.05"))
    default_limit: int = int(os.getenv("SEARCH_DEFAULT_LIMIT", "10"))
    snippet_length: int = int(os.getenv("SNIPPET_LENGTH", "220"))

@dataclass
class DatabaseConfig:
    url: str = os.getenv("DATABASE_URL", "sqlite:///./scrapai.db")
    echo: bool = os.getenv("DB_ECHO", "false").lower() in ("true", "1", "yes")

@dataclass
class ServerConfig:
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    enable_background_workers: bool = os.getenv("ENABLE_BACKGROUND_WORKERS", "true").lower() in ("true", "1", "yes")
    worker_interval: int = int(os.getenv("WORKER_INTERVAL", "5"))

@dataclass 
class Config:
    crawler: CrawlerConfig = field(default_factory=CrawlerConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    server: ServerConfig = field(default_factory=ServerConfig)

config = Config()

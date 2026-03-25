from dataclasses import dataclass, field
from typing import Optional

@dataclass
class CrawlerConfig:
    user_agent: str = "ScrapAI-Bot/1.0"
    request_delay: int = 2

@dataclass
class EmbeddingConfig:
    model: str = "all-MiniLM-L6-v2"
    batch_size: int = 32

@dataclass
class ChunkingConfig:
    chunk_size: int = 500
    overlap: int = 50
    batch_size: int = 32

@dataclass
class DatabaseConfig:
    url: str = "sqlite:///./scrapai.db"
    echo: bool = False

@dataclass 
class Config:
    crawler: CrawlerConfig = field(default_factory=CrawlerConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)

config = Config()

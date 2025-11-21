import os
from dataclasses import dataclass
from typing import List

@dataclass
class DatabaseConfig:
    url: str = os.getenv("SUPABASE_URL", "")
    key: str = os.getenv("SUPABASE_KEY", "")
    
@dataclass
class CrawlerConfig:
    user_agent: str = "ScrapAI-Bot/1.0 (+https://github.com/yourusername/scrap-ai)"
    request_delay: int = 1
    max_concurrent: int = 10
    respect_robots: bool = True
    js_timeout: int = 30000
    
@dataclass
class EmbeddingConfig:
    model: str = "sentence-transformers/all-MiniLM-L6-v2"
    batch_size: int = 32
    device: str = "cpu"
    
@dataclass
class Config:
    database: DatabaseConfig = DatabaseConfig()
    crawler: CrawlerConfig = CrawlerConfig()
    embedding: EmbeddingConfig = EmbeddingConfig()
    
config = Config()

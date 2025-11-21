import os
from dataclasses import dataclass

@dataclass
class CrawlerConfig:
    user_agent: str = "ScrapAI-Bot/1.0 (+https://github.com/SmartGenzAI1/ScrapAI)"
    request_delay: int = 2  # Be polite
    max_concurrent: int = 5
    respect_robots: bool = True
    
@dataclass
class EmbeddingConfig:
    model: str = "all-MiniLM-L6-v2"  # Lighter model
    batch_size: int = 10
    device: str = "cpu"
    
@dataclass
class Config:
    crawler: CrawlerConfig = CrawlerConfig()
    embedding: EmbeddingConfig = EmbeddingConfig()
    
config = Config()

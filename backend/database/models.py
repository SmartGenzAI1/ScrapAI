from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class ScrapedPage(BaseModel):
    id: Optional[str] = None
    url: str
    title: Optional[str] = None
    language: Optional[str] = None
    content: Optional[str] = None
    content_hash: Optional[str] = None
    raw_html_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    crawl_time: datetime = datetime.now()

class Embedding(BaseModel):
    id: Optional[str] = None
    page_id: str
    vector: list
    metadata: Optional[Dict[str, Any]] = None
    inserted_at: datetime = datetime.now()

class CrawlQueue(BaseModel):
    id: Optional[str] = None
    url: str
    domain: str
    priority: int = 0
    status: str = "queued"
    attempts: int = 0
    scheduled_at: datetime = datetime.now()

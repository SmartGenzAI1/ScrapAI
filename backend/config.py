from dataclasses import dataclass

@dataclass
class CrawlerConfig:
    user_agent: str = "ScrapAI-Bot/1.0"
    request_delay: int = 2
    
@dataclass 
class Config:
    crawler: CrawlerConfig = CrawlerConfig()
    
config = Config()

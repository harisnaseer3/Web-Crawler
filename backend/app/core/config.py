"""Configuration settings for the web crawler search engine."""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str = "sqlite:///./crawler.db"
    database_path: str = "crawler.db"
    
    # Crawler settings
    max_threads: int = 50
    max_ips_per_run: int = 10000
    batch_size: int = 100
    request_timeout: int = 5
    politeness_delay: float = 1.0
    max_retries: int = 3
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_title: str = "Web Crawler Search Engine"
    api_version: str = "1.0.0"
    
    # CORS settings
    cors_origins: list = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "crawler.log"
    
    # Search settings
    max_search_results: int = 100
    default_search_limit: int = 10
    
    # TF-IDF settings
    max_keywords_per_page: int = 20
    min_keyword_length: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


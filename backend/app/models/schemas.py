"""Pydantic models for API request/response schemas."""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Search request model."""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    limit: int = Field(default=10, ge=1, le=100, description="Number of results to return")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")


class SearchResult(BaseModel):
    """Search result model."""
    ip_address: str
    domain: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    score: float
    response_time: Optional[float] = None
    last_crawled: Optional[datetime] = None


class SearchResponse(BaseModel):
    """Search response model."""
    results: List[SearchResult]
    total_count: int
    query: str
    execution_time: float


class CrawlStats(BaseModel):
    """Crawler statistics model."""
    active_hosts: int
    total_hosts: int
    total_keywords: int
    total_pages: int
    crawl_status: str
    total_crawled: int
    last_update: Optional[datetime] = None
    queue_size: int = 0
    positive_detections: int = 0


class CrawlRequest(BaseModel):
    """Crawl request model."""
    network: str = Field(default="0.0.0.0/0", description="Network range to crawl")
    max_ips: Optional[int] = Field(default=None, ge=1, le=100000, description="Maximum IPs to crawl")


class CrawlResponse(BaseModel):
    """Crawl response model."""
    status: str
    message: str
    network: str
    max_ips: Optional[int] = None


class HostInfo(BaseModel):
    """Host information model."""
    ip_address: str
    domain: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    server_info: Optional[str] = None
    content_type: Optional[str] = None
    is_active: bool
    last_crawled: Optional[datetime] = None


class KeywordInfo(BaseModel):
    """Keyword information model."""
    keyword: str
    frequency: int
    tf_score: float
    idf_score: float
    tf_idf_score: float


class PageInfo(BaseModel):
    """Page information model."""
    url: str
    title: Optional[str] = None
    meta_description: Optional[str] = None
    http_status: Optional[int] = None
    load_time: Optional[float] = None
    content_size: int
    last_crawled: datetime
    keywords: List[KeywordInfo] = []


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    status_code: int


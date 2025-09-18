"""Search API endpoints."""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from ..models.schemas import SearchRequest, SearchResponse, SearchResult
from ..services.search_service import search_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["search"])


@router.post("/", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Search the crawled content using TF-IDF scoring."""
    try:
        result = search_service.search(
            query=request.query,
            limit=request.limit,
            offset=request.offset
        )
        
        # Convert results to SearchResult objects
        search_results = []
        for item in result['results']:
            search_results.append(SearchResult(
                ip_address=item['ip_address'],
                domain=item.get('domain'),
                title=item.get('title'),
                description=item.get('description'),
                score=item['score'],
                response_time=item.get('response_time'),
                last_crawled=item.get('last_crawled')
            ))
        
        return SearchResponse(
            results=search_results,
            total_count=result['total_count'],
            query=result['query'],
            execution_time=result['execution_time']
        )
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/domain/{domain}", response_model=SearchResponse)
async def search_by_domain(
    domain: str,
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """Search for hosts by domain name."""
    try:
        result = search_service.search_by_domain(
            domain=domain,
            limit=limit,
            offset=offset
        )
        
        # Convert results to SearchResult objects
        search_results = []
        for item in result['results']:
            search_results.append(SearchResult(
                ip_address=item['ip_address'],
                domain=item.get('domain'),
                title=item.get('title'),
                description=item.get('description'),
                score=item['score'],
                response_time=item.get('response_time'),
                last_crawled=item.get('last_crawled')
            ))
        
        return SearchResponse(
            results=search_results,
            total_count=result['total_count'],
            query=result['query'],
            execution_time=result['execution_time']
        )
        
    except Exception as e:
        logger.error(f"Domain search error: {e}")
        raise HTTPException(status_code=500, detail=f"Domain search failed: {str(e)}")


@router.get("/keywords/popular")
async def get_popular_keywords(limit: int = Query(default=20, ge=1, le=100)):
    """Get most popular keywords."""
    try:
        keywords = search_service.get_popular_keywords(limit=limit)
        return {"keywords": keywords}
    except Exception as e:
        logger.error(f"Error getting popular keywords: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get keywords: {str(e)}")


@router.get("/host/{ip_address}")
async def get_host_details(ip_address: str):
    """Get detailed information about a specific host."""
    try:
        host_info = search_service.get_host_details(ip_address)
        if not host_info:
            raise HTTPException(status_code=404, detail="Host not found")
        return host_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting host details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get host details: {str(e)}")


@router.get("/analytics")
async def get_search_analytics(limit: int = Query(default=50, ge=1, le=200)):
    """Get search analytics and statistics."""
    try:
        analytics = search_service.get_search_analytics(limit=limit)
        return analytics
    except Exception as e:
        logger.error(f"Error getting search analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

"""Crawler management API endpoints."""

import logging
import threading
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional

from ..models.schemas import CrawlRequest, CrawlResponse, CrawlStats
from ..services.crawler_service import crawler_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/crawl", tags=["crawler"])


@router.post("/start", response_model=CrawlResponse)
async def start_crawl(request: CrawlRequest, background_tasks: BackgroundTasks):
    """Start the crawler with specified parameters."""
    try:
        if crawler_service.active:
            return CrawlResponse(
                status="already_running",
                message="Crawler is already running",
                network=request.network,
                max_ips=request.max_ips
            )
        
        # Start crawler in background
        def run_crawler():
            crawler_service.start_crawling(
                network=request.network,
                max_ips=request.max_ips
            )
        
        background_tasks.add_task(run_crawler)
        
        return CrawlResponse(
            status="started",
            message=f"Crawler started for network {request.network}",
            network=request.network,
            max_ips=request.max_ips
        )
        
    except Exception as e:
        logger.error(f"Error starting crawler: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start crawler: {str(e)}")


@router.post("/stop", response_model=CrawlResponse)
async def stop_crawl():
    """Stop the crawler."""
    try:
        if not crawler_service.active:
            return CrawlResponse(
                status="not_running",
                message="Crawler is not currently running",
                network="",
                max_ips=None
            )
        
        success = crawler_service.stop_crawling()
        
        if success:
            return CrawlResponse(
                status="stopped",
                message="Crawler stopped successfully",
                network="",
                max_ips=None
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to stop crawler")
            
    except Exception as e:
        logger.error(f"Error stopping crawler: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop crawler: {str(e)}")


@router.get("/status")
async def get_crawl_status():
    """Get current crawler status."""
    try:
        return {
            "active": crawler_service.active,
            "thread_count": len(crawler_service.threads),
            "queue_size": crawler_service.task_queue.qsize()
        }
    except Exception as e:
        logger.error(f"Error getting crawl status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.get("/stats", response_model=CrawlStats)
async def get_crawl_stats():
    """Get crawler statistics."""
    try:
        stats = crawler_service.get_stats()
        return CrawlStats(**stats)
    except Exception as e:
        logger.error(f"Error getting crawl stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/live/currently-scanning")
async def get_currently_scanning(limit: int = 50):
    """Get a snapshot list of IPs currently being scanned."""
    try:
        return {
            "ips": crawler_service.get_currently_scanning(limit=limit),
            "count": crawler_service.get_currently_scanning_count()
        }
    except Exception as e:
        logger.error(f"Error getting currently scanning: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get currently scanning: {str(e)}")


@router.get("/live/events")
async def get_recent_events(limit: int = 100):
    """Get recent scan events (scan_start, detected, failed, stored)."""
    try:
        return {"events": crawler_service.get_recent_events(limit=limit)}
    except Exception as e:
        logger.error(f"Error getting recent events: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get events: {str(e)}")


@router.post("/pause")
async def pause_crawl():
    """Pause the crawler (temporarily stop processing new IPs)."""
    try:
        if not crawler_service.active:
            raise HTTPException(status_code=400, detail="Crawler is not running")
        
        crawler_service.stop_event.set()
        crawler_service.update_crawl_state('paused')
        
        return {"status": "paused", "message": "Crawler paused successfully"}
        
    except Exception as e:
        logger.error(f"Error pausing crawler: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to pause crawler: {str(e)}")


@router.post("/resume")
async def resume_crawl():
    """Resume the crawler after being paused."""
    try:
        if not crawler_service.active:
            raise HTTPException(status_code=400, detail="Crawler is not running")
        
        crawler_service.stop_event.clear()
        crawler_service.update_crawl_state('running')
        
        return {"status": "resumed", "message": "Crawler resumed successfully"}
        
    except Exception as e:
        logger.error(f"Error resuming crawler: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to resume crawler: {str(e)}")


@router.post("/queue/populate")
async def populate_queue(
    network: str = "0.0.0.0/0",
    count: int = 1000
):
    """Manually populate the crawl queue with IPs."""
    try:
        if count > 100000:
            raise HTTPException(status_code=400, detail="Count too large, maximum 100000")
        
        added_count = crawler_service.populate_queue(network, count)
        
        return {
            "status": "success",
            "message": f"Added {added_count} IPs to crawl queue",
            "network": network,
            "count": added_count
        }
        
    except Exception as e:
        logger.error(f"Error populating queue: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to populate queue: {str(e)}")


@router.get("/queue/stats")
async def get_queue_stats():
    """Get crawl queue statistics."""
    try:
        from ..core.database import db_manager
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get queue statistics by status
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM crawl_queue
                GROUP BY status
            """)
            
            status_counts = {}
            for row in cursor.fetchall():
                status_counts[row[0]] = row[1]
            
            # Get total queue size
            cursor.execute("SELECT COUNT(*) FROM crawl_queue")
            total_size = cursor.fetchone()[0]
            
            return {
                "total_size": total_size,
                "status_breakdown": status_counts,
                "current_queue_size": crawler_service.task_queue.qsize()
            }
            
    except Exception as e:
        logger.error(f"Error getting queue stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get queue stats: {str(e)}")

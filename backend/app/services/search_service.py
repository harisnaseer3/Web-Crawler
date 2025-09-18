"""Search service for querying crawled content."""

import sqlite3
import time
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from ..core.database import db_manager
from ..core.config import settings

logger = logging.getLogger(__name__)


class SearchService:
    """Service for searching crawled content using TF-IDF scoring."""
    
    def __init__(self):
        self.cache = {}  # Simple in-memory cache for frequent queries
    
    def search(self, query: str, limit: int = 10, offset: int = 0) -> Dict:
        """Search the crawled content using TF-IDF scoring."""
        start_time = time.time()
        
        try:
            # Parse query terms
            query_terms = [term.lower().strip() for term in query.split() 
                          if len(term.strip()) >= settings.min_keyword_length]
            
            if not query_terms:
                return {
                    'results': [],
                    'total_count': 0,
                    'query': query,
                    'execution_time': time.time() - start_time
                }
            
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build search query with TF-IDF scoring
                placeholders = ','.join('?' * len(query_terms))
                
                # Main search query with TF-IDF scoring
                search_query = f"""
                    SELECT 
                        h.ip_address,
                        h.domain,
                        h.title,
                        h.description,
                        h.response_time,
                        h.last_crawled,
                        SUM(pk.frequency * k.total_occurrences) as score,
                        COUNT(DISTINCT p.id) as page_count
                    FROM hosts h
                    JOIN pages p ON h.id = p.host_id
                    JOIN page_keywords pk ON p.id = pk.page_id
                    JOIN keywords k ON pk.keyword_id = k.id
                    WHERE k.keyword IN ({placeholders}) 
                        AND h.is_active = 1
                    GROUP BY h.id
                    ORDER BY score DESC, page_count DESC
                    LIMIT ? OFFSET ?
                """
                
                cursor.execute(search_query, query_terms + [limit, offset])
                results = []
                
                for row in cursor.fetchall():
                    results.append({
                        'ip_address': row[0],
                        'domain': row[1],
                        'title': row[2],
                        'description': row[3],
                        'score': float(row[6]) if row[6] else 0.0,
                        'response_time': row[4],
                        'last_crawled': row[5],
                        'page_count': row[7]
                    })
                
                # Get total count for pagination
                count_query = f"""
                    SELECT COUNT(DISTINCT h.id)
                    FROM hosts h
                    JOIN pages p ON h.id = p.host_id
                    JOIN page_keywords pk ON p.id = pk.page_id
                    JOIN keywords k ON pk.keyword_id = k.id
                    WHERE k.keyword IN ({placeholders}) 
                        AND h.is_active = 1
                """
                
                cursor.execute(count_query, query_terms)
                total_count = cursor.fetchone()[0]
                
                # Log search for analytics
                self._log_search(query, total_count)
                
                execution_time = time.time() - start_time
                
                return {
                    'results': results,
                    'total_count': total_count,
                    'query': query,
                    'execution_time': execution_time
                }
                
        except Exception as e:
            logger.error(f"Search error: {e}")
            return {
                'results': [],
                'total_count': 0,
                'query': query,
                'execution_time': time.time() - start_time,
                'error': str(e)
            }
    
    def search_by_domain(self, domain: str, limit: int = 10, offset: int = 0) -> Dict:
        """Search for hosts by domain name."""
        start_time = time.time()
        
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT ip_address, domain, title, description, response_time, last_crawled
                    FROM hosts
                    WHERE domain LIKE ? AND is_active = 1
                    ORDER BY last_crawled DESC
                    LIMIT ? OFFSET ?
                """, (f"%{domain}%", limit, offset))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'ip_address': row[0],
                        'domain': row[1],
                        'title': row[2],
                        'description': row[3],
                        'score': 1.0,  # Domain matches get equal score
                        'response_time': row[4],
                        'last_crawled': row[5]
                    })
                
                # Get total count
                cursor.execute("""
                    SELECT COUNT(*) FROM hosts
                    WHERE domain LIKE ? AND is_active = 1
                """, (f"%{domain}%",))
                
                total_count = cursor.fetchone()[0]
                
                return {
                    'results': results,
                    'total_count': total_count,
                    'query': f"domain:{domain}",
                    'execution_time': time.time() - start_time
                }
                
        except Exception as e:
            logger.error(f"Domain search error: {e}")
            return {
                'results': [],
                'total_count': 0,
                'query': f"domain:{domain}",
                'execution_time': time.time() - start_time,
                'error': str(e)
            }
    
    def get_popular_keywords(self, limit: int = 20) -> List[Dict]:
        """Get most popular keywords."""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT keyword, total_occurrences, COUNT(DISTINCT page_id) as page_count
                    FROM keywords k
                    JOIN page_keywords pk ON k.id = pk.keyword_id
                    GROUP BY k.id
                    ORDER BY total_occurrences DESC, page_count DESC
                    LIMIT ?
                """, (limit,))
                
                keywords = []
                for row in cursor.fetchall():
                    keywords.append({
                        'keyword': row[0],
                        'total_occurrences': row[1],
                        'page_count': row[2]
                    })
                
                return keywords
                
        except Exception as e:
            logger.error(f"Error getting popular keywords: {e}")
            return []
    
    def get_host_details(self, ip_address: str) -> Optional[Dict]:
        """Get detailed information about a specific host."""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get host information
                cursor.execute("""
                    SELECT ip_address, domain, title, description, status_code,
                           response_time, server_info, content_type, is_active, last_crawled
                    FROM hosts
                    WHERE ip_address = ?
                """, (ip_address,))
                
                host_row = cursor.fetchone()
                if not host_row:
                    return None
                
                host_info = {
                    'ip_address': host_row[0],
                    'domain': host_row[1],
                    'title': host_row[2],
                    'description': host_row[3],
                    'status_code': host_row[4],
                    'response_time': host_row[5],
                    'server_info': host_row[6],
                    'content_type': host_row[7],
                    'is_active': bool(host_row[8]),
                    'last_crawled': host_row[9]
                }
                
                # Get pages for this host
                cursor.execute("""
                    SELECT url, title, meta_description, http_status, load_time, 
                           content_size, last_crawled
                    FROM pages
                    WHERE host_id = (SELECT id FROM hosts WHERE ip_address = ?)
                    ORDER BY last_crawled DESC
                """, (ip_address,))
                
                pages = []
                for row in cursor.fetchall():
                    pages.append({
                        'url': row[0],
                        'title': row[1],
                        'meta_description': row[2],
                        'http_status': row[3],
                        'load_time': row[4],
                        'content_size': row[5],
                        'last_crawled': row[6]
                    })
                
                host_info['pages'] = pages
                
                # Get top keywords for this host
                cursor.execute("""
                    SELECT k.keyword, SUM(pk.frequency) as total_frequency
                    FROM keywords k
                    JOIN page_keywords pk ON k.id = pk.keyword_id
                    JOIN pages p ON pk.page_id = p.id
                    JOIN hosts h ON p.host_id = h.id
                    WHERE h.ip_address = ?
                    GROUP BY k.id
                    ORDER BY total_frequency DESC
                    LIMIT 10
                """, (ip_address,))
                
                keywords = []
                for row in cursor.fetchall():
                    keywords.append({
                        'keyword': row[0],
                        'frequency': row[1]
                    })
                
                host_info['top_keywords'] = keywords
                
                return host_info
                
        except Exception as e:
            logger.error(f"Error getting host details: {e}")
            return None
    
    def _log_search(self, query: str, result_count: int):
        """Log search query for analytics."""
        try:
            with db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT INTO search_history (query, result_count, search_time)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (query, result_count))
                conn.commit()
        except Exception as e:
            logger.error(f"Error logging search: {e}")
    
    def get_search_analytics(self, limit: int = 50) -> Dict:
        """Get search analytics and statistics."""
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get recent searches
                cursor.execute("""
                    SELECT query, result_count, search_time
                    FROM search_history
                    ORDER BY search_time DESC
                    LIMIT ?
                """, (limit,))
                
                recent_searches = []
                for row in cursor.fetchall():
                    recent_searches.append({
                        'query': row[0],
                        'result_count': row[1],
                        'search_time': row[2]
                    })
                
                # Get search statistics
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_searches,
                        AVG(result_count) as avg_results,
                        COUNT(DISTINCT query) as unique_queries
                    FROM search_history
                    WHERE search_time >= datetime('now', '-24 hours')
                """)
                
                stats_row = cursor.fetchone()
                stats = {
                    'total_searches_24h': stats_row[0] if stats_row[0] else 0,
                    'avg_results_24h': float(stats_row[1]) if stats_row[1] else 0.0,
                    'unique_queries_24h': stats_row[2] if stats_row[2] else 0
                }
                
                return {
                    'recent_searches': recent_searches,
                    'statistics': stats
                }
                
        except Exception as e:
            logger.error(f"Error getting search analytics: {e}")
            return {'recent_searches': [], 'statistics': {}}


# Global search service instance
search_service = SearchService()

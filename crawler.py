"""
Legacy Web Crawler - This file is kept for backward compatibility.
For the new structured application, use the backend/app/ directory.

To run the new application:
1. Backend: python start_backend.py
2. Frontend: npm start (in frontend directory)

This legacy file will be deprecated in future versions.
"""

import sqlite3
import threading
import random
import requests
import ipaddress
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime
import logging
from queue import Queue
import re
from collections import Counter
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('WebCrawler')

# Print deprecation warning
logger.warning("This legacy crawler.py is deprecated. Please use the new structured application in backend/app/")

class WebCrawler:
    def __init__(self, db_path='crawler.db', max_threads=50, max_ips_per_run=10000):
        self.db_path = db_path
        self.max_threads = max_threads
        self.max_ips_per_run = max_ips_per_run
        self.active = False
        self.threads = []
        self.task_queue = Queue()
        self.lock = threading.Lock()
        self.init_database()
        
    def init_database(self):
        """Initialize database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            with open('schema.sql', 'r') as f:
                conn.executescript(f.read())
            conn.commit()
    
    def generate_random_ips(self, network="0.0.0.0/0", count=1000):
        """Generate random IP addresses within a network range"""
        try:
            net = ipaddress.ip_network(network)
            ips = []
            for _ in range(count):
                # Generate random IP within the network
                random_ip = ipaddress.IPv4Address(
                    random.randint(int(net.network_address), int(net.broadcast_address))
                )
                ips.append(str(random_ip))
            return ips
        except Exception as e:
            logger.error(f"Error generating IPs: {e}")
            return []
    
    def populate_queue(self, network="0.0.0.0/0", count=10000):
        """Populate the crawl queue with random IPs"""
        try:
            ips = self.generate_random_ips(network, count)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("BEGIN TRANSACTION")
                for ip in ips:
                    try:
                        conn.execute(
                            "INSERT OR IGNORE INTO crawl_queue (ip_address) VALUES (?)",
                            (ip,)
                        )
                    except sqlite3.IntegrityError:
                        pass  # IP already exists in queue
                conn.commit()
            logger.info(f"Added {len(ips)} IPs to crawl queue")
        except Exception as e:
            logger.error(f"Error populating queue: {e}")
    
    def get_next_ip_batch(self, batch_size=100):
        """Get a batch of IPs to process from the queue"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE crawl_queue SET status = 'in-progress' WHERE id IN ("
                    "SELECT id FROM crawl_queue WHERE status = 'pending' LIMIT ?"
                    ") RETURNING ip_address",
                    (batch_size,)
                )
                ips = [row[0] for row in cursor.fetchall()]
                conn.commit()
                return ips
        except Exception as e:
            logger.error(f"Error getting next IP batch: {e}")
            return []
    
    def extract_keywords(self, text, max_keywords=20):
        """Extract keywords from text using TF-IDF approach"""
        # Simple implementation - in production, use NLTK or spaCy
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        word_freq = Counter(words)
        
        # Remove common stop words
        stop_words = set(['the', 'and', 'for', 'with', 'this', 'that', 'are', 'from', 'was', 'were', 'you', 'your', 'has', 'have'])
        filtered_freq = {word: count for word, count in word_freq.items() if word not in stop_words}
        
        # Get top keywords
        keywords = sorted(filtered_freq.items(), key=lambda x: x[1], reverse=True)[:max_keywords]
        return keywords
    
    def crawl_ip(self, ip):
        """Crawl a single IP address on port 80"""
        url = f"http://{ip}"
        try:
            start_time = time.time()
            response = requests.get(
                url, 
                timeout=5,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; WebCrawler/1.0)'}
            )
            response_time = time.time() - start_time
            
            # Parse HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string if soup.title else None
            
            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc['content'] if meta_desc else None
            
            # Extract server information
            server_info = response.headers.get('Server', '')
            
            # Extract keywords from page content
            text_content = soup.get_text()
            keywords = self.extract_keywords(text_content)
            
            return {
                'status_code': response.status_code,
                'title': title,
                'description': description,
                'response_time': response_time,
                'server_info': server_info,
                'content_type': response.headers.get('Content-Type', ''),
                'content': response.text,
                'keywords': keywords
            }
        except requests.RequestException as e:
            logger.debug(f"Failed to crawl {ip}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error crawling {ip}: {e}")
            return None
    
    def process_ip(self, ip):
        """Process a single IP address and store results in database"""
        result = self.crawl_ip(ip)
        
        with sqlite3.connect(self.db_path) as conn:
            if result:
                # Insert or update host information
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT OR REPLACE INTO hosts 
                    (ip_address, last_crawled, status_code, title, description, 
                     response_time, server_info, content_type, is_active)
                    VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, 1)""",
                    (ip, result['status_code'], result['title'], result['description'],
                     result['response_time'], result['server_info'], result['content_type'])
                )
                host_id = cursor.lastrowid
                
                # Insert page content
                content_hash = hash(result['content'])
                cursor.execute(
                    """INSERT INTO pages 
                    (host_id, url, content_hash, title, meta_description, 
                     http_status, load_time, content_size, last_crawled)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                    (host_id, f"http://{ip}", content_hash, result['title'], 
                     result['description'], result['status_code'], 
                     result['response_time'], len(result['content']))
                )
                page_id = cursor.lastrowid
                
                # Process keywords
                for keyword, frequency in result['keywords']:
                    # Insert or get keyword ID
                    cursor.execute(
                        "INSERT OR IGNORE INTO keywords (keyword) VALUES (?)",
                        (keyword,)
                    )
                    cursor.execute(
                        "SELECT id FROM keywords WHERE keyword = ?",
                        (keyword,)
                    )
                    keyword_id = cursor.fetchone()[0]
                    
                    # Update keyword occurrence count
                    cursor.execute(
                        "UPDATE keywords SET total_occurrences = total_occurrences + 1 WHERE id = ?",
                        (keyword_id,)
                    )
                    
                    # Insert page-keyword relationship
                    cursor.execute(
                        """INSERT INTO page_keywords 
                        (page_id, keyword_id, frequency)
                        VALUES (?, ?, ?)""",
                        (page_id, keyword_id, frequency)
                    )
                
                # Update crawl queue status
                cursor.execute(
                    "UPDATE crawl_queue SET status = 'completed' WHERE ip_address = ?",
                    (ip,)
                )
                
                logger.info(f"Successfully crawled {ip}: {result['status_code']}")
            else:
                # Mark as failed in hosts table
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT OR REPLACE INTO hosts 
                    (ip_address, last_crawled, is_active)
                    VALUES (?, CURRENT_TIMESTAMP, 0)""",
                    (ip,)
                )
                
                # Update crawl queue status
                cursor.execute(
                    "UPDATE crawl_queue SET status = 'failed' WHERE ip_address = ?",
                    (ip,)
                )
                
                logger.debug(f"Failed to crawl {ip}")
            
            conn.commit()
    
    def worker(self):
        """Worker thread function to process IPs from the queue"""
        while self.active:
            try:
                ip = self.task_queue.get(timeout=5)
                if ip is None:  # Sentinel value to stop
                    break
                
                self.process_ip(ip)
                self.task_queue.task_done()
                
            except Queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Worker error: {e}")
    
    def update_crawl_state(self, status, total_crawled=None):
        """Update the crawl state in the database"""
        with sqlite3.connect(self.db_path) as conn:
            if total_crawled is not None:
                conn.execute(
                    "UPDATE crawl_state SET status = ?, total_crawled = ?, last_update = CURRENT_TIMESTAMP",
                    (status, total_crawled)
                )
            else:
                conn.execute(
                    "UPDATE crawl_state SET status = ?, last_update = CURRENT_TIMESTAMP",
                    (status,)
                )
            conn.commit()
    
    def start_crawling(self, network="0.0.0.0/0"):
        """Start the crawling process"""
        if self.active:
            logger.warning("Crawler is already running")
            return
        
        self.active = True
        
        # Initialize crawl state
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO crawl_state (id, current_network, status, start_time) VALUES (1, ?, 'running', CURRENT_TIMESTAMP)",
                (network,)
            )
            conn.commit()
        
        # Populate queue with random IPs
        self.populate_queue(network, self.max_ips_per_run)
        
        # Start worker threads
        for i in range(self.max_threads):
            thread = threading.Thread(target=self.worker, name=f"Worker-{i+1}")
            thread.daemon = True
            thread.start()
            self.threads.append(thread)
        
        logger.info(f"Started {self.max_threads} worker threads")
        
        # Main processing loop
        try:
            while self.active:
                # Get next batch of IPs
                ip_batch = self.get_next_ip_batch(100)
                if not ip_batch:
                    logger.info("No more IPs to process. Waiting...")
                    time.sleep(10)
                    # Repopulate queue if empty
                    self.populate_queue(network, self.max_ips_per_run // 10)
                    continue
                
                # Add IPs to task queue
                for ip in ip_batch:
                    self.task_queue.put(ip)
                
                # Update crawl state
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM crawl_queue WHERE status = 'completed'")
                    total_crawled = cursor.fetchone()[0]
                
                self.update_crawl_state('running', total_crawled)
                logger.info(f"Added {len(ip_batch)} IPs to task queue. Total crawled: {total_crawled}")
                
                # Wait for queue to process
                self.task_queue.join()
                
        except KeyboardInterrupt:
            logger.info("Crawler interrupted by user")
        except Exception as e:
            logger.error(f"Crawler error: {e}")
        finally:
            self.stop_crawling()
    
    def stop_crawling(self):
        """Stop the crawling process"""
        logger.info("Stopping crawler...")
        self.active = False
        
        # Wait for threads to finish
        for _ in range(self.max_threads):
            self.task_queue.put(None)  # Sentinel values to stop workers
        
        for thread in self.threads:
            thread.join(timeout=5)
        
        self.threads.clear()
        
        # Update crawl state
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM crawl_queue WHERE status = 'completed'")
            total_crawled = cursor.fetchone()[0]
        
        self.update_crawl_state('stopped', total_crawled)
        logger.info("Crawler stopped successfully")
    
    def get_stats(self):
        """Get crawling statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get total crawled count
            cursor.execute("SELECT COUNT(*) FROM hosts WHERE is_active = 1")
            active_hosts = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM hosts")
            total_hosts = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM keywords")
            total_keywords = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM pages")
            total_pages = cursor.fetchone()[0]
            
            cursor.execute("SELECT status, total_crawled, last_update FROM crawl_state WHERE id = 1")
            crawl_state = cursor.fetchone()
            
            return {
                'active_hosts': active_hosts,
                'total_hosts': total_hosts,
                'total_keywords': total_keywords,
                'total_pages': total_pages,
                'crawl_status': crawl_state[0] if crawl_state else 'unknown',
                'total_crawled': crawl_state[1] if crawl_state else 0,
                'last_update': crawl_state[2] if crawl_state else None
            }

# FastAPI implementation for the web service
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from typing import List, Optional

app = FastAPI(title="Web Crawler Search Engine")
crawler = WebCrawler()

class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    offset: int = 0

class SearchResult(BaseModel):
    ip_address: str
    domain: Optional[str]
    title: Optional[str]
    description: Optional[str]
    score: float

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total_count: int
    query: str

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Search the crawled content"""
    try:
        with sqlite3.connect(crawler.db_path) as conn:
            # Simple search implementation - in production, use full-text search
            query_terms = request.query.lower().split()
            placeholders = ','.join('?' * len(query_terms))
            
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT h.ip_address, h.domain, h.title, h.description,
                       SUM(pk.frequency * k.total_occurrences) as score
                FROM hosts h
                JOIN pages p ON h.id = p.host_id
                JOIN page_keywords pk ON p.id = pk.page_id
                JOIN keywords k ON pk.keyword_id = k.id
                WHERE k.keyword IN ({placeholders}) AND h.is_active = 1
                GROUP BY h.id
                ORDER BY score DESC
                LIMIT ? OFFSET ?
            """, query_terms + [request.limit, request.offset])
            
            results = []
            for row in cursor.fetchall():
                results.append(SearchResult(
                    ip_address=row[0],
                    domain=row[1],
                    title=row[2],
                    description=row[3],
                    score=row[4]
                ))
            
            # Get total count
            cursor.execute(f"""
                SELECT COUNT(DISTINCT h.id)
                FROM hosts h
                JOIN pages p ON h.id = p.host_id
                JOIN page_keywords pk ON p.id = pk.page_id
                JOIN keywords k ON pk.keyword_id = k.id
                WHERE k.keyword IN ({placeholders}) AND h.is_active = 1
            """, query_terms)
            
            total_count = cursor.fetchone()[0]
            
            return SearchResponse(
                results=results,
                total_count=total_count,
                query=request.query
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/crawl/start")
async def start_crawl(network: str = "0.0.0.0/0"):
    """Start the crawler"""
    if crawler.active:
        return {"status": "already_running"}
    
    # Run crawler in a separate thread
    import threading
    crawl_thread = threading.Thread(
        target=crawler.start_crawling,
        kwargs={'network': network},
        daemon=True
    )
    crawl_thread.start()
    
    return {"status": "started"}

@app.post("/crawl/stop")
async def stop_crawl():
    """Stop the crawler"""
    crawler.stop_crawling()
    return {"status": "stopped"}

@app.get("/crawl/stats")
async def get_crawl_stats():
    """Get crawler statistics"""
    return crawler.get_stats()

if __name__ == "__main__":
    # Run the FastAPI application
    uvicorn.run(app, host="0.0.0.0", port=8000)
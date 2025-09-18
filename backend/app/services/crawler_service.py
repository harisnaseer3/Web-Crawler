"""Web crawler service with multithreading and resumable operations."""

import sqlite3
import threading
import random
import requests
import ipaddress
import time
import logging
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from collections import Counter
from queue import Queue, Empty
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from ..core.config import settings
from ..core.database import db_manager

logger = logging.getLogger(__name__)


class WebCrawlerService:
    """Main web crawler service with multithreading support."""
    
    def __init__(self):
        self.active = False
        self.threads: List[threading.Thread] = []
        self.task_queue = Queue()
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        
    def generate_random_ips(self, network: str = "0.0.0.0/0", count: int = 1000) -> List[str]:
        """Generate random IP addresses within a network range."""
        try:
            net = ipaddress.ip_network(network)
            ips = []
            for _ in range(count):
                random_ip = ipaddress.IPv4Address(
                    random.randint(int(net.network_address), int(net.broadcast_address))
                )
                ips.append(str(random_ip))
            return ips
        except Exception as e:
            logger.error(f"Error generating IPs: {e}")
            return []
    
    def populate_queue(self, network: str = "0.0.0.0/0", count: int = 10000) -> int:
        """Populate the crawl queue with random IPs."""
        try:
            ips = self.generate_random_ips(network, count)
            with db_manager.get_connection() as conn:
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
            return len(ips)
        except Exception as e:
            logger.error(f"Error populating queue: {e}")
            return 0
    
    def get_next_ip_batch(self, batch_size: int = 100) -> List[str]:
        """Get a batch of IPs to process from the queue."""
        try:
            with db_manager.get_connection() as conn:
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
    
    def extract_keywords(self, text: str, max_keywords: int = 20) -> List[Tuple[str, int]]:
        """Extract keywords from text using TF-IDF approach."""
        # Simple implementation - in production, use NLTK or spaCy
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        word_freq = Counter(words)
        
        # Remove common stop words
        stop_words = set([
            'the', 'and', 'for', 'with', 'this', 'that', 'are', 'from', 'was', 'were',
            'you', 'your', 'has', 'have', 'had', 'will', 'can', 'could', 'would',
            'should', 'may', 'might', 'must', 'shall', 'do', 'does', 'did', 'done',
            'is', 'am', 'be', 'been', 'being', 'get', 'got', 'gotten', 'go', 'went',
            'gone', 'come', 'came', 'see', 'saw', 'seen', 'know', 'knew', 'known',
            'think', 'thought', 'take', 'took', 'taken', 'make', 'made', 'give',
            'gave', 'given', 'find', 'found', 'look', 'looked', 'use', 'used',
            'work', 'worked', 'call', 'called', 'try', 'tried', 'ask', 'asked',
            'need', 'needed', 'feel', 'felt', 'become', 'became', 'leave', 'left',
            'put', 'keep', 'kept', 'let', 'begin', 'began', 'begun', 'seem',
            'seemed', 'help', 'helped', 'show', 'showed', 'shown', 'hear', 'heard',
            'play', 'played', 'run', 'ran', 'move', 'moved', 'live', 'lived',
            'believe', 'believed', 'bring', 'brought', 'happen', 'happened',
            'write', 'wrote', 'written', 'sit', 'sat', 'stand', 'stood', 'lose',
            'lost', 'pay', 'paid', 'meet', 'met', 'include', 'included', 'continue',
            'continued', 'set', 'follow', 'followed', 'stop', 'stopped', 'create',
            'created', 'speak', 'spoke', 'spoken', 'read', 'allow', 'allowed',
            'add', 'added', 'spend', 'spent', 'grow', 'grew', 'grown', 'open',
            'opened', 'walk', 'walked', 'win', 'won', 'offer', 'offered', 'remember',
            'remembered', 'love', 'loved', 'consider', 'considered', 'appear',
            'appeared', 'buy', 'bought', 'wait', 'waited', 'serve', 'served',
            'die', 'died', 'send', 'sent', 'expect', 'expected', 'build', 'built',
            'stay', 'stayed', 'fall', 'fell', 'fallen', 'cut', 'reach', 'reached',
            'kill', 'killed', 'remain', 'remained', 'suggest', 'suggested', 'raise',
            'raised', 'pass', 'passed', 'sell', 'sold', 'require', 'required',
            'report', 'reported', 'decide', 'decided', 'pull', 'pulled'
        ])
        
        filtered_freq = {word: count for word, count in word_freq.items() 
                        if word not in stop_words and len(word) >= settings.min_keyword_length}
        
        # Get top keywords
        keywords = sorted(filtered_freq.items(), key=lambda x: x[1], reverse=True)[:max_keywords]
        return keywords
    
    def crawl_ip(self, ip: str) -> Optional[Dict]:
        """Crawl a single IP address on port 80."""
        url = f"http://{ip}"
        try:
            start_time = time.time()
            response = requests.get(
                url, 
                timeout=settings.request_timeout,
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
            keywords = self.extract_keywords(text_content, settings.max_keywords_per_page)
            
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
    
    def process_ip(self, ip: str) -> bool:
        """Process a single IP address and store results in database."""
        result = self.crawl_ip(ip)
        
        try:
            with db_manager.get_connection() as conn:
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
                    return True
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
                    return False
                
                conn.commit()
        except Exception as e:
            logger.error(f"Error processing IP {ip}: {e}")
            return False
    
    def worker(self):
        """Worker thread function to process IPs from the queue."""
        while not self.stop_event.is_set():
            try:
                ip = self.task_queue.get(timeout=5)
                if ip is None:  # Sentinel value to stop
                    break
                
                self.process_ip(ip)
                self.task_queue.task_done()
                
                # Politeness delay
                time.sleep(settings.politeness_delay)
                
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Worker error: {e}")
    
    def update_crawl_state(self, status: str, total_crawled: Optional[int] = None):
        """Update the crawl state in the database."""
        try:
            with db_manager.get_connection() as conn:
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
        except Exception as e:
            logger.error(f"Error updating crawl state: {e}")
    
    def start_crawling(self, network: str = "0.0.0.0/0", max_ips: Optional[int] = None) -> bool:
        """Start the crawling process."""
        if self.active:
            logger.warning("Crawler is already running")
            return False
        
        try:
            self.active = True
            self.stop_event.clear()
            
            # Initialize crawl state
            with db_manager.get_connection() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO crawl_state (id, current_network, status, start_time) VALUES (1, ?, 'running', CURRENT_TIMESTAMP)",
                    (network,)
                )
                conn.commit()
            
            # Populate queue with random IPs
            ip_count = max_ips or settings.max_ips_per_run
            self.populate_queue(network, ip_count)
            
            # Start worker threads
            for i in range(settings.max_threads):
                thread = threading.Thread(target=self.worker, name=f"Worker-{i+1}")
                thread.daemon = True
                thread.start()
                self.threads.append(thread)
            
            logger.info(f"Started {settings.max_threads} worker threads")
            
            # Main processing loop
            while self.active and not self.stop_event.is_set():
                # Get next batch of IPs
                ip_batch = self.get_next_ip_batch(settings.batch_size)
                if not ip_batch:
                    logger.info("No more IPs to process. Waiting...")
                    time.sleep(10)
                    # Repopulate queue if empty
                    self.populate_queue(network, settings.max_ips_per_run // 10)
                    continue
                
                # Add IPs to task queue
                for ip in ip_batch:
                    self.task_queue.put(ip)
                
                # Update crawl state
                with db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM crawl_queue WHERE status = 'completed'")
                    total_crawled = cursor.fetchone()[0]
                
                self.update_crawl_state('running', total_crawled)
                logger.info(f"Added {len(ip_batch)} IPs to task queue. Total crawled: {total_crawled}")
                
                # Wait for queue to process
                self.task_queue.join()
            
            return True
            
        except Exception as e:
            logger.error(f"Crawler error: {e}")
            self.stop_crawling()
            return False
    
    def stop_crawling(self) -> bool:
        """Stop the crawling process."""
        logger.info("Stopping crawler...")
        self.active = False
        self.stop_event.set()
        
        # Wait for threads to finish
        for _ in range(settings.max_threads):
            self.task_queue.put(None)  # Sentinel values to stop workers
        
        for thread in self.threads:
            thread.join(timeout=5)
        
        self.threads.clear()
        
        # Update crawl state
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM crawl_queue WHERE status = 'completed'")
                total_crawled = cursor.fetchone()[0]
            
            self.update_crawl_state('stopped', total_crawled)
            logger.info("Crawler stopped successfully")
            return True
        except Exception as e:
            logger.error(f"Error stopping crawler: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Get crawling statistics."""
        try:
            with db_manager.get_connection() as conn:
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
                
                cursor.execute("SELECT COUNT(*) FROM crawl_queue WHERE status = 'pending'")
                queue_size = cursor.fetchone()[0]
                
                cursor.execute("SELECT status, total_crawled, last_update FROM crawl_state WHERE id = 1")
                crawl_state = cursor.fetchone()
                
                return {
                    'active_hosts': active_hosts,
                    'total_hosts': total_hosts,
                    'total_keywords': total_keywords,
                    'total_pages': total_pages,
                    'crawl_status': crawl_state[0] if crawl_state else 'unknown',
                    'total_crawled': crawl_state[1] if crawl_state else 0,
                    'last_update': crawl_state[2] if crawl_state else None,
                    'queue_size': queue_size
                }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}


# Global crawler service instance
crawler_service = WebCrawlerService()

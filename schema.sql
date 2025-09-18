-- Web Crawler Search Engine Database Schema
-- This schema supports resumable crawling operations, host information,
-- page content with keywords and TF-IDF scores, and crawl queue management

-- Crawl state table for tracking overall crawl progress
CREATE TABLE IF NOT EXISTS crawl_state (
    id INTEGER PRIMARY KEY,
    current_network TEXT NOT NULL DEFAULT '0.0.0.0/0',
    status TEXT NOT NULL DEFAULT 'stopped', -- 'running', 'stopped', 'paused'
    total_crawled INTEGER DEFAULT 0,
    start_time TIMESTAMP,
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Hosts table for storing IP addresses and metadata
CREATE TABLE IF NOT EXISTS hosts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address TEXT UNIQUE NOT NULL,
    domain TEXT,
    last_crawled TIMESTAMP,
    status_code INTEGER,
    title TEXT,
    description TEXT,
    response_time REAL,
    server_info TEXT,
    content_type TEXT,
    is_active BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pages table for storing page content and metadata
CREATE TABLE IF NOT EXISTS pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    content_hash TEXT,
    title TEXT,
    meta_description TEXT,
    http_status INTEGER,
    load_time REAL,
    content_size INTEGER,
    last_crawled TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (host_id) REFERENCES hosts (id) ON DELETE CASCADE
);

-- Keywords table for storing extracted keywords
CREATE TABLE IF NOT EXISTS keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT UNIQUE NOT NULL,
    total_occurrences INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Page-keyword relationships with frequency data
CREATE TABLE IF NOT EXISTS page_keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    page_id INTEGER NOT NULL,
    keyword_id INTEGER NOT NULL,
    frequency INTEGER NOT NULL,
    tf_score REAL DEFAULT 0.0,
    idf_score REAL DEFAULT 0.0,
    tf_idf_score REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (page_id) REFERENCES pages (id) ON DELETE CASCADE,
    FOREIGN KEY (keyword_id) REFERENCES keywords (id) ON DELETE CASCADE,
    UNIQUE(page_id, keyword_id)
);

-- Crawl queue for managing IP addresses to be crawled
CREATE TABLE IF NOT EXISTS crawl_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address TEXT UNIQUE NOT NULL,
    status TEXT DEFAULT 'pending', -- 'pending', 'in-progress', 'completed', 'failed'
    priority INTEGER DEFAULT 0,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Robots.txt cache for respecting crawl policies
CREATE TABLE IF NOT EXISTS robots_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    host TEXT NOT NULL,
    robots_content TEXT,
    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    crawl_delay INTEGER DEFAULT 1,
    disallowed_paths TEXT, -- JSON array of disallowed paths
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(host)
);

-- Search history for analytics
CREATE TABLE IF NOT EXISTS search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    result_count INTEGER,
    search_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_ip TEXT,
    session_id TEXT
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_hosts_ip ON hosts(ip_address);
CREATE INDEX IF NOT EXISTS idx_hosts_active ON hosts(is_active);
CREATE INDEX IF NOT EXISTS idx_pages_host_id ON pages(host_id);
CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON keywords(keyword);
CREATE INDEX IF NOT EXISTS idx_page_keywords_page_id ON page_keywords(page_id);
CREATE INDEX IF NOT EXISTS idx_page_keywords_keyword_id ON page_keywords(keyword_id);
CREATE INDEX IF NOT EXISTS idx_crawl_queue_status ON crawl_queue(status);
CREATE INDEX IF NOT EXISTS idx_crawl_queue_ip ON crawl_queue(ip_address);
CREATE INDEX IF NOT EXISTS idx_robots_cache_host ON robots_cache(host);
CREATE INDEX IF NOT EXISTS idx_search_history_query ON search_history(query);
CREATE INDEX IF NOT EXISTS idx_search_history_time ON search_history(search_time);

-- Full-text search index for pages content
CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(
    title, 
    meta_description, 
    content,
    content=pages,
    content_rowid=id
);

-- Triggers to maintain data integrity and update timestamps
CREATE TRIGGER IF NOT EXISTS update_hosts_timestamp 
    AFTER UPDATE ON hosts
    FOR EACH ROW
    BEGIN
        UPDATE hosts SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_crawl_queue_timestamp 
    AFTER UPDATE ON crawl_queue
    FOR EACH ROW
    BEGIN
        UPDATE crawl_queue SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- Trigger to update FTS index when pages are updated
CREATE TRIGGER IF NOT EXISTS pages_ai AFTER INSERT ON pages BEGIN
    INSERT INTO pages_fts(rowid, title, meta_description, content) 
    VALUES (NEW.id, NEW.title, NEW.meta_description, 
            (SELECT content FROM pages WHERE id = NEW.id));
END;

CREATE TRIGGER IF NOT EXISTS pages_au AFTER UPDATE ON pages BEGIN
    UPDATE pages_fts SET 
        title = NEW.title, 
        meta_description = NEW.meta_description,
        content = (SELECT content FROM pages WHERE id = NEW.id)
    WHERE rowid = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS pages_ad AFTER DELETE ON pages BEGIN
    DELETE FROM pages_fts WHERE rowid = OLD.id;
END;

-- Initialize crawl state
INSERT OR IGNORE INTO crawl_state (id, status) VALUES (1, 'stopped');


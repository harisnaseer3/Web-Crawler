# Web Crawler Search Engine

A comprehensive web crawler search engine built with FastAPI backend and React frontend, featuring multithreaded crawling, resumable operations, and advanced search capabilities.

## Features

### Backend (FastAPI)
- **Multithreaded Web Crawler**: Random IP selection with configurable thread count
- **Resumable Operations**: Database-backed state management for stopping and resuming crawls
- **Advanced Search**: TF-IDF scoring for relevant search results
- **RESTful API**: Complete API for search, crawler management, and statistics
- **SQLite Database**: Optimized schema for crawl state, host info, and content storage
- **Robots.txt Respect**: Politeness delays and crawl policy compliance
- **Real-time Statistics**: Live monitoring of crawl progress and performance

### Frontend (React)
- **Modern Search Interface**: Clean, Google-like search experience
- **Real-time Dashboard**: Live crawler status and statistics monitoring
- **Responsive Design**: Mobile-friendly interface with Tailwind CSS
- **Advanced Controls**: Start, stop, pause, and resume crawler operations
- **Search Analytics**: Popular keywords and search statistics
- **Pagination**: Efficient browsing of search results

## Project Structure

```
crawler/
├── backend/                 # FastAPI backend
│   └── app/
│       ├── api/            # API endpoints
│       ├── core/           # Core configuration
│       ├── models/         # Pydantic schemas
│       ├── services/       # Business logic
│       └── utils/          # Utility functions
├── frontend/               # React frontend
│   ├── public/            # Static assets
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API services
│   │   └── styles/        # CSS styles
│   └── package.json
├── schema.sql             # Database schema
├── requirements.txt       # Python dependencies
└── README.md
```

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Initialize the database**:
   ```bash
   # The database will be automatically created when you start the backend
   ```

4. **Start the backend server**:
   ```bash
   cd backend
   python -m app.main
   # Or with uvicorn directly:
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

The API will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

### Frontend Setup

1. **Install Node.js dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Start the development server**:
   ```bash
   npm start
   ```

The frontend will be available at `http://localhost:3000`

## Usage

### Starting a Crawl

1. **Via API**:
   ```bash
   curl -X POST "http://localhost:8000/crawl/start" \
        -H "Content-Type: application/json" \
        -d '{"network": "0.0.0.0/0", "max_ips": 1000}'
   ```

2. **Via Frontend**:
   - Navigate to the Dashboard
   - Configure network range and max IPs
   - Click "Start" to begin crawling

### Searching

1. **Via API**:
   ```bash
   curl -X POST "http://localhost:8000/search/" \
        -H "Content-Type: application/json" \
        -d '{"query": "python programming", "limit": 10}'
   ```

2. **Via Frontend**:
   - Use the search bar on the homepage
   - Browse results with pagination
   - View detailed host information

### Monitoring Progress

- **Dashboard**: Real-time statistics and controls
- **API Endpoints**:
  - `GET /crawl/stats` - Current statistics
  - `GET /crawl/status` - Crawler status
  - `GET /crawl/queue/stats` - Queue information

## Configuration

### Backend Configuration

Key settings in `.env`:

```env
# Crawler Performance
MAX_THREADS=50              # Number of concurrent threads
MAX_IPS_PER_RUN=10000       # Maximum IPs per crawl session
BATCH_SIZE=100              # IPs processed per batch
REQUEST_TIMEOUT=5           # HTTP request timeout (seconds)
POLITENESS_DELAY=1.0        # Delay between requests (seconds)

# Search Settings
MAX_SEARCH_RESULTS=100      # Maximum search results
DEFAULT_SEARCH_LIMIT=10     # Default results per page
MAX_KEYWORDS_PER_PAGE=20    # Keywords extracted per page
```

### Frontend Configuration

Environment variables in `frontend/.env`:

```env
REACT_APP_API_URL=http://localhost:8000
```

## API Reference

### Search Endpoints

- `POST /search/` - Search crawled content
- `GET /search/domain/{domain}` - Search by domain
- `GET /search/keywords/popular` - Get popular keywords
- `GET /search/host/{ip_address}` - Get host details
- `GET /search/analytics` - Search analytics

### Crawler Endpoints

- `POST /crawl/start` - Start crawler
- `POST /crawl/stop` - Stop crawler
- `POST /crawl/pause` - Pause crawler
- `POST /crawl/resume` - Resume crawler
- `GET /crawl/status` - Get crawler status
- `GET /crawl/stats` - Get crawler statistics
- `POST /crawl/queue/populate` - Populate crawl queue

## Database Schema

The SQLite database includes:

- **crawl_state**: Overall crawl progress and status
- **hosts**: IP addresses and metadata
- **pages**: Page content and metadata
- **keywords**: Extracted keywords with frequency
- **page_keywords**: Page-keyword relationships with TF-IDF scores
- **crawl_queue**: Queue management for IP addresses
- **robots_cache**: Robots.txt compliance cache
- **search_history**: Search analytics and statistics

## Development

### Backend Development

```bash
cd backend
# Install development dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn app.main:app --reload

# Run tests
pytest
```

### Frontend Development

```bash
cd frontend
# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build
```

## Production Deployment

### Backend Deployment

1. **Using Gunicorn**:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
   ```

2. **Using Docker**:
   ```dockerfile
   FROM python:3.9-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

### Frontend Deployment

1. **Build and serve**:
   ```bash
   npm run build
   # Serve the build folder with any static server
   ```

2. **Using Nginx**:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       root /path/to/frontend/build;
       index index.html;
       
       location / {
           try_files $uri $uri/ /index.html;
       }
   }
   ```

## Performance Tuning

### Backend Optimization

- **Thread Count**: Adjust `MAX_THREADS` based on your system
- **Batch Size**: Larger batches reduce database overhead
- **Request Timeout**: Balance between speed and reliability
- **Database**: Consider PostgreSQL for high-volume deployments

### Frontend Optimization

- **Code Splitting**: Implement lazy loading for large components
- **Caching**: Add service worker for offline functionality
- **CDN**: Use CDN for static assets in production

## Troubleshooting

### Common Issues

1. **Database Locked**: Ensure only one crawler instance is running
2. **Memory Usage**: Reduce `MAX_THREADS` or `BATCH_SIZE`
3. **Rate Limiting**: Increase `POLITENESS_DELAY`
4. **CORS Errors**: Check `CORS_ORIGINS` configuration

### Logs

- Backend logs: `crawler.log`
- Frontend logs: Browser console
- Database: SQLite logs in system logs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation
- Review the API docs at `/docs`

# judex Deployment Guide

## 🚀 Deployment Overview

This guide covers deploying the judex STF data scraper in various environments, from development to production.

## ⚖️ Legal and Compliance Considerations

### Important Legal Notice

Before deploying this scraper, please be aware of the following legal considerations:

-   **robots.txt is not legally binding** - The STF portal's robots.txt file is a voluntary protocol with no legal force
-   **No Terms of Service found** - Despite extensive searching, the STF portal does not have publicly accessible terms of service
-   **Public data only** - This scraper only accesses publicly available case information
-   **Respectful scraping** - The scraper implements delays and follows ethical practices

### STF Portal robots.txt Analysis

```
User-agent: *
Disallow: /processos

User-agent: AhrefsBot
Disallow: /
```

The robots.txt disallows access to `/processos`, but this is not legally enforceable. The scraper accesses individual case pages through direct URLs, not the disallowed directory.

### Ethical Scraping Practices

The scraper implements several ethical practices:

-   **Download delays**: 2-second delays between requests
-   **Concurrent request limits**: Maximum 1 concurrent request
-   **Error handling**: Graceful handling of rate limits and errors
-   **Respectful user agent**: Identifies itself as a research tool

## 📋 Prerequisites

### System Requirements

-   **Python**: 3.10 or higher
-   **Memory**: Minimum 2GB RAM (4GB+ recommended)
-   **Storage**: 10GB+ free space for database and logs
-   **Network**: Stable internet connection for web scraping

### Software Dependencies

-   **Chrome/Chromium**: Latest stable version
-   **ChromeDriver**: Compatible with Chrome version
-   **SQLite**: 3.8+ (usually included with Python)

### Python Dependencies

```bash
# Core dependencies
pydantic>=2.12.2
scrapy>=2.13.3
scrapy-selenium>=0.0.7
selenium<4.0.0
beautifulsoup4>=4.14.2
pandas>=2.3.3

# Development dependencies
pytest>=8.4.2
pytest-cov>=7.0.0
black>=25.9.0
mypy>=1.18.2
ruff>=0.14.0
```

## 🛠 Installation Methods

### Method 1: Using uv (Recommended)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
git clone <repository-url>
cd judex

# Install dependencies
uv sync

# Verify installation
uv run python -c "import judex; print('Installation successful')"
```

### Method 2: Using pip

```bash
# Clone repository
git clone <repository-url>
cd judex

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Verify installation
python -c "import judex; print('Installation successful')"
```

### Method 3: Using Docker

```dockerfile
# Dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d'.' -f1-3) \
    && CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}") \
    && wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROMEDRIVER_PATH=/usr/local/bin/chromedriver

# Default command
CMD ["python", "-m", "judex.core"]
```

```bash
# Build and run Docker container
docker build -t judex .
docker run -v $(pwd)/data:/app/data judex
```

## 🔧 Configuration

### Environment Variables

```bash
# Database configuration
export DATABASE_PATH="/path/to/judex.db"
export DATABASE_BACKUP_PATH="/path/to/backups/"

# Scraping configuration
export DOWNLOAD_DELAY="2.0"
export CONCURRENT_REQUESTS="1"
export AUTOTHROTTLE_ENABLED="true"

# Selenium configuration
export CHROME_BIN="/usr/bin/google-chrome"
export CHROMEDRIVER_PATH="/usr/local/bin/chromedriver"
export SELENIUM_HEADLESS="true"

# Logging configuration
export LOG_LEVEL="INFO"
export LOG_FILE="/var/log/judex/judex.log"

# Output configuration
export OUTPUT_DIR="/var/lib/judex/output"
export EXPORT_FORMAT="csv,json"
```

### Configuration Files

#### `judex/settings.py`

```python
# Database settings
DATABASE_PATH = os.getenv("DATABASE_PATH", "judex.db")
DATABASE_BACKUP_ENABLED = True
DATABASE_BACKUP_INTERVAL = 3600  # seconds

# Scraping settings
DOWNLOAD_DELAY = float(os.getenv("DOWNLOAD_DELAY", "2.0"))
CONCURRENT_REQUESTS = int(os.getenv("CONCURRENT_REQUESTS", "1"))
AUTOTHROTTLE_ENABLED = os.getenv("AUTOTHROTTLE_ENABLED", "true").lower() == "true"

# Selenium settings
SELENIUM_DRIVER_NAME = "chrome"
SELENIUM_DRIVER_EXECUTABLE_PATH = os.getenv("CHROMEDRIVER_PATH")
SELENIUM_DRIVER_ARGUMENTS = [
    "--headless" if os.getenv("SELENIUM_HEADLESS", "true").lower() == "true" else "",
    "--incognito",
    "--window-size=920,600",
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-dev-shm-usage",
]

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "judex.log")

# Output settings
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
EXPORT_FORMATS = os.getenv("EXPORT_FORMAT", "csv").split(",")
```

#### `config.yaml`

```yaml
# Database configuration
database:
    path: 'judex.db'
    backup_enabled: true
    backup_interval: 3600
    max_connections: 10

# Scraping configuration
scraping:
    download_delay: 2.0
    concurrent_requests: 1
    autothrottle_enabled: true
    retry_times: 3
    retry_http_codes: [403, 408, 429, 500, 502, 503, 504]

# Selenium configuration
selenium:
    driver_name: 'chrome'
    headless: true
    window_size: '920,600'
    arguments:
        - '--incognito'
        - '--no-sandbox'
        - '--disable-dev-shm-usage'

# Logging configuration
logging:
    level: 'INFO'
    file: 'judex.log'
    max_size: '10MB'
    backup_count: 5

# Output configuration
output:
    directory: 'output'
    formats: ['csv', 'json']
    compression: false
```

## 🏗 Deployment Environments

### Development Environment

```bash
# Local development setup
git clone <repository-url>
cd judex
uv sync --group dev

# Run tests
uv run python -m pytest

# Start development server
uv run python -m judex.core --config config.yaml
```

### Staging Environment

```bash
# Staging deployment
export ENVIRONMENT="staging"
export DATABASE_PATH="/var/lib/judex/staging.db"
export LOG_LEVEL="DEBUG"
export OUTPUT_DIR="/var/lib/judex/staging/output"

# Run with staging configuration
uv run python -m judex.core --config config.staging.yaml
```

### Production Environment

#### Systemd Service

```ini
# /etc/systemd/system/judex.service
[Unit]
Description=judex STF Data Scraper
After=network.target

[Service]
Type=simple
User=judex
Group=judex
WorkingDirectory=/opt/judex
Environment=PYTHONPATH=/opt/judex
Environment=DATABASE_PATH=/var/lib/judex/judex.db
Environment=LOG_LEVEL=INFO
Environment=OUTPUT_DIR=/var/lib/judex/output
ExecStart=/opt/judex/.venv/bin/python -m judex.core --config /etc/judex/config.yaml
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable judex
sudo systemctl start judex
sudo systemctl status judex
```

#### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
    judex:
        build: .
        container_name: judex
        restart: unless-stopped
        volumes:
            - ./data:/app/data
            - ./logs:/app/logs
            - ./config:/app/config
        environment:
            - DATABASE_PATH=/app/data/judex.db
            - LOG_LEVEL=INFO
            - OUTPUT_DIR=/app/data/output
        command: python -m judex.core --config /app/config/config.yaml

    nginx:
        image: nginx:alpine
        container_name: judex-nginx
        ports:
            - '80:80'
        volumes:
            - ./nginx.conf:/etc/nginx/nginx.conf
            - ./data:/var/www/html
        depends_on:
            - judex
```

## 📊 Monitoring and Logging

### Logging Configuration

```python
# logging_config.py
import logging
import logging.handlers
from pathlib import Path

def setup_logging(log_level="INFO", log_file="judex.log"):
    """Setup logging configuration"""

    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.handlers.RotatingFileHandler(
                log_dir / log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            ),
            logging.StreamHandler()
        ]
    )

    return logging.getLogger("judex")
```

### Health Checks

```python
# health_check.py
import sqlite3
import requests
from pathlib import Path

def check_database_health(db_path):
    """Check database connectivity and integrity"""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM processos")
            count = cursor.fetchone()[0]
            return {"status": "healthy", "record_count": count}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

def check_selenium_health():
    """Check Selenium WebDriver health"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")

        driver = webdriver.Chrome(options=options)
        driver.get("https://www.google.com")
        driver.quit()
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

def check_system_health():
    """Comprehensive system health check"""
    return {
        "database": check_database_health("judex.db"),
        "selenium": check_selenium_health(),
        "timestamp": datetime.now().isoformat()
    }
```

### Prometheus Metrics

```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

# Metrics
scraping_requests_total = Counter('scraping_requests_total', 'Total scraping requests', ['status'])
scraping_duration_seconds = Histogram('scraping_duration_seconds', 'Scraping duration')
database_connections = Gauge('database_connections', 'Active database connections')
memory_usage_bytes = Gauge('memory_usage_bytes', 'Memory usage in bytes')

def setup_metrics(port=8000):
    """Setup Prometheus metrics server"""
    start_http_server(port)
    return {
        'scraping_requests_total': scraping_requests_total,
        'scraping_duration_seconds': scraping_duration_seconds,
        'database_connections': database_connections,
        'memory_usage_bytes': memory_usage_bytes
    }
```

## 🔒 Security Considerations

### Access Control

```bash
# Create dedicated user
sudo useradd -r -s /bin/false judex
sudo mkdir -p /var/lib/judex
sudo chown judex:judex /var/lib/judex
sudo chmod 750 /var/lib/judex
```

### Network Security

```bash
# Firewall configuration
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (if serving web interface)
sudo ufw deny 8000/tcp   # Block metrics port from external access
sudo ufw enable
```

### Data Protection

```python
# data_encryption.py
import sqlite3
from cryptography.fernet import Fernet
import os

def encrypt_database(db_path, key_path):
    """Encrypt database file"""
    with open(key_path, 'rb') as f:
        key = f.read()

    fernet = Fernet(key)

    with open(db_path, 'rb') as f:
        data = f.read()

    encrypted_data = fernet.encrypt(data)

    with open(f"{db_path}.encrypted", 'wb') as f:
        f.write(encrypted_data)

def decrypt_database(encrypted_path, key_path, output_path):
    """Decrypt database file"""
    with open(key_path, 'rb') as f:
        key = f.read()

    fernet = Fernet(key)

    with open(encrypted_path, 'rb') as f:
        encrypted_data = f.read()

    decrypted_data = fernet.decrypt(encrypted_data)

    with open(output_path, 'wb') as f:
        f.write(decrypted_data)
```

## 📈 Performance Optimization

### Database Optimization

```sql
-- Create indexes for better performance
CREATE INDEX idx_processos_classe ON processos(classe);
CREATE INDEX idx_processos_data_protocolo ON processos(data_protocolo);
CREATE INDEX idx_processos_relator ON processos(relator);
CREATE INDEX idx_partes_numero_unico ON partes(numero_unico);
CREATE INDEX idx_andamentos_numero_unico ON andamentos(numero_unico);

-- Analyze database for query optimization
ANALYZE;
```

### Memory Optimization

```python
# memory_optimization.py
import gc
import psutil
import os

def optimize_memory():
    """Optimize memory usage"""
    # Force garbage collection
    gc.collect()

    # Monitor memory usage
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()

    # Log memory usage
    logger.info(f"Memory usage: {memory_info.rss / 1024 / 1024:.2f} MB")

    # Cleanup if memory usage is high
    if memory_info.rss > 1024 * 1024 * 1024:  # 1GB
        logger.warning("High memory usage detected, forcing cleanup")
        gc.collect()
```

### Concurrent Processing

```python
# concurrent_processing.py
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

async def async_scraping(session, url):
    """Async scraping function"""
    async with session.get(url) as response:
        return await response.text()

def parallel_scraping(urls, max_workers=4):
    """Parallel scraping with thread pool"""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(scrape_url, url) for url in urls]
        results = [future.result() for future in futures]
    return results
```

## 🚨 Troubleshooting

### Common Issues

#### ChromeDriver Issues

```bash
# Check ChromeDriver version
chromedriver --version

# Check Chrome version
google-chrome --version

# Update ChromeDriver
sudo apt-get update
sudo apt-get install chromium-chromedriver
```

#### Database Issues

```bash
# Check database integrity
sqlite3 judex.db "PRAGMA integrity_check;"

# Repair database
sqlite3 judex.db "VACUUM;"

# Backup database
cp judex.db judex.db.backup
```

#### Memory Issues

```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head

# Kill high memory processes
sudo pkill -f judex
```

### Log Analysis

```bash
# View recent logs
tail -f /var/log/judex/judex.log

# Search for errors
grep -i error /var/log/judex/judex.log

# Monitor real-time logs
journalctl -u judex -f
```

### Performance Monitoring

```bash
# Monitor system resources
htop
iotop
nethogs

# Monitor database
sqlite3 judex.db "SELECT COUNT(*) FROM processos;"
sqlite3 judex.db ".schema"
```

This deployment guide provides comprehensive instructions for deploying judex in various environments, ensuring reliable and scalable operation.

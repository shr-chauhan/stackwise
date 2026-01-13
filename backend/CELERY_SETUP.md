# Celery AI Analysis Pipeline Setup

## Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Start Redis
**Windows (Docker):**
```powershell
docker run -d -p 6379:6379 redis
```

**macOS:**
```bash
brew install redis && brew services start redis
```

**Linux:**
```bash
sudo apt-get install redis-server && sudo systemctl start redis
```

### 3. Run Migration & Start Services

**Terminal 1 - FastAPI:**
```bash
cd backend
.\venv\Scripts\Activate.ps1  # Windows
# or: source venv/bin/activate  # macOS/Linux
alembic upgrade head
uvicorn app.main:app --reload
```

**Terminal 2 - Celery Worker:**
```bash
cd backend
.\venv\Scripts\Activate.ps1  # Windows
# Windows (requires --pool=solo):
celery -A app.celery_worker worker --loglevel=info --queues=ai_analysis --pool=solo
# macOS/Linux:
# celery -A app.celery_worker worker --loglevel=info --queues=ai_analysis --concurrency=2
```

### 4. Test It

Send a 500 error:
```bash
curl -X POST http://localhost:8000/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "project_key": "test",
    "message": "Server error",
    "method": "GET",
    "path": "/api/test",
    "status_code": 500,
    "timestamp": "2024-01-15T12:00:00Z"
  }'
```

Check analysis in database:
```sql
SELECT e.id, e.status_code, a.analysis_text 
FROM error_events e 
LEFT JOIN error_analysis a ON e.id = a.error_event_id 
WHERE e.status_code >= 500;
```

## Overview

This setup adds an asynchronous AI analysis pipeline using Redis + Celery to analyze error events with status_code >= 500.

## Architecture

```
FastAPI → Store Error Event → Enqueue Celery Task (if status_code >= 500)
                                    ↓
                              Redis Queue (ai_analysis)
                                    ↓
                              Celery Worker
                                    ↓
                              AI Analysis → Store in error_analysis table
```

## Prerequisites

1. **Redis** must be running
2. **PostgreSQL** database (already set up)
3. **Python dependencies** installed

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Redis

Add to your `.env` file:

```env
REDIS_URL=redis://localhost:6379/0
```

### 3. Start Redis

**Windows:**
- Download Redis from https://github.com/microsoftarchive/redis/releases
- Or use Docker: `docker run -d -p 6379:6379 redis`

**macOS:**
```bash
brew install redis
brew services start redis
```

**Linux:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

### 4. Run Database Migration

Apply the existing migration for `error_analysis` table:

```bash
alembic upgrade head
```

### 5. Start Celery Worker

**Windows (PowerShell):**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
celery -A app.celery_worker worker --loglevel=info --queues=ai_analysis --pool=solo
```

**Note for Windows**: The `--pool=solo` flag is **required** on Windows. The default `prefork` pool doesn't work on Windows due to process forking limitations.

**macOS/Linux:**
```bash
cd backend
source venv/bin/activate
celery -A app.celery_worker worker --loglevel=info --queues=ai_analysis --concurrency=2
```

Or use the provided scripts:
- Windows: `worker_start.bat` (includes `--pool=solo`)
- Unix: `worker_start.sh`

## How It Works

### 1. Error Ingestion Flow

1. Client sends error event to `/api/v1/events`
2. FastAPI stores error in PostgreSQL
3. **If status_code >= 500**: Enqueues Celery task (non-blocking)
4. API returns immediately (doesn't wait for analysis)

### 2. AI Analysis Flow

1. Celery worker picks up task from `ai_analysis` queue
2. Worker fetches error event from database
3. Checks:
   - Skip if status_code < 500
   - Skip if analysis already exists
4. Calls AI/LLM (currently mocked)
5. Stores analysis in `error_analysis` table

### 3. Task Retry Logic

- **Max retries**: 3
- **Backoff**: Exponential (up to 10 minutes)
- **Timeout**: 4 minutes soft, 5 minutes hard
- **Auto-retry**: On any Exception

## Configuration

### Celery Settings (in `app/celery_app.py`)

- **Queue**: `ai_analysis` (dedicated queue)
- **Broker**: Redis
- **Task timeout**: 4-5 minutes (suitable for LLM calls)
- **Retries**: 3 with exponential backoff
- **Concurrency**: 2 workers (adjustable)

### Environment Variables

```env
REDIS_URL=redis://localhost:6379/0
```

## Testing

### 1. Start Services

**Terminal 1 - FastAPI:**
```bash
cd backend
uvicorn app.main:app --reload
```

**Terminal 2 - Celery Worker:**
```bash
# Windows:
cd backend
celery -A app.celery_worker worker --loglevel=info --queues=ai_analysis --pool=solo

# macOS/Linux:
cd backend
celery -A app.celery_worker worker --loglevel=info --queues=ai_analysis --concurrency=2
```

**Terminal 3 - Redis (if not running as service):**
```bash
redis-server
```

### 2. Trigger Error Event

Send an error with status_code >= 500:

```bash
curl -X POST http://localhost:8000/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "project_key": "test-project",
    "message": "Database connection failed",
    "stack": "Error: Connection timeout",
    "method": "GET",
    "path": "/api/users",
    "status_code": 500,
    "timestamp": "2024-01-15T12:00:00Z"
  }'
```

### 3. Verify Analysis

Check the database:

```sql
SELECT 
    e.id as error_id,
    e.status_code,
    e.payload->>'message' as error_message,
    a.analysis_text,
    a.model,
    a.confidence,
    a.created_at
FROM error_events e
LEFT JOIN error_analysis a ON e.id = a.error_event_id
WHERE e.status_code >= 500
ORDER BY e.created_at DESC
LIMIT 5;
```

## Monitoring

### Check Celery Worker Status

```bash
celery -A app.celery_worker inspect active
celery -A app.celery_worker inspect stats
```

### Check Redis Queue

```bash
redis-cli
> LLEN celery  # Check queue length
> KEYS *       # List all keys
```

## Production Considerations

1. **Scale Workers**: Run multiple worker processes
   ```bash
   celery -A app.celery_worker worker --loglevel=info --queues=ai_analysis --concurrency=4
   ```

2. **Monitor**: Use Flower for Celery monitoring
   ```bash
   pip install flower
   celery -A app.celery_worker flower
   ```

3. **Replace Mock LLM**: Update `perform_ai_analysis()` in `app/tasks.py` with actual LLM API call

4. **Error Handling**: Current implementation retries on any exception - consider filtering retryable errors

## Troubleshooting

### Windows: PermissionError [WinError 5] Access is denied

**Symptom**: Worker crashes with `PermissionError: [WinError 5] Access is denied` when using default `prefork` pool.

**Solution**: Use `--pool=solo` flag on Windows:
```powershell
celery -A app.celery_worker worker --loglevel=info --queues=ai_analysis --pool=solo
```

**Why**: Windows doesn't support Unix-style process forking. The `solo` pool runs tasks in the main process, which works perfectly for development and small workloads on Windows.

### Worker not picking up tasks
- Check Redis is running: `redis-cli ping` (should return PONG)
- Verify queue name matches: `--queues=ai_analysis`
- Check worker logs for errors

### Tasks failing
- Check database connection
- Verify error_event exists
- Check worker logs for detailed errors

### Tasks not being enqueued
- Check FastAPI logs for enqueue errors
- Verify Celery app is imported correctly
- Check Redis connection

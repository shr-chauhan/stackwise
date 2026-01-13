# Stackwise - AI-Powered Error Debugging Platform

An open-source error ingestion and debugging system with AI-powered analysis for capturing, storing, and intelligently analyzing application errors.

> **Important**: StackWise is a **self-hosted** error analysis platform. This project does **not** provide a hosted SaaS offering. Users are expected to deploy and operate StackWise in their own environment.

## Overview

Stackwise provides a complete solution for error tracking and debugging:
- **Node.js SDK**: Express middleware that captures errors automatically
- **FastAPI Backend**: RESTful API for receiving and storing error events
- **Next.js Dashboard**: Modern web UI for project management and error viewing
- **AI-Powered Analysis**: Automatic error analysis using LLMs with source code context
- **PostgreSQL Storage**: Efficient storage with JSONB payloads
- **Celery Workers**: Asynchronous AI analysis pipeline

## Architecture

```
┌─────────────┐         HTTP POST          ┌─────────────┐
│   Express   │ ──────────────────────────> │   FastAPI   │
│     App     │                             │   Backend   │
│             │                             │             │
│  SDK Middle │                             │  PostgreSQL │
│    ware     │                             │  Database   │
└─────────────┘                             └─────────────┘
                                                    │
                                                    │ Enqueue
                                                    ▼
                                            ┌─────────────┐
                                            │   Redis     │
                                            │   Queue     │
                                            └─────────────┘
                                                    │
                                                    │ Process
                                                    ▼
                                            ┌─────────────┐
                                            │   Celery    │
                                            │   Worker    │
                                            │  (AI Analysis)
                                            └─────────────┘
                                                    │
┌─────────────┐         HTTP GET           ┌─────────────┐
│   Next.js   │ ──────────────────────────> │   FastAPI   │
│  Dashboard  │                             │   Backend   │
│             │                             │             │
│  (UI/UX)    │ <────────────────────────── │  (REST API) │
└─────────────┘         JSON Response       └─────────────┘
```

## Project Structure

```
.
├── backend/          # FastAPI backend application
│   ├── app/          # Application code
│   │   ├── celery/   # Celery workers for AI analysis
│   │   ├── database/ # Database models and connection
│   │   └── utils/    # Utilities (auth, git fetcher, etc.)
│   ├── alembic/      # Database migrations
│   └── README.md     # Backend documentation
├── frontend/         # Next.js dashboard (web UI)
│   ├── app/          # Next.js app router pages
│   ├── components/   # React components
│   ├── lib/          # API client and utilities
│   └── README.md     # Frontend documentation
├── sdks/
│   └── node/         # Node.js SDK (npm package)
│       └── README.md # SDK documentation
└── example/          # Example Express app
```

## Quick Start

### 1. Start Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set up database (see backend/README.md for details)
createdb error_ingestion
alembic upgrade head

# Configure environment
cp env.example .env
# Edit .env with your database credentials, Redis URL, and OpenAI API key

# Start Redis (required for Celery)
# Windows: docker run -d -p 6379:6379 redis
# macOS: brew services start redis
# Linux: sudo systemctl start redis

# Run server
uvicorn app.main:app --reload
```

Backend will be available at `http://localhost:8000`

### 2. Start Celery Worker (for AI Analysis)

```bash
cd backend

# In a separate terminal, start Celery worker
celery -A app.celery.celery_app worker --loglevel=info --queues=ai_analysis
```

See [CELERY_SETUP.md](./backend/CELERY_SETUP.md) for detailed setup.

### 3. Start Frontend Dashboard

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp env.example .env.local
# Edit .env.local with your backend API URL and GitHub OAuth credentials

# Run development server
npm run dev
```

Frontend will be available at `http://localhost:3000`

### 4. Install SDK

```bash
cd sdks/node

# Install dependencies
npm install

# Build TypeScript
npm run build
```

### 3. Use in Your Express App

```javascript
const express = require('express');
const { errorIngestionMiddleware } = require('@error-ingestion/sdk-node');

const app = express();

// Add error ingestion middleware (after routes, before error handler)
app.use(errorIngestionMiddleware({
  apiUrl: 'http://localhost:8000',
  projectKey: 'my-project'
}));

// Your routes...
app.get('/api/users/:id', async (req, res, next) => {
  try {
    // Your code
  } catch (err) {
    next(err); // Error will be automatically captured
  }
}));

app.listen(3000);
```

### 5. Test with Example App

```bash
cd example

# Install dependencies
npm install

# Run example
npm start

# Trigger test error
curl http://localhost:3000/test-error
```

## Features

### SDK Features
- ✅ Express error-handling middleware
- ✅ Automatic error capture (message, stack, method, path, status code)
- ✅ Path sanitization (replaces IDs with `:id` to reduce cardinality)
- ✅ Non-blocking (doesn't interrupt request handling)
- ✅ Duplicate prevention (symbol flag prevents double ingestion)
- ✅ TypeScript support with type definitions

### Backend Features
- ✅ RESTful API with FastAPI
- ✅ Request validation with Pydantic
- ✅ PostgreSQL storage with JSONB payloads
- ✅ Automatic project creation
- ✅ Database migrations with Alembic
- ✅ Comprehensive error logging
- ✅ Thread-safe project creation
- ✅ GitHub OAuth authentication
- ✅ User and project management
- ✅ Asynchronous AI analysis with Celery
- ✅ Source code fetching from Git repositories

### Frontend Features
- ✅ Modern Next.js dashboard with TypeScript
- ✅ GitHub OAuth authentication
- ✅ Project management (create, view, edit projects)
- ✅ Error event viewing and filtering
- ✅ AI analysis results display
- ✅ Repository configuration
- ✅ SDK setup instructions
- ✅ Responsive design with Tailwind CSS

### AI Analysis Features
- ✅ Automatic analysis for errors (status_code >= 500)
- ✅ Stack trace parsing and file path extraction
- ✅ Source code context from Git repositories
- ✅ LLM-powered error debugging (OpenAI GPT models)
- ✅ Confidence scoring and model tracking
- ✅ Source code usage tracking

## Documentation

- **[Backend README](./backend/README.md)** - Backend setup, API documentation, migrations
- **[Frontend README](./frontend/README.md)** - Frontend dashboard setup and features
- **[SDK README](./sdks/node/README.md)** - SDK installation and usage
- **[Alembic Setup](./backend/ALEMBIC_SETUP.md)** - Database migration guide
- **[AI Debugging](./backend/AI_DEBUGGING.md)** - AI-powered error analysis documentation
- **[Celery Setup](./backend/CELERY_SETUP.md)** - Celery worker setup for AI analysis (includes quick start)
- **[Deployment Guide](./DEPLOYMENT.md)** - Docker Compose deployment (single & distributed)

## Configuration

### Backend
- See `backend/README.md` for environment variables and configuration
- Requires: PostgreSQL, Redis, OpenAI API key (for AI analysis)

### Frontend
- See `frontend/README.md` for environment variables and configuration
- Requires: Backend API URL, GitHub OAuth credentials

### SDK
- `apiUrl`: Backend API URL (required)
- `projectKey`: Project identifier (required)
- `timeout`: Request timeout in ms (optional, default: 5000)

## Development

### Backend
```bash
cd backend
# See backend/README.md for development setup
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# See frontend/README.md for detailed setup
```

### Celery Worker
```bash
cd backend
celery -A app.celery.celery_app worker --loglevel=info --queues=ai_analysis
```

### SDK
```bash
cd sdks/node
npm install
npm run build
```

## Production Deployment

### Docker Compose Deployment (Recommended)

The easiest way to deploy Stackwise is using Docker Compose. See **[DEPLOYMENT.md](./DEPLOYMENT.md)** for detailed deployment guide.

#### Quick Start with Docker

1. **Set up environment:**
   ```bash
   cp env.production.example .env
   # Edit .env with your production values
   ```

2. **Start all services:**
   ```bash
   docker-compose up -d
   ```

3. **Check status:**
   ```bash
   docker-compose ps
   ```

#### Deployment Options

- **Single Machine**: All services on one server (see `docker-compose.yml`)
- **Distributed**: Services across multiple machines (see `docker-compose.distributed.yml`)
- **Docker Swarm**: For orchestration across multiple nodes

See **[DEPLOYMENT.md](./DEPLOYMENT.md)** for:
- Single machine deployment
- Distributed deployment strategies
- Scaling options
- Security best practices
- Monitoring and backup

### Manual Deployment

#### Backend
1. Set `ENV=production` in `.env`
2. Run migrations: `alembic upgrade head`
3. Deploy with production WSGI server (e.g., Gunicorn)
4. Deploy Celery worker separately or on same server

#### Frontend
1. Build: `npm run build`
2. Deploy to Vercel, Netlify, or any Node.js hosting
3. Configure environment variables in hosting platform

#### SDK
1. Build: `npm run build`
2. Publish to npm (or use as local package)

### Cloud Deployment Options

- **Frontend**: Vercel (free tier, excellent CDN)
- **Backend**: Railway, DigitalOcean, or AWS
- **Database**: Railway Postgres, Neon, or Supabase
- **Redis**: Railway, Upstash, or AWS ElastiCache

## Tech Stack

- **Frontend**: Next.js 16, TypeScript, Tailwind CSS, NextAuth.js
- **Backend**: FastAPI, Python 3.11+, SQLAlchemy, Pydantic
- **Database**: PostgreSQL with JSONB
- **Queue**: Redis + Celery
- **AI**: OpenAI GPT models (configurable)
- **SDK**: Node.js/TypeScript

## Assumptions

1. **Project Key**: Projects identified by `project_key`, created via API
2. **Non-blocking**: SDK failures don't interrupt request handling
3. **Authentication**: GitHub OAuth for dashboard access
4. **Path Sanitization**: IDs in paths are replaced with `:id` placeholder
5. **Error Handling**: Backend validates all fields and returns appropriate HTTP codes
6. **AI Analysis**: Automatically triggered for errors with status_code >= 500

## Next Steps (Future Phases)

- Error grouping and deduplication
- Real-time error notifications
- Rate limiting
- Error filtering and rules
- Additional SDKs (Python, Ruby, etc.)
- Custom AI model support
- Error trends and analytics

## Contributing

We welcome contributions to StackWise! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines on how to contribute.

Key points:
- **PRs are welcome** - We appreciate all contributions, big or small
- **Large changes should be discussed first** - For significant changes, please open an issue first to discuss the approach
- **This is a self-hosted project** - StackWise is designed to be self-hosted, not a SaaS offering

## License

MIT


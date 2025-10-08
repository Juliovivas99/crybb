# CryBB Bot Live Testing Setup Guide

## ✅ Completed Setup Tasks

### 1️⃣ Environment Configuration

- ✅ Created `.env` template with all required variables
- ✅ Updated `src/config.py` validation for live mode and AI pipeline
- ✅ Added proper environment variable handling

### 2️⃣ Docker Configuration

- ✅ Created `docker-compose.yml` with restart policies and health checks
- ✅ Updated `Dockerfile` to include curl for health checks
- ✅ Fixed Docker command to use `python3 src/main.py`

### 3️⃣ Health Server

- ✅ Created `src/server.py` with FastAPI health endpoints
- ✅ Modified `src/main.py` to run health server concurrently
- ✅ Added `/health` and `/metrics` endpoints for monitoring

## 🚀 Next Steps for Live Testing

### Step 1: Configure Environment Variables

Create your `.env` file in the project root with your actual credentials:

```bash
# Copy the template
cp env.example .env

# Edit with your actual values
nano .env
```

**Required Variables:**

```env
# X API (Basic plan)
API_KEY=your_api_key_here
API_SECRET=your_api_secret_here
ACCESS_TOKEN=your_access_token_here
ACCESS_SECRET=your_access_secret_here
BEARER_TOKEN=your_bearer_token_here

# OAuth2 (Basic plan requirement)
CLIENT_ID=your_client_id_here
CLIENT_SECRET=your_client_secret_here

# Bot identity
BOT_HANDLE=@crybbmaker

# General
POLL_SECONDS=30
HTTP_TIMEOUT_SECS=15
TWITTER_MODE=live

# AI
REPLICATE_API_TOKEN=your_replicate_token_here
REPLICATE_MODEL=google/nano-banana
REPLICATE_TIMEOUT_SECS=120
REPLICATE_POLL_INTERVAL_SECS=2
AI_MAX_CONCURRENCY=2
AI_MAX_ATTEMPTS=2
IMAGE_PIPELINE=ai
CRYBB_STYLE_URL=https://crybb-assets-p55s0u52l-juliovivas99s-projects.vercel.app/crybb.jpeg

# Optional
```

### Step 2: Test Locally (Debug Mode)

Before deploying to Docker, test locally to see real-time behavior:

```bash
# Set live mode
export TWITTER_MODE=live

# Run the bot
python3 src/main.py
```

**Expected Output:**

```
Bot initialized: @crybbmaker (ID: 123456789)
Health server started on port 8000
Starting CryBB Maker Bot...
Polling for mentions since ID: None
No new mentions found
```

**Test the health endpoint:**

```bash
curl http://localhost:8000/health
curl http://localhost:8000/metrics
```

### Step 3: Trigger Bot with Test Tweet

1. From another X account, tweet: `@crybbmaker make me crybb`
2. Watch the logs for:
   - ✅ Mention detection
   - ✅ AI generation (URL + timing)
   - ✅ Reply with media upload success

### Step 4: Deploy with Docker

Once local tests work, deploy to run 24/7:

```bash
# Build and start
docker compose up -d --build

# Watch logs
docker compose logs -f crybb-bot

# Check health
curl http://localhost:8000/health
```

### Step 5: Verify End-to-End

1. Send a real mention from another X account
2. Within 30–60 seconds you should see a reply with AI-generated image
3. If anything fails, check:
   - `docker compose logs -f crybb-bot`
   - `python tools/run_diagnostics.py` for backend issues

## 🔧 Troubleshooting

### Common Issues:

1. **Missing Environment Variables**

   ```bash
   python tools/run_diagnostics.py --mode auto
   ```

2. **API Rate Limits**

   - Bot respects Twitter rate limits automatically
   - Check logs for "Rate limited" messages

3. **AI Generation Failures**

   - Verify `REPLICATE_API_TOKEN` is valid
   - Check `CRYBB_STYLE_URL` is accessible
   - Monitor AI timeout settings

4. **Docker Health Check Failures**
   ```bash
   # Check if health endpoint is responding
   docker exec crybb-bot curl -f http://localhost:8000/health
   ```

### Monitoring Commands:

```bash
# View real-time logs
docker compose logs -f crybb-bot

# Check container status
docker compose ps

# Restart if needed
docker compose restart crybb-bot

# Stop and clean up
docker compose down
```

## ✅ Acceptance Criteria Checklist

- [ ] `.env` is correctly filled with real credentials
- [ ] Bot can be run locally in live mode
- [ ] Health endpoints respond correctly (`/health`, `/metrics`)
- [ ] Bot successfully replies to mentions with AI image
- [ ] Docker deployment runs continuously with restart policy
- [ ] End-to-end test with real Twitter mention works

## 🎯 Optional Next Steps

Once live testing works, consider adding:

- Slack/Telegram notifier for errors
- Auto-restart AI jobs on failures
- `/metrics` endpoint enhancements
- Prometheus/Grafana monitoring
- Automated backup of `since_id` data

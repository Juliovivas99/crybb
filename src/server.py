"""
FastAPI health server for CryBB Maker Bot.
Provides health check and metrics endpoints for container orchestration.
"""
from fastapi import FastAPI
from datetime import datetime
import os
import time
from config import Config

app = FastAPI(title="CryBB Maker Bot", version="2.0.0")

# Global metrics counters
metrics = {
    "processed": 0,
    "ai_fail": 0,
    "rate_limited": 0,
    "replies_sent": 0,
    "last_mention_time": None,
    "since_id": None
}

@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration."""
    return {
        "ok": True,
        "timestamp": datetime.utcnow().isoformat(),
        "image_pipeline": Config.IMAGE_PIPELINE,
        "last_mention_time": metrics["last_mention_time"],
        "since_id": metrics["since_id"],
        "bot_handle": Config.BOT_HANDLE,
        "twitter_mode": Config.TWITTER_MODE
    }

@app.get("/metrics")
async def get_metrics():
    """Metrics endpoint with counters and status."""
    return {
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "counters": {
            "processed": metrics["processed"],
            "ai_fail": metrics["ai_fail"],
            "rate_limited": metrics["rate_limited"],
            "replies_sent": metrics["replies_sent"]
        },
        "config": {
            "bot_handle": Config.BOT_HANDLE,
            "twitter_mode": Config.TWITTER_MODE,
            "image_pipeline": Config.IMAGE_PIPELINE,
            "poll_seconds": Config.POLL_SECONDS,
            "ai_model": Config.REPLICATE_MODEL,
            "rate_limit_per_hour": Config.RATE_LIMIT_PER_HOUR
        },
        "environment": {
            "port": Config.PORT,
            "python_path": os.environ.get("PYTHONPATH", ""),
            "working_directory": os.getcwd()
        }
    }

def update_metrics(processed: int = 0, ai_fail: int = 0, rate_limited: int = 0, 
                   replies_sent: int = 0, last_mention_time: str = None, since_id: str = None):
    """Update global metrics."""
    if processed:
        metrics["processed"] += processed
    if ai_fail:
        metrics["ai_fail"] += ai_fail
    if rate_limited:
        metrics["rate_limited"] += rate_limited
    if replies_sent:
        metrics["replies_sent"] += replies_sent
    if last_mention_time:
        metrics["last_mention_time"] = last_mention_time
    if since_id:
        metrics["since_id"] = since_id

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=Config.PORT)




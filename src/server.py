"""
FastAPI health server for CryBB Maker Bot.
Provides health check and metrics endpoints for container orchestration.
"""
from fastapi import FastAPI
from datetime import datetime
import os
from .config import Config

app = FastAPI(title="CryBB Maker Bot", version="1.0.0")

@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "bot_handle": Config.BOT_HANDLE,
        "twitter_mode": Config.TWITTER_MODE,
        "image_pipeline": Config.IMAGE_PIPELINE
    }

@app.get("/metrics")
async def metrics():
    """Basic metrics and status endpoint."""
    return {
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=Config.PORT)




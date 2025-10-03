# app.py
"""
Main application file to initialize and run the FastAPI server.
"""
import logging
import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from huggingface_hub import snapshot_download
from huggingface_hub import hf_hub_download

from api import endpoints
from config import (
    MODEL_DIR_EN, REPO_ID_EN, 
    MODEL_DIR_FR, REPO_ID_FR,
    MODEL_DIR_ZH, REPO_ID_ZH,
    SUMMARIZER_MODEL_DIR, SUMMARIZER_REPO_ID, SUMMARIZER_FILENAME
)

# Setup basic logging
# Define a robust logging configuration DICTIONARY
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "loggers": {
        "": {  # This is the root logger
            "handlers": ["console"],
            "level": "INFO",  # Set the level to INFO to see everything
        },
        "uvicorn.error": { "level": "INFO" },
        "uvicorn.access": { "handlers": ["console"], "level": "INFO", "propagate": False },
    },
}

logger = logging.getLogger(__name__) # Keep this for app-level logging

app = FastAPI(title="Live Radio Karaoke")

@app.on_event("startup")
async def download_model_if_needed():
    """Check for and download the ASR models on startup."""
    from performance_config import PERFORMANCE_MODE, PERF_CONFIG
    
    logger.info("🚀 Starting SynchroLyrics with optimizations...")
    logger.info(f"🎯 Performance Mode: {PERFORMANCE_MODE}")
    logger.info(f"⚙️  Configuration: {PERF_CONFIG}")
    logger.info("Checking for ASR models...")
    
    # Check and download English model
    tokens_path_en = os.path.join(MODEL_DIR_EN, "tokens.txt")
    if not os.path.exists(tokens_path_en):
        logger.warning(f"English model not found in {MODEL_DIR_EN}. Downloading from Hugging Face Hub...")
        try:
            snapshot_download(repo_id=REPO_ID_EN, local_dir=MODEL_DIR_EN, local_dir_use_symlinks=False)
            logger.info("English model download complete.")
        except Exception as e:
            logger.error(f"Failed to download English model: {e}")
            raise
    else:
        logger.info("English model found locally.")
    
    # Check and download French model
    tokens_path_fr = os.path.join(MODEL_DIR_FR, "tokens.txt")
    if not os.path.exists(tokens_path_fr):
        logger.warning(f"French model not found in {MODEL_DIR_FR}. Downloading from Hugging Face Hub...")
        try:
            snapshot_download(repo_id=REPO_ID_FR, local_dir=MODEL_DIR_FR, local_dir_use_symlinks=False)
            logger.info("French model download complete.")
        except Exception as e:
            logger.error(f"Failed to download French model: {e}")
            raise
    else:
        logger.info("French model found locally.")
    
    # Check and download Mandarin model
    tokens_path_zh = os.path.join(MODEL_DIR_ZH, "tokens.txt")
    if not os.path.exists(tokens_path_zh):
        logger.warning(f"Mandarin model not found in {MODEL_DIR_ZH}. Downloading from Hugging Face Hub...")
        try:
            snapshot_download(repo_id=REPO_ID_ZH, local_dir=MODEL_DIR_ZH, local_dir_use_symlinks=False)
            logger.info("Mandarin model download complete.")
        except Exception as e:
            logger.error(f"Failed to download Mandarin model: {e}")
            raise
    else:
        logger.info("Mandarin model found locally.")

    # Check and download Summarizer model
    if not os.path.exists(SUMMARIZER_MODEL_DIR):
        logger.warning(f"Summarizer model not found at {SUMMARIZER_MODEL_DIR}. Downloading from Hugging Face Hub...")
        try:
            hf_hub_download(repo_id=SUMMARIZER_REPO_ID, filename=SUMMARIZER_FILENAME, local_dir=".", local_dir_use_symlinks=False)
            # Rename the downloaded file to the expected path
            os.rename(SUMMARIZER_FILENAME, SUMMARIZER_MODEL_DIR)
            logger.info("Summarizer model download complete.")
        except Exception as e:
            logger.error(f"Failed to download summarizer model: {e}")
            raise

# Include the API router
app.include_router(endpoints.router)

# Mount the frontend directory to serve static files (HTML, CSS, JS)
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

if __name__ == "__main__":
    # Use the defined logging config
    uvicorn.run(app, host="0.0.0.0", port=8001, log_config=LOGGING_CONFIG)
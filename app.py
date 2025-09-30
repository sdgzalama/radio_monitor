import logging
import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from huggingface_hub import snapshot_download
from huggingface_hub import hf_hub_download

from api import endpoints

from config import (
    MODEL_DIR_SW,REPO_ID_SW,
    MODEL_DIR_EN, REPO_ID_EN,
    MODEL_DIR_FR,REPO_ID_FR,
    MODEL_DIR_ZH,REPO_ID_ZH,
    SUMMARIZER_MODEL_DIR, SUMMARIZER_REPO_ID,SUMMARIZER_FILENAME
)

LOGGING_CONFIG = {

}
# app level logging 
logger = logging.getLogger(__name__)

app = FastAPI(title="Live radio monitor")

@app.on_event("startup")
# check some model if not download them 
async def download_model_if_needed():
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


        # Check and download Swahili model
    tokens_path_sw = os.path.join(MODEL_DIR_SW, "tokens.txt")
    if not os.path.exists(tokens_path_sw):
        logger.warning(f"Swahili model not found in {MODEL_DIR_SW}. Downloading from Hugging Face Hub...")
        try:
            snapshot_download(repo_id=REPO_ID_SW, local_dir=MODEL_DIR_SW, local_dir_use_symlinks=False)
            logger.info("Swahili model download complete.")
        except Exception as e:
            logger.error(f"Failed to download Swahili model: {e}")
            raise
    else:
        logger.info("Swahili model found locally.")

    
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
        

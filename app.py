import logging
import os
import uvicorn
from fastapi import FastAPi
from fastapi.staticfiles import StaticFiles
from huggingface_hub import snapshot_download
from huggingface_hub import hf_hub_download

from api import endpoints

from config import (
    MODEL_DIR_EN, REPO_ID_EN,
    MODEL_DIR_FR,REPO_ID_FR,
    MODEL_DIR_ZH,REPO_ID_ZH,
    SUMMARIZER_MODEL_DIR, SUMMARIZER_REPO_ID,SUMMARIZER_FILENAME
)
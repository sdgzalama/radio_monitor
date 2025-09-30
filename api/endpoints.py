import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import FileResponse, JSONResponse
from core.connection_manager import ConnectionManager
from core.asr_service import ASRService
from core.audio_streamer import AudioStreamer
from core.summarizer_service import SummarizerService
from config import RADIO_URLS, STATION_LANGUAGES, get_asr_language
from performance_config import PERF_CONFIG

logger = logging.getLogger(__name__)
router = APIRouter()


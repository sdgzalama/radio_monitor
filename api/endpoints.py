# api/endpoints.py (FINAL, CORRECTED, AND ROBUST VERSION)
"""
Defines the FastAPI endpoints for serving the frontend and handling WebSocket connections.
REFACTORED to manage background tasks on a per-station basis.
"""
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

manager = ConnectionManager()
# Global state refactored to be per-station
# Key: station_name, Value: dict of tasks, queues, etc.
STATION_SERVICES = {}

@router.get("/")
async def get_root():
    """Serves the main frontend HTML file."""
    return FileResponse("frontend/index.html")

@router.get("/api/stations")
async def get_stations():
    """Returns the list of available radio stations."""
    # Return stations together with their detected language map so the frontend
    # can render favorite badges without an extra request.
    try:
        return JSONResponse(content={
            "stations": RADIO_URLS,
            "languages": STATION_LANGUAGES
        })
    except Exception as e:
        logger.error(f"Failed to return stations with languages: {e}")
        # Fallback to returning just the station map
        return JSONResponse(content=RADIO_URLS)


# NOTE: `/api/stations/languages` was removed — languages are now included
# in the payload returned by `/api/stations` to reduce round-trips.

@router.get("/api/stations/discover")
async def discover_stations(
    search: str = "",
    country: str = "",
    language: str = "",
    category: str = "popular",
    limit: int = 50
):
    """
    Discover radio stations using Radio Browser API.
    
    Query parameters:
    - search: Station name search query
    - country: Country code filter (US, FR, TW, etc.)
    - language: Language filter (english, french, chinese)
    - category: Category filter (popular, news, music)
    - limit: Maximum number of results (default 50)
    """
    try:
        # Debug log incoming parameters
        logger.info(f"/api/stations/discover called with search='{search}', country='{country}', language='{language}', category='{category}', limit={limit}")
        from api.radio_browser import discover_stations
        stations = await discover_stations(
            search_query=search,
            country=country,
            language=language,
            category=category
        )
        
        # Limit results
        limited_stations = stations[:limit]
        
        return JSONResponse(content={
            "stations": limited_stations,
            "count": len(limited_stations),
            "total_found": len(stations),
            "source": "radio-browser"
        })
        
    except Exception as e:
        logger.error(f"Error discovering stations: {e}")
        return JSONResponse(
            content={
                "error": "Failed to discover stations",
                "stations": [],
                "count": 0
            },
            status_code=500
        )

@router.get("/api/stations/categories")
async def get_station_categories():
    """Get available station categories and countries."""
    return JSONResponse(content={
        "categories": [
            {"id": "popular", "name": "Most Popular", "description": "Globally popular stations"},
            {"id": "news", "name": "News & Talk", "description": "News and talk radio"},
            {"id": "music", "name": "Music", "description": "Music stations"},
            {"id": "local", "name": "Local Favorites", "description": "Curated local stations"}
        ],
        "countries": [
            {"code": "US", "name": "United States", "flag": "🇺🇸"},
            {"code": "FR", "name": "France", "flag": "🇫🇷"},
            {"code": "TW", "name": "Taiwan", "flag": "🇹🇼"},
            {"code": "GB", "name": "United Kingdom", "flag": "🇬🇧"},
            {"code": "CA", "name": "Canada", "flag": "🇨🇦"},
            {"code": "AU", "name": "Australia", "flag": "🇦🇺"},
            {"code": "DE", "name": "Germany", "flag": "🇩🇪"},
            {"code": "JP", "name": "Japan", "flag": "🇯🇵"},
            {"code": "CN", "name": "China", "flag": "🇨🇳"},
            {"code": "IT", "name": "Italy", "flag": "🇮🇹"},
            {"code": "ES", "name": "Spain", "flag": "🇪🇸"},
            {"code": "BR", "name": "Brazil", "flag": "🇧🇷"}
        ],
        "languages": [
            {"code": "en", "name": "English", "asr_support": True},
            {"code": "fr", "name": "French", "asr_support": True},
            {"code": "zh", "name": "Chinese", "asr_support": True},
            {"code": "de", "name": "German", "asr_support": False},
            {"code": "es", "name": "Spanish", "asr_support": False},
            {"code": "it", "name": "Italian", "asr_support": False}
        ]
    })

@router.get("/api/status")
async def get_status():
    """Returns the current number of connected users and performance info."""
    from performance_config import PERFORMANCE_MODE, PERF_CONFIG
    return JSONResponse(content={
        "user_count": manager.get_connection_count(),
        "performance_mode": PERFORMANCE_MODE,
        "performance_config": {
            "asr_threads": PERF_CONFIG["asr_threads"],
            "chunk_size": PERF_CONFIG["chunk_size"],
            "max_connections": PERF_CONFIG["max_connections"],
            "enable_summarizer": PERF_CONFIG["enable_summarizer"],
            "summary_threshold": PERF_CONFIG["summary_threshold"]
        }
    })

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, station: str = Query(None)):
    """Handles the WebSocket connection for a single client."""
    if not station or station not in RADIO_URLS:
        station = next(iter(RADIO_URLS.keys()))

    # STEP 1: Accept the connection here, at the beginning of the endpoint. This is the correct protocol.
    await websocket.accept()

    # STEP 2: Pass the now-active websocket to the manager to handle logic.
    is_connected = await manager.connect(websocket, station)
    if not is_connected:
        # The manager found the server was full, sent a "wait" message, and closed the connection.
        # We must stop execution here to prevent errors.
        return
    
    # --- From here on, we know the connection is valid and accepted ---

    # If this is the first client for this station, start the services
    if station not in STATION_SERVICES:
        logger.info(f"First client for '{station}'. Initializing services.")
        logger.info(f"🎯 Performance Mode: {PERF_CONFIG.get('mode', 'unknown')} | "
                       f"ASR Threads: {PERF_CONFIG['asr_threads']} | "
                       f"Chunk Size: {PERF_CONFIG['chunk_size']} | "
                       f"Summarizer: {'✅ Enabled' if PERF_CONFIG['enable_summarizer'] else '❌ Disabled'}")
        
        # Send performance mode info IMMEDIATELY after connection
        performance_payload = {
            "mode": PERF_CONFIG.get('mode', 'unknown'),
            "asr_threads": PERF_CONFIG["asr_threads"],
            "chunk_size": PERF_CONFIG["chunk_size"],
            "enable_summarizer": PERF_CONFIG["enable_summarizer"],
            "max_connections": PERF_CONFIG["max_connections"]
        }
        
        logger.info(f"🎯 DEBUG: Sending performance_info to client IMMEDIATELY: {performance_payload}")
        
        await websocket.send_json({
            "type": "performance_info",
            "payload": performance_payload
        })
            
        radio_url = RADIO_URLS[station]
        detected_language = STATION_LANGUAGES.get(station, "en")
        
        # Get ASR language and fallback info
        asr_language, is_fallback = get_asr_language(detected_language)
        
        # Send comprehensive language info to the client
        language_payload = {
            "detected_language": detected_language,
            "asr_language": asr_language,
            "is_fallback": is_fallback,
            "station": station
        }
        
        if is_fallback:
            language_payload["fallback_message"] = f"Station language '{detected_language}' not supported. Using '{asr_language}' ASR model for best approximation."
        
        await websocket.send_json({
            "type": "language", 
            "payload": language_payload
        })
        
        # Create the necessary queues for this station - Dynamic sizing based on performance mode
        pcm_queue = asyncio.Queue(maxsize=PERF_CONFIG["pcm_queue_size"])
        text_queue = asyncio.Queue(maxsize=PERF_CONFIG["text_queue_size"])
        
        # Update the global config for the ASR model
        import config
        config.CURRENT_MODEL = asr_language

        # Asynchronously initialize services that have blocking I/O
        asr_service = await ASRService.create(pcm_queue, manager, station, text_queue if PERF_CONFIG["enable_summarizer"] else None)
        
        # Only create summarizer if enabled in performance config
        if PERF_CONFIG["enable_summarizer"]:
            summarizer_service = SummarizerService(text_queue, manager, station)
            summarizer_task = asyncio.create_task(summarizer_service.run_summarization_loop())
        else:
            summarizer_task = None
            logger.info(f"Summarizer disabled for station '{station}' due to performance mode.")
        
        audio_streamer = AudioStreamer(pcm_queue, manager, radio_url, station)

        # Create and store tasks
        tasks = {
            "audio_task": asyncio.create_task(audio_streamer.run_fetching_loop()),
            "asr_task": asyncio.create_task(asr_service.run_transcription_loop()),
            "clients": 1,
        }
        
        # Add summarizer task only if enabled
        if summarizer_task:
            tasks["summarizer_task"] = summarizer_task
        
        STATION_SERVICES[station] = tasks
    else:
        logger.info(f"New client joined existing station '{station}'.")
        STATION_SERVICES[station]["clients"] += 1

    # Keep the connection alive
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from station '{station}'.")
    finally:
        await manager.disconnect(websocket)
        
        # If this was the last client for the station, shut down its services
        if station in STATION_SERVICES:
            STATION_SERVICES[station]["clients"] -= 1
            if STATION_SERVICES[station]["clients"] == 0:
                logger.info(f"Last client for '{station}' disconnected. Stopping services.")
                STATION_SERVICES[station]["audio_task"].cancel()
                STATION_SERVICES[station]["asr_task"].cancel()
                
                # Only cancel summarizer if it exists
                if "summarizer_task" in STATION_SERVICES[station]:
                    STATION_SERVICES[station]["summarizer_task"].cancel()
                
                del STATION_SERVICES[station]
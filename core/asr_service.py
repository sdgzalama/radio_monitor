# core/asr_service.py (FINAL VERSION)
"""
Handles the real-time speech-to-text transcription using sherpa-onnx.
"""
import asyncio
import logging
from typing import Tuple
import numpy as np
import sherpa_onnx
from config import get_asr_config, SAMPLE_RATE, CURRENT_MODEL
from core.connection_manager import ConnectionManager
from functools import partial

# Import OpenCC for Chinese conversion
try:
    import opencc
    s2tw_converter = opencc.OpenCC('s2twp')
    OPENCC_AVAILABLE = True
    logging.info("OpenCC loaded successfully")
except ImportError:
    OPENCC_AVAILABLE = False
    logging.warning("OpenCC not available. Chinese text will not be converted to Traditional Chinese.")

logger = logging.getLogger(__name__)

class ASRService:
    """Manages the ASR model and transcription process."""

    def __init__(self, pcm_queue: asyncio.Queue, manager: ConnectionManager, station_name: str, text_queue: asyncio.Queue | None = None):
        self.pcm_queue = pcm_queue
        self.manager = manager
        self.station_name = station_name
        self.current_model = CURRENT_MODEL
        self.text_queue = text_queue
        self.recognizer = None
        self.stream = None
        self._utterance_counter = 0 # NEW: Counter for unique utterance IDs
        logger.info(f"ASR Service initialized for {self.current_model} model. Recognizer will be created asynchronously.")

    @classmethod
    async def create(cls, pcm_queue: asyncio.Queue, manager: ConnectionManager, station_name: str, text_queue: asyncio.Queue | None = None):
        """Creates and asynchronously initializes an ASRService instance."""
        service = cls(pcm_queue, manager, station_name, text_queue)
        loop = asyncio.get_running_loop()
        asr_config = get_asr_config()
        logger.info("Loading ASR model... This may take a moment.")
        recognizer_func = partial(sherpa_onnx.OnlineRecognizer.from_transducer, **asr_config)
        service.recognizer = await loop.run_in_executor(None, recognizer_func)
        service.stream = service.recognizer.create_stream()
        logger.info("ASR Recognizer created and stream opened successfully.")
        return service

    def _convert_chinese_text(self, text: str) -> str:
        """Convert Simplified Chinese to Traditional Chinese (Taiwan variant) if needed."""
        if self.current_model == "zh" and OPENCC_AVAILABLE and text.strip():
            try:
                converted = s2tw_converter.convert(text)
                logger.debug(f"Converted '{text}' to '{converted}'")
                return converted
            except Exception as e:
                logger.warning(f"Failed to convert Chinese text '{text}': {e}")
                return text
        return text

    def _process_chunk(self, pcm_chunk: bytes) -> dict | None:
        """Processes a single PCM chunk with the ASR recognizer."""
        samples = np.frombuffer(pcm_chunk, dtype=np.int16)
        samples_float = samples.astype(np.float32) / 32768.0
        self.stream.accept_waveform(SAMPLE_RATE, samples_float)

        while self.recognizer.is_ready(self.stream):
            self.recognizer.decode_stream(self.stream)

        result = self.recognizer.get_result_all(self.stream)
        is_final = self.recognizer.is_endpoint(self.stream)

        if result.text.strip():
            original_text = result.text.strip()
            final_tokens = result.tokens
            converted_text = original_text

            if self.current_model == "zh":
                converted_text = self._convert_chinese_text(original_text)
                final_tokens = list(converted_text.replace(" ", " "))
            
            response = {
                "text": converted_text,
                "tokens": final_tokens,
                "timestamps": result.timestamps,
                "start_time": result.start_time,
                "is_final": is_final
            }

            if is_final:
                self.recognizer.reset(self.stream)
                if self.text_queue and converted_text:
                    try:
                        self._utterance_counter += 1
                        utterance_id = self._utterance_counter
                        response["utterance_id"] = utterance_id
                        self.text_queue.put_nowait((converted_text, utterance_id))
                    except asyncio.QueueFull:
                        logger.warning("Summarizer text queue is full. Dropping transcript.")
            return response
        return None

    async def run_transcription_loop(self):
        """The main loop for receiving PCM data and performing transcription."""
        logger.info("🎤 ASR transcription task started.")
        loop = asyncio.get_running_loop()
        current_utterance_abs_start_time = None

        try:
            while True:
                from config import CURRENT_MODEL
                if CURRENT_MODEL != self.current_model:
                    logger.info(f"Switching ASR model from {self.current_model} to {CURRENT_MODEL}")
                    del self.stream
                    del self.recognizer
                    
                    asr_config = get_asr_config()
                    self.recognizer = sherpa_onnx.OnlineRecognizer.from_transducer(**asr_config)
                    self.stream = self.recognizer.create_stream()
                    self.current_model = CURRENT_MODEL
                    logger.info(f"ASR model switched to {self.current_model}")

                pcm_chunk, chunk_start_time = await self.pcm_queue.get()

                if current_utterance_abs_start_time is None:
                    current_utterance_abs_start_time = chunk_start_time

                result = await loop.run_in_executor(None, self._process_chunk, pcm_chunk)

                if result:
                    result["absolute_start_time"] = current_utterance_abs_start_time
                    self.manager.broadcast_to_station(self.station_name, {"type": "asr", "payload": result})
                    if result["is_final"]:
                        current_utterance_abs_start_time = None

                self.pcm_queue.task_done()
        except asyncio.CancelledError:
            logger.info("🎤 ASR transcription task cancelled.")
        except Exception as e:
            logger.error(f"💥 ASR task failed: {e}", exc_info=True)
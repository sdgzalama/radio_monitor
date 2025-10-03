# core/summarizer_service.py (FINAL VERSION)
"""
Handles background text summarization using a GGUF model with llama-cpp-python.
"""
import asyncio
import logging
from datetime import datetime, timezone
from llama_cpp import Llama
from config import SUMMARIZER_MODEL_DIR
from core.connection_manager import ConnectionManager
from performance_config import PERF_CONFIG
import os

logger = logging.getLogger(__name__)

# --- Tunable Parameters - Dynamic based on performance mode ---
SUMMARY_TRIGGER_THRESHOLD = PERF_CONFIG["summary_threshold"]
MAX_INPUT_CHARS = PERF_CONFIG["llm_context_size"]
CONTEXT_KEEPALIVE_CHARS = min(100, MAX_INPUT_CHARS // 20)  # Dynamic based on context size

class SummarizerService:
    """
    Manages text aggregation and periodic summarization for a single station.
    """

    def __init__(self, text_queue: asyncio.Queue, manager: ConnectionManager, station_name: str):
        self.text_queue = text_queue
        self.manager = manager
        self.station_name = station_name
        self.transcript_buffer = ""
        self.utterance_id_buffer = [] # Buffer for utterance IDs
        self.llm = None
        self.summarization_in_progress = False

    def _load_model(self):
        """Loads the Llama.cpp model. This is a blocking operation."""
        logger.info("Loading summarizer model... This may take a moment.")
        try:
            self.llm = Llama(
                model_path=SUMMARIZER_MODEL_DIR,
                n_ctx=MAX_INPUT_CHARS,
                n_gpu_layers=0,
                verbose=False,
                n_threads=PERF_CONFIG["llm_threads"],
                repeat_penalty=1.1,  # Slightly reduced from 1.2
                n_batch=64,  # Added for optimization
                low_vram=True,  # Added to save memory
            )
            logger.info("Summarizer model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load summarizer model: {e}", exc_info=True)
            self.llm = None

    def _generate_summary(self, text_to_summarize: str) -> str:
        """
        Generates a summary from the given text. This is a blocking, CPU-intensive operation.
        """
        if not self.llm:
            return "Summarizer model is not available."
        messages = [
            {"role": "system", "content": "You are a broadcast summarizer. Your task is to provide a brief, neutral, and concise summary of the live radio transcript. Capture the main points. Do not add any preamble like 'Here is a summary'."},
            {"role": "user", "content": f"Please summarize the following transcript:\n\n---\n{text_to_summarize}\n---"}
        ]
        try:
            output = self.llm.create_chat_completion(messages=messages, max_tokens=400)
            summary = output['choices'][0]['message']['content'].strip()
            return summary
        except Exception as e:
            logger.error(f"Error during summary generation: {e}")
            return "Error generating summary."

    async def run_summarization_loop(self):
        """
        Main loop to listen for new text and trigger summarization.
        """
        loop = asyncio.get_running_loop()
        self.manager.broadcast_to_station(self.station_name, {"type": "summary_state", "payload": {"status": "loading"}})
        await loop.run_in_executor(None, self._load_model)
        
        if not self.llm:
            logger.error("Cannot start summarization loop; model failed to load.")
            self.manager.broadcast_to_station(self.station_name, {"type": "summary_state", "payload": {"status": "error", "message": "Model failed to load."}})
            return
 
        self.manager.broadcast_to_station(self.station_name, {"type": "summary_state", "payload": {"status": "ready"}})
        logger.info(f"🎤 Summarizer task started for station: {self.station_name}")

        while True:
            try:
                new_text, utterance_id = await self.text_queue.get()
                self.transcript_buffer += f" {new_text}"
                self.utterance_id_buffer.append(utterance_id)
                
                logger.debug(f"[{self.station_name}] Transcript buffer is now {len(self.transcript_buffer)} chars.")

                if len(self.transcript_buffer) > SUMMARY_TRIGGER_THRESHOLD and not self.summarization_in_progress:
                    self.summarization_in_progress = True
                    
                    text_snapshot = self.transcript_buffer[-MAX_INPUT_CHARS:]
                    source_ids_snapshot = self.utterance_id_buffer[:]
                    
                    logger.info(f"Triggering summary for {self.station_name} with {len(text_snapshot)} chars.")
                    self.manager.broadcast_to_station(self.station_name, {"type": "summary_state", "payload": {"status": "summarizing"}})

                    summary = await loop.run_in_executor(None, self._generate_summary, text_snapshot)
                    
                    logger.info(f"Generated summary for {self.station_name}: {summary}")
                    
                    timestamp_utc = datetime.now(timezone.utc).isoformat()

                    self.manager.broadcast_to_station(self.station_name, {
                        "type": "summary",
                        "payload": {
                            "summary": summary, 
                            "station": self.station_name,
                            "timestamp": timestamp_utc,
                            "source_utterance_ids": source_ids_snapshot
                        }
                    })

                    self.transcript_buffer = self.transcript_buffer[-CONTEXT_KEEPALIVE_CHARS:]
                    keep_ratio = CONTEXT_KEEPALIVE_CHARS / len(text_snapshot) if text_snapshot else 0
                    num_ids_to_keep = int(len(source_ids_snapshot) * keep_ratio)
                    self.utterance_id_buffer = self.utterance_id_buffer[-num_ids_to_keep:]
                    
                    self.manager.broadcast_to_station(self.station_name, {"type": "summary_state", "payload": {"status": "ready"}})
                    self.summarization_in_progress = False
                else:
                    logger.debug(f"[{self.station_name}] Not enough text to summarize or summarization already in progress.")

                self.text_queue.task_done()
            except asyncio.CancelledError:
                logger.info(f"🎤 Summarizer task for {self.station_name} cancelled.")
                break
            except Exception as e:
                logger.error(f"💥 Summarizer task for {self.station_name} failed: {e}", exc_info=True)
                self.summarization_in_progress = False
                await asyncio.sleep(5)
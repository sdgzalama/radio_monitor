# core/audio_streamer.py
"""
Fetches the live radio stream, transcodes it with FFmpeg, and distributes it.
ENHANCED WITH DETAILED DEBUGGING AND EXPLICIT TIMEOUTS.
"""
import asyncio
import logging
import aiohttp
import ssl
from config import CHUNK_SIZE, SAMPLE_RATE, BYTES_PER_SAMPLE
from core.connection_manager import ConnectionManager

logger = logging.getLogger("audio_streamer")
QUEUE_PUT_TIMEOUT = 5.0

class AudioStreamer:
    def __init__(self, pcm_queue: asyncio.Queue, manager: ConnectionManager, radio_url: str, station_name: str):
        self.pcm_queue = pcm_queue
        self.manager = manager
        self.radio_url = radio_url
        self.station_name = station_name
        self._pcm_reader_task: asyncio.Task | None = None
        logger.info(f"Audio Streamer initialized for station: {radio_url}")

    async def _pcm_reader_loop(self, proc: asyncio.subprocess.Process):
        """Reads PCM data from FFmpeg's stdout and queues it for ASR."""
        logger.info("[PCM_READER] Reader started for PID %s", proc.pid)
        logger.info(f"[PCM_READER] Task started. Reading from FFmpeg PID {proc.pid} stdout.")
        server_stream_time = 0.0
        try:
            while True:
                logger.debug(f"[PCM_READER] Awaiting proc.stdout.read({CHUNK_SIZE})...")
                pcm_chunk = await proc.stdout.read(CHUNK_SIZE)
                
                if len(pcm_chunk) == 0:
                    logger.warning("[PCM_READER] Reached end of FFmpeg stream (read 0 bytes). Exiting loop.")
                    break
                
                # logger.info(f"[PCM_READER] Read {len(pcm_chunk)} bytes of PCM data from FFmpeg.")

                chunk_duration = len(pcm_chunk) / (SAMPLE_RATE * BYTES_PER_SAMPLE)
                
                try:
                    q_size = self.pcm_queue.qsize()
                    logger.debug(f"[PCM_READER] PCM queue size is {q_size}/{self.pcm_queue.maxsize} before put.")
                    
                    await asyncio.wait_for(
                        self.pcm_queue.put((pcm_chunk, server_stream_time)),
                        timeout=QUEUE_PUT_TIMEOUT
                    )
                    
                    logger.debug(f"[PCM_READER] Successfully queued chunk for ASR at stream time {server_stream_time:.2f}s.")
                except asyncio.TimeoutError:
                    logger.error(
                        f"[PCM_READER] DEADLOCK ALERT: Failed to put PCM chunk into ASR queue within {QUEUE_PUT_TIMEOUT}s. "
                        "The ASR service may be stuck. Clearing queue to prevent total stall."
                    )
                    while not self.pcm_queue.empty():
                        self.pcm_queue.get_nowait()
                except Exception as q_err:
                    logger.error(f"[PCM_READER] Error putting to queue: {q_err}", exc_info=True)
                    break

                server_stream_time += chunk_duration

        except asyncio.CancelledError:
            logger.info("[PCM_READER] Task cancelled.")
        except Exception as e:
            logger.error(f"[PCM_READER] 💥 Task failed unexpectedly: {e}", exc_info=True)
        finally:
            logger.warning("[PCM_READER] Task finished.")
            logger.warning("[PCM_READER] Reader exited for PID %s", proc.pid)

    async def run_fetching_loop(self):
        """The main loop for fetching and processing the radio stream."""
        logger.info("[FETCHER] Main fetcher task started.")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        loop = asyncio.get_running_loop()
        
        # Create SSL context with relaxed verification for problematic streams
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Define timeout for the connection
        timeout = aiohttp.ClientTimeout(total=None, connect=30, sock_read=None, sock_connect=30)
        
        # Track consecutive failures to implement exponential backoff
        consecutive_failures = 0
        max_consecutive_failures = 5

        while True:
            proc = None
            try:
                logger.info(f"[FETCHER] Attempting to connect to radio stream: {self.radio_url}")
                
                # Try with SSL first (for HTTPS streams)
                connector = aiohttp.TCPConnector(
                    ssl=ssl_context,
                    limit=100,
                    limit_per_host=30,
                    ttl_dns_cache=300,
                    use_dns_cache=False,
                )
                
                async with aiohttp.ClientSession(
                    timeout=timeout, 
                    connector=connector,
                    headers=headers
                ) as session:
                    async with session.get(self.radio_url) as response:
                        if response.status != 200:
                            raise aiohttp.ClientError(f"Radio stream returned status: {response.status}")

                        logger.info("✅ [FETCHER] Successfully connected to radio stream.")
                        content_type = response.headers.get('Content-Type', '').lower()
                        mime = 'audio/mpeg'
                        if 'aac' in content_type:
                            mime = 'audio/aac'
                        elif 'ogg' in content_type:
                            mime = 'audio/ogg'
                        logger.info(f"[FETCHER] Determined client MIME type: {mime}")
                        self.manager.broadcast_to_station(self.station_name, {"type": "config", "payload": {"mime": mime}})

                        proc = await asyncio.create_subprocess_exec(
                            'ffmpeg', '-i', 'pipe:0', '-f', 's16le', '-ar', str(SAMPLE_RATE),
                            '-ac', '1', '-loglevel', 'warning', 'pipe:1',
                            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL, 
                        )

                        logger.info("[FETCHER] Started FFmpeg process. PID: %s", proc.pid)

                        # cancel old reader (if any) *before* spawning the new one
                        if self._pcm_reader_task and not self._pcm_reader_task.done():
                            self._pcm_reader_task.cancel()
                            try:
                                await asyncio.wait_for(self._pcm_reader_task, timeout=2.0)
                            except asyncio.TimeoutError:
                                logger.warning("[FETCHER] PCM reader task did not cancel in time.")

                        # now spawn reader for the *new* process
                        logger.info("[FETCHER] Spawning reader for PID %s", proc.pid)
                        self._pcm_reader_task = asyncio.create_task(self._pcm_reader_loop(proc))

                        chunk_count = 0
                        async for chunk in response.content.iter_chunked(CHUNK_SIZE):
                            chunk_count += 1
                            # logger.info(f"[FETCHER] Received chunk #{chunk_count} ({len(chunk)} bytes) from radio stream.")
                            
                            self.manager.broadcast_to_station(self.station_name, chunk)
                            logger.debug(f"[FETCHER] Broadcasted {len(chunk)} raw bytes to clients.")
                            
                            try:
                                logger.debug(f"[FETCHER] Writing {len(chunk)} bytes to FFmpeg stdin...")
                                await loop.run_in_executor(None, proc.stdin.write, chunk)
                                await proc.stdin.drain()
                                logger.debug("[FETCHER] FFmpeg stdin drained successfully.")
                            except (BrokenPipeError, ConnectionResetError) as pipe_err:
                                logger.warning(f"[FETCHER] FFmpeg process closed stdin pipe unexpectedly: {pipe_err}. Ending stream processing.")
                                break
                        
                        logger.warning("[FETCHER] Radio stream chunk iteration ended. Closing FFmpeg stdin.")
                        if proc.stdin and not proc.stdin.is_closing():
                            proc.stdin.close()
                        
                        logger.info("[FETCHER] Waiting for PCM reader task to complete...")
                        await self._pcm_reader_task
                        logger.info("[FETCHER] PCM reader task has completed.")
                
                # Reset failure counter on successful connection
                consecutive_failures = 0
                
            except aiohttp.ClientConnectorError as conn_err:
                consecutive_failures += 1
                error_msg = str(conn_err)
                logger.error(f"[FETCHER] Connection error: {error_msg}")
                
                # Check if it's a connection refused error
                if "Connect call failed" in error_msg or "Connection refused" in error_msg:
                    logger.warning(f"[FETCHER] Connection refused for {self.radio_url}. This may indicate the stream is offline or the URL is incorrect.")
                elif "Name or service not known" in error_msg:
                    logger.warning(f"[FETCHER] DNS resolution failed for {self.radio_url}. Check the URL or network connectivity.")
                
                # Implement exponential backoff
                backoff_time = min(5 * (2 ** consecutive_failures), 60)  # Max 60 seconds
                logger.info(f"[FETCHER] Consecutive failures: {consecutive_failures}. Backing off for {backoff_time} seconds...")
                
                if consecutive_failures >= max_consecutive_failures:
                    logger.error(f"[FETCHER] Too many consecutive failures ({consecutive_failures}). Consider checking the stream URL.")
                    # Send error message to clients
                    self.manager.broadcast_to_station(self.station_name, {
                        "type": "error", 
                        "payload": {
                            "message": f"Unable to connect to stream after {consecutive_failures} attempts. The stream may be offline."
                        }
                    })
                await asyncio.sleep(backoff_time)
            except ssl.SSLError as ssl_err:
                logger.warning(f"[FETCHER] SSL error occurred: {ssl_err}. Trying without SSL verification...")
                # Retry with completely disabled SSL verification
                try:
                    connector = aiohttp.TCPConnector(ssl=False)
                    async with aiohttp.ClientSession(timeout=timeout, connector=connector, headers=headers) as session:
                        async with session.get(self.radio_url) as response:
                            if response.status != 200:
                                raise aiohttp.ClientError(f"Radio stream returned status: {response.status}")
                            
                            logger.info("✅ [FETCHER] Successfully connected to radio stream (SSL disabled).")
                            content_type = response.headers.get('Content-Type', '').lower()
                            mime = 'audio/mpeg'
                            if 'aac' in content_type:
                                mime = 'audio/aac'
                            elif 'ogg' in content_type:
                                mime = 'audio/ogg'
                            logger.info(f"[FETCHER] Determined client MIME type: {mime}")
                            self.manager.broadcast_to_station(self.station_name, {"type": "config", "payload": {"mime": mime}})

                            proc = await asyncio.create_subprocess_exec(
                                'ffmpeg', '-i', 'pipe:0', '-f', 's16le', '-ar', str(SAMPLE_RATE),
                                '-ac', '1', '-loglevel', 'warning', 'pipe:1',
                                stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL, 
                            )

                            logger.info("[FETCHER] Started FFmpeg process. PID: %s", proc.pid)

                            # cancel old reader (if any) *before* spawning the new one
                            if self._pcm_reader_task and not self._pcm_reader_task.done():
                                self._pcm_reader_task.cancel()
                                try:
                                    await asyncio.wait_for(self._pcm_reader_task, timeout=2.0)
                                except (asyncio.TimeoutError, aiohttp.ServerTimeoutError):
                                    logger.warning("[FETCHER] PCM reader task did not cancel in time.")

                            # now spawn reader for the *new* process
                            logger.info("[FETCHER] Spawning reader for PID %s", proc.pid)
                            self._pcm_reader_task = asyncio.create_task(self._pcm_reader_loop(proc))

                            chunk_count = 0
                            async for chunk in response.content.iter_chunked(CHUNK_SIZE):
                                chunk_count += 1
                                # logger.info(f"[FETCHER] Received chunk #{chunk_count} ({len(chunk)} bytes) from radio stream.")
                                
                                self.manager.broadcast_to_station(self.station_name, chunk)
                                logger.debug(f"[FETCHER] Broadcasted {len(chunk)} raw bytes to clients.")
                                
                                try:
                                    logger.debug(f"[FETCHER] Writing {len(chunk)} bytes to FFmpeg stdin...")
                                    await loop.run_in_executor(None, proc.stdin.write, chunk)
                                    await proc.stdin.drain()
                                    logger.debug("[FETCHER] FFmpeg stdin drained successfully.")
                                except (BrokenPipeError, ConnectionResetError) as pipe_err:
                                    logger.warning(f"[FETCHER] FFmpeg process closed stdin pipe unexpectedly: {pipe_err}. Ending stream processing.")
                                    break
                            
                            logger.warning("[FETCHER] Radio stream chunk iteration ended. Closing FFmpeg stdin.")
                            if proc.stdin and not proc.stdin.is_closing():
                                proc.stdin.close()
                            
                            logger.info("[FETCHER] Waiting for PCM reader task to complete...")
                            await self._pcm_reader_task
                            logger.info("[FETCHER] PCM reader task has completed.")
                            
                    # Reset failure counter on successful connection
                    consecutive_failures = 0
                except Exception as retry_err:
                    consecutive_failures += 1
                    logger.error(f"[FETCHER] Retry with disabled SSL also failed: {retry_err}")
                    
            except asyncio.TimeoutError:
                consecutive_failures += 1
                logger.warning("[FETCHER] Connection to radio stream timed out.")
                await asyncio.sleep(5) # Wait before reconnecting on timeout
                
            except aiohttp.ClientError as client_err:
                consecutive_failures += 1
                logger.error(f"[FETCHER] Client error: {client_err}")
                
            except asyncio.CancelledError:
                logger.info("[FETCHER] Main fetcher task cancelled.")
                break
                
            except Exception as e:
                consecutive_failures += 1
                logger.error(f"[FETCHER] 💥 Fetcher loop failed: {e}. Reconnecting...", exc_info=True)
                
            finally:
                logger.warning("[FETCHER] Cleaning up current session...")
                if self._pcm_reader_task and not self._pcm_reader_task.done():
                    self._pcm_reader_task.cancel()
                if proc and proc.returncode is None:
                    logger.info(f"[FETCHER] Terminating FFmpeg process PID: {proc.pid}")
                    proc.terminate()
                    await proc.wait()
                    logger.info(f"[FETCHER] FFmpeg process PID: {proc.pid} terminated.")
                
                # Calculate backoff time based on consecutive failures
                if consecutive_failures > 0:
                    backoff_time = min(5 * (2 ** (consecutive_failures - 1)), 60)
                else:
                    backoff_time = 5
                    
                logger.info(f"[FETCHER] Cleanup complete. Waiting {backoff_time} seconds before next action.")
                await asyncio.sleep(backoff_time)
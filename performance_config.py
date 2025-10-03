# performance_config.py
"""
Performance configuration for optimizing SynchroLyrics on resource-constrained environments.
"""
import os

# Performance mode: "normal" | "low_resource" | "ultra_low"
PERFORMANCE_MODE = os.getenv("PERFORMANCE_MODE", "low_resource")

def get_performance_config():
    """Returns performance configuration based on the current mode."""
    
    if PERFORMANCE_MODE == "ultra_low":
        return {
            "mode": "ultra_low",
            "asr_threads": 1,
            "summary_threshold": 10000,  # Very high threshold
            "max_connections": 1,
            "chunk_size": 1600,  # Very small chunks
            "enable_summarizer": False,  # Disable completely
            "pcm_queue_size": 25,
            "text_queue_size": 50,
            "llm_context_size": 1024,
            "llm_threads": 1,
        }
    elif PERFORMANCE_MODE == "low_resource":
        return {
            "mode": "low_resource",
            "asr_threads": 1,
            "summary_threshold": 5000,
            "max_connections": 1,
            "chunk_size": 3200,
            "enable_summarizer": True,
            "pcm_queue_size": 50,
            "text_queue_size": 100,
            "llm_context_size": 2048,
            "llm_threads": 1,
        }
    else:  # normal mode
        return {
            "mode": "normal",
            "asr_threads": 2,
            "summary_threshold": 2000,
            "max_connections": 2,
            "chunk_size": 6400,
            "enable_summarizer": True,
            "pcm_queue_size": 100,
            "text_queue_size": 200,
            "llm_context_size": 4096,
            "llm_threads": 2,
        }

# Get current config
PERF_CONFIG = get_performance_config()
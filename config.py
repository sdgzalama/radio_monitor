# config.py
"""
Centralized configuration for Live Radio Karaoke (English + Swahili)
"""
import os
from performance_config import PERF_CONFIG

# -----------------------------
# ASR Model Configuration
# -----------------------------
# English ASR model (existing)
MODEL_DIR_EN = "./sherpa-onnx-streaming-zipformer-en-20M-2023-02-17"
REPO_ID_EN = "csukuangfj/sherpa-onnx-streaming-zipformer-en-20M-2023-02-17"

# Swahili ASR model (placeholder - replace with actual model path)
MODEL_DIR_SW = "./sherpa-onnx-streaming-zipformer-sw-2025-10-02"
REPO_ID_SW = "your-hf-username/sherpa-onnx-streaming-zipformer-sw-2025-10-02"

# Summarizer model (optional)
SUMMARIZER_MODEL_DIR = "./google_gemma-3-1b-it-qat-Q4_0.gguf"
SUMMARIZER_REPO_ID = "bartowski/google_gemma-3-1b-it-qat-GGUF"
SUMMARIZER_FILENAME = "google_gemma-3-1b-it-qat-Q4_0.gguf"

# Current model in use (default to English)
CURRENT_MODEL = "en"
MODEL_DIRS = {
    "en": MODEL_DIR_EN,
    "sw": MODEL_DIR_SW
}
REPO_IDS = {
    "en": REPO_ID_EN,
    "sw": REPO_ID_SW
}

# -----------------------------
# Radio Station Configuration
# -----------------------------
RADIO_URLS = {
    ## English
    "KEXP (Seattle, 64 kbps)": "https://kexp.streamguys1.com/kexp64.aac",
    "NPR": "https://npr-ice.streamguys1.com/live.mp3",

    ## Swahili
    "Radio Citizen (Kenya)": "https://stream-158.zeno.fm/xv5375hfkbruv?zt=eyJhbGciOiJIUzI1NiJ9.eyJzdHJlYW0iOiJ4djUzNzVoZmticnV2IiwiaG9zdCI6InN0cmVhbS0xNTguemVuby5mbSIsInJ0dGwiOjUsImp0aSI6InJhR2J0eGJoUlMtaUNYRnNySUZHQ3ciLCJpYXQiOjE3NTk0MDYwOTIsImV4cCI6MTc1OTQwNjE1Mn0.UghvdVaYrQKCj_Ruo_ob9WSyN1qHgTY3mjOZwA4s2qs",
    "BBC Swahili": "https://bbcmedia.ic.llnwd.net/stream/bbcmedia_sw1_mf_p"
}

# Map stations to languages
STATION_LANGUAGES = {
    "KEXP (Seattle, 64 kbps)": "en",
    "NPR": "en",
    "Radio Citizen (Kenya)": "sw",
    "BBC Swahili": "sw"
}

# Supported ASR languages
SUPPORTED_ASR_LANGUAGES = {"en", "sw"}

# -----------------------------
# ASR Language Helpers
# -----------------------------
def get_asr_language(detected_language: str) -> str:
    """
    Returns ASR language for detected language.
    Defaults to English if unsupported.
    """
    return detected_language if detected_language in SUPPORTED_ASR_LANGUAGES else "en"

def detect_station_language(station_name: str) -> str:
    """
    Returns the language code for a given station.
    Defaults to English.
    """
    return STATION_LANGUAGES.get(station_name, "en")

# -----------------------------
# Default station
# -----------------------------
DEFAULT_RADIO_URL = RADIO_URLS["NPR"]

# -----------------------------
# Audio Processing
# -----------------------------
CHUNK_SIZE = PERF_CONFIG["chunk_size"]
SAMPLE_RATE = 16000
BYTES_PER_SAMPLE = 2  # 16-bit PCM

# -----------------------------
# ASR Model Config Loader
# -----------------------------
def get_current_model_dir():
    """Returns the current model directory based on CURRENT_MODEL setting."""
    return MODEL_DIRS.get(CURRENT_MODEL, MODEL_DIR_EN)

def get_current_repo_id():
    """Returns the current repo ID based on CURRENT_MODEL setting."""
    return REPO_IDS.get(CURRENT_MODEL, REPO_ID_EN)

def get_asr_config() -> dict:
    """
    Returns configuration for the sherpa-onnx ASR model.
    Checks for required model files.
    """
    model_dir = get_current_model_dir()
    
    if not os.path.exists(os.path.join(model_dir, "tokens.txt")):
        raise FileNotFoundError(
            f"ASR model not found in {model_dir}. "
            "Please ensure the model path is correct."
        )

    # Helper to find existing model files
    def find_model_file(names):
        for name in names:
            path = os.path.join(model_dir, name)
            if os.path.exists(path):
                return path
        return None

    encoder_path = find_model_file(["encoder.onnx", "encoder.int8.onnx"])
    decoder_path = find_model_file(["decoder.onnx"])
    joiner_path = find_model_file(["joiner.onnx", "joiner.int8.onnx"])

    if not encoder_path or not decoder_path or not joiner_path:
        raise FileNotFoundError(
            f"Required model files not found in {model_dir}. "
            f"Found: encoder={encoder_path}, decoder={decoder_path}, joiner={joiner_path}"
        )

    return {
        "tokens": os.path.join(model_dir, "tokens.txt"),
        "encoder": encoder_path,
        "decoder": decoder_path,
        "joiner": joiner_path,
        "enable_endpoint_detection": True,
        "num_threads": PERF_CONFIG["asr_threads"],
        "rule3_min_utterance_length": 500,
    }

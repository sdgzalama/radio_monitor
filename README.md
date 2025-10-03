---
title: Live Radio Karaoke with ASR Transcription
emoji: 📻
colorFrom: blue
colorTo: red
sdk: docker
pinned: false
license: apache-2.0
short_description: SynchroLyrics
---

# Live Radio Karaoke

[![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4% hugging%20face-Spaces-blue)](https://huggingface.co/spaces) <!-- Replace with your actual space link -->

Live Radio Karaoke is a real-time, multilingual speech-to-text application that transcribes live radio streams and presents the text with karaoke-style word highlighting. Built with FastAPI, WebSockets, and the high-performance `sherpa-onnx` ASR engine, it provides a seamless and engaging "karaoke" experience for spoken word content from radio stations around the world.

This application is designed for and optimized to run on **Hugging Face Spaces**.

***

## Key Features

*   **Real-Time Transcription**: Audio from live radio is processed and transcribed with minimal latency.
*   **Multilingual Support**: Seamlessly switches between different Automatic Speech Recognition (ASR) models to support English, French, and Mandarin Chinese stations.
*   **Karaoke-Style Highlighting**: Transcribed words are highlighted in sync with the live audio, providing an intuitive and engaging user experience.
*   **Dynamic Model Switching**: The backend automatically loads the correct ASR model based on the language of the selected radio station, without restarting the application.
*   **Broad Station Selection**: Comes pre-configured with a diverse list of radio stations for all supported languages.
*   **Efficient Backend**: Built on an asynchronous Python stack (FastAPI, Uvicorn, aiohttp) for high performance and concurrency.
*   **Optimized ASR Engine**: Utilizes `sherpa-onnx` for fast, lightweight, and streaming-capable speech recognition.
*   **Modern Frontend**: A clean, responsive, and user-friendly interface built with vanilla JavaScript, HTML, and CSS, featuring a dynamic background and station selection modal.
*   **Containerized Deployment**: A complete `Dockerfile` is provided for easy, reproducible deployment on services like Hugging Face Spaces.

## How It Works (Architecture)

The application follows a sophisticated streaming architecture to achieve low-latency transcription and audio playback.

1.  **Client Connection**: The user selects a station and clicks "Play". The frontend establishes a WebSocket connection to the FastAPI backend.
2.  **Backend Initialization**: Upon the first user connecting to a specific station, the backend spins up two primary background tasks:
    *   **`AudioStreamer`**: Connects to the selected radio station's URL.
    *   **`ASRService`**: Loads the appropriate `sherpa-onnx` model for the station's language (e.g., French model for "France Inter").
3.  **Audio Ingestion & Processing**:
    *   The `AudioStreamer` fetches the audio stream (e.g., MP3, AAC) in chunks.
    *   **Dual Audio Path**: Each raw audio chunk is immediately sent down two parallel paths:
        *   **Path A (Playback)**: The chunk is broadcast directly over the WebSocket to all connected clients. The frontend uses the Media Source Extensions API to append these raw chunks into an audio buffer for seamless playback.
        *   **Path B (Transcription)**: The same chunk is piped into a local `ffmpeg` subprocess.
4.  **Transcoding**: The `ffmpeg` process transcodes the audio on-the-fly into the format required by the ASR model: raw 16-bit PCM, 16kHz sample rate, single channel (mono).
5.  **Speech-to-Text**:
    *   The raw PCM audio data from `ffmpeg` is placed into an asynchronous queue.
    *   The `ASRService` retrieves the PCM data from the queue and feeds it into the `sherpa-onnx` streaming recognizer.
    *   The ASR engine outputs transcription results, including the text, individual tokens, and timestamps for each word.
6.  **Broadcast and Render**:
    *   The transcription results (JSON payloads) are broadcast over the WebSocket to all clients.
    *   The frontend JavaScript receives these payloads, renders the text, and starts a `requestAnimationFrame` loop. This loop continuously compares the audio player's current time with the word timestamps to apply the "karaoke" highlight to the correct word.

## Project Structure

```
.
├── api
│   └── endpoints.py      # FastAPI WebSocket and API endpoint definitions.
├── core
│   ├── asr_service.py        # Manages the sherpa-onnx model and transcription loop.
│   ├── audio_streamer.py     # Fetches, transcodes (via ffmpeg), and queues radio audio.
│   └── connection_manager.py # Handles WebSocket connections and broadcasting.
├── frontend
│   ├── css
│   │   └── style.css       # Main stylesheet for the application.
│   ├── js
│   │   └── main.js         # Core frontend logic, WebSocket handling, and rendering.
│   └── index.html          # The single-page HTML structure.
├── app.py                  # Main FastAPI application; handles model downloads on startup.
├── config.py               # Central configuration for models, stations, and audio settings.
├── Dockerfile              # Instructions for building the production Docker image.
└── requirements.txt        # Python dependencies.
```

## Running Locally

### Prerequisites

*   Python 3.11+
*   `ffmpeg` installed and available in your system's PATH.
*   An internet connection (for downloading models on the first run).

### Instructions

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd live-radio-karaoke
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the required Python packages:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application:**
    ```bash
    uvicorn app:app --host 0.0.0.0 --port 7860
    ```

5.  **Open your browser** and navigate to `http://localhost:7860`.

> **Note:** The first time you run the application, it will download the ASR models for English, French, and Mandarin from the Hugging Face Hub. This may take some time and requires a stable internet connection. Subsequent startups will be much faster as the models will be cached locally.

## Running with Docker

The easiest way to run the application with a consistent environment is by using Docker.

1.  **Build the Docker image:**
    ```bash
    docker build -t live-radio-karaoke .
    ```

2.  **Run the Docker container:**
    ```bash
    docker run -p 7860:7860 live-radio-karaoke
    ```

3.  **Open your browser** and navigate to `http://localhost:7860`.

## Configuration

The application's primary configuration is located in `config.py`. Here you can:

*   **Add/Remove Radio Stations**: Modify the `RADIO_URLS` dictionary to add new stations.
*   **Map Stations to Languages**: Update the `STATION_LANGUAGES` dictionary to assign a language (`en`, `fr`, or `zh`) to new stations. The application defaults to English if a station is not explicitly mapped.
*   **Change ASR Models**: Update the `REPO_ID` and `MODEL_DIR` constants to use different `sherpa-onnx` models from the Hugging Face Hub.

## Technical Details & Design Choices

*   **ASR Engine (`sherpa-onnx`)**: Chosen for its high performance, low resource consumption, and excellent support for streaming recognition, which is critical for this real-time application.
*   **Connection Limit (`MAX_CONNECTIONS = 1`)**: In `core/connection_manager.py`, the maximum number of concurrent connections is set to `1`. This is an intentional design choice for the public demo on Hugging Face Spaces to manage CPU and memory resources effectively. It prevents multiple users from triggering separate, resource-intensive `ffmpeg` and ASR processes. For self-hosting, this value can be increased, but be mindful of server capacity.
*   **Chinese Text Conversion**: The `ASRService` uses the `opencc-python-reimplemented` library to convert the output of the Mandarin ASR model (which is in Simplified Chinese) to Traditional Chinese for display, catering to a broader audience.
*   **Frontend Audio Playback (`MediaSource` API)**: This browser API is used to create a custom media stream from the incoming raw audio chunks. It gives us precise control over the audio buffer and is essential for playing the non-standard stream of audio segments being sent from the backend.
*   **Synchronization**: The frontend implements a synchronization mechanism (`userSyncOffset`) to align the ASR timestamps with the actual audio playback time, accounting for network and processing latency. This offset can be adjusted via a slider in the debug panel.
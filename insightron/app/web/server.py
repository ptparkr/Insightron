import os
import sys
import uuid
import json
import logging
import asyncio
from typing import List, Optional
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Add root directory to python path
root_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Import Insightron Core Modules
from insightron.core.config import DEFAULT_LANGUAGE, WHISPER_MODEL
from insightron.core.settings_manager import SettingsManager
from insightron.services.transcription.transcribe import AudioTranscriber
from insightron.services.batch.batch_processor import batch_transcribe_files
from insightron.services.realtime.realtime_transcriber import RealtimeTranscriber

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI App
app = FastAPI(title="Insightron Web App")

# Managers
settings_manager = SettingsManager()

# Static Files
static_dir = Path(__file__).parent / "static"
app.mount("/css", StaticFiles(directory=static_dir / "css"), name="css")
app.mount("/js", StaticFiles(directory=static_dir / "js"), name="js")
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


# --- API Models ---
class SettingsPayload(BaseModel):
    model: str
    language: str
    formatting: str


# --- API Endpoints ---

@app.get("/api/settings")
async def get_settings():
    """Retrieve current settings."""
    return {
        "model": settings_manager.get("model", WHISPER_MODEL),
        "language": settings_manager.get("language", DEFAULT_LANGUAGE),
        "formatting": settings_manager.get("formatting", "auto")
    }

@app.post("/api/settings")
async def update_settings(payload: SettingsPayload):
    """Update settings."""
    settings_manager.set("model", payload.model)
    settings_manager.set("language", payload.language)
    settings_manager.set("formatting", payload.formatting)
    return {"status": "success"}

@app.post("/api/transcribe")
async def transcribe_single(file: UploadFile = File(...)):
    """Transcribe a single audio file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    # Save uploaded file to a temporary location
    suffix = Path(file.filename).suffix
    with NamedTemporaryFile(delete=False, suffix=suffix) as temp:
        temp.write(await file.read())
        temp_path = temp.name

    try:
        model_size = settings_manager.get("model", WHISPER_MODEL)
        lang = settings_manager.get("language", DEFAULT_LANGUAGE)
        formatting = settings_manager.get("formatting", "auto")
        
        # AudioTranscriber expects str paths usually
        transcriber = AudioTranscriber(model_size, lang)
        
        # This blocks, but we can wrap it in a thread later if needed
        # For simplicity in the FastAPI context, we just call it directly.
        # Run in executor to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        def _run_transcribe():
            return transcriber.transcribe_file(
                temp_path,
                progress_callback=lambda msg: logger.info(msg),
                formatting_style=formatting,
                language=lang
            )
        
        output_path, data = await loop.run_in_executor(None, _run_transcribe)
        return {
            "status": "success",
            "filename": output_path.name,
            "duration": data.get("duration", 0)
        }
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/api/batch")
async def transcribe_batch(files: List[UploadFile] = File(...)):
    """Transcribe multiple audio files."""
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    temp_paths = []
    
    for file in files:
        suffix = Path(file.filename).suffix
        with NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            temp.write(await file.read())
            temp_paths.append((temp.name, file.filename))
            
    try:
        model_size = settings_manager.get("model", WHISPER_MODEL)
        lang = settings_manager.get("language", DEFAULT_LANGUAGE)
        
        # Only pass paths to the batch processor
        file_paths = [p for p, _ in temp_paths]
        
        loop = asyncio.get_event_loop()
        def _run_batch():
            return batch_transcribe_files(
                file_paths,
                model_size=model_size,
                language=lang,
                progress_callback=lambda c, t, f: logger.info(f"Batch: {c}/{t} {f}")
            )
            
        results = await loop.run_in_executor(None, _run_batch)
        return {
            "status": "success",
            "successful": results.get("completed", 0),
            "failed": results.get("failed_count", 0)
        }
    except Exception as e:
        logger.error(f"Batch transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        for temp_path, _ in temp_paths:
            if os.path.exists(temp_path):
                os.remove(temp_path)

# --- Realtime WebSocket ---

@app.websocket("/api/realtime")
async def websocket_realtime(websocket: WebSocket):
    """Handle incoming realtime audio frames and stream transcriptions back."""
    await websocket.accept()
    logger.info("WebSocket connected for Realtime Transcription")
    
    # Initialize Realtime Transcriber
    rt = RealtimeTranscriber()
    rt.model_size = settings_manager.get("model", WHISPER_MODEL)
    rt.language = settings_manager.get("language", DEFAULT_LANGUAGE)
    
    # Custom loop for accepting raw chunk bytes over WS and sending transcripts
    try:
        # We start the engine but bypass device_index, feeding buffers manually
        rt.audio_queue.queue.clear()
        
        # Start transcription thread manually without pyAudio callback
        import threading
        rt.is_recording = True
        transcription_thread = threading.Thread(
            target=rt._transcription_loop,
            args=(
                lambda text: asyncio.run(websocket.send_json({"type": "transcript", "text": text, "is_final": True})),
                lambda lvl: None # We handle visualizer level client-side
            ),
            daemon=True
        )
        transcription_thread.start()
        
        # Receive loop
        import numpy as np
        while True:
            data = await websocket.receive()
            if 'text' in data:
                # Client sent a JSON message (e.g. {type:"eof"})
                msg = json.loads(data['text'])
                if msg.get('type') == 'eof':
                    logger.info("Received EOF from client.")
                    break
            elif 'bytes' in data:
                # 32-bit float array sent from AudioWorklet/ScriptProcessor
                raw_bytes = data['bytes']
                chunk = np.frombuffer(raw_bytes, dtype=np.float32)
                
                # Append to buffers
                rt.full_audio_buffer.append(chunk)
                rt.audio_queue.put(chunk)
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket Error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass
    finally:
        # Stop Transcriber
        rt.is_recording = False
        rt.audio_queue.put(None) # Unblock
        
        # Attempt to save the recording as a note just like gui does
        try:
            from datetime import datetime
            from insightron.core.config import RECORDINGS_FOLDER, TRANSCRIPTION_FOLDER
            from insightron.core.utils import create_realtime_note
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"web_recording_{timestamp}.wav"
            save_path = RECORDINGS_FOLDER / filename
            
            # Simple save (bypassing rt.save_recording if needed, or calling it)
            if rt.full_audio_buffer:
                rt.save_recording(str(save_path))
                
                t_data = rt.get_transcription_data()
                text_content = t_data['text'] or "(No speech detected)"
                note_filename = f"web_recording_{timestamp}"
                
                duration_seconds = 0
                total_samples = sum(len(c) for c in rt.full_audio_buffer)
                duration_seconds = total_samples / rt.sample_rate
                
                minutes = int(duration_seconds // 60)
                seconds = int(duration_seconds % 60)
                duration_str = f"{minutes}:{seconds:02d}"
                
                note_content = create_realtime_note(
                    filename=note_filename,
                    text=text_content,
                    date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    duration=duration_str,
                    file_size_mb=save_path.stat().st_size / (1024 * 1024) if save_path.exists() else 0,
                    model=rt.model_size,
                    language=t_data['language'],
                    formatting_style=settings_manager.get("formatting", "auto"),
                    duration_seconds=duration_seconds,
                    segments=t_data['segments'],
                    folder_path=str(TRANSCRIPTION_FOLDER)
                )
                
                note_path = TRANSCRIPTION_FOLDER / f"{note_filename}.md"
                note_path.write_text(note_content, encoding='utf-8')
                logger.info(f"Saved web recording note to {note_path}")
        except Exception as e:
            logger.error(f"Error saving web realtime note: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("insightron.app.web.server:app", host="127.0.0.1", port=8000, reload=True)


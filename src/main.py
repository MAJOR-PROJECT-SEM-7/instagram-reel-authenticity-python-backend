import json
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from src.controller.request_handler import handle_request
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import whisper

# Global variable to store the model
ml_models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    print("Loading Whisper model...")
    ml_models["whisper"] = whisper.load_model("base")
    print("Whisper model loaded.")
    yield
    # Clean up the ML models and release the resources
    ml_models.clear()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
)


@app.websocket("/api/checkAuthenticityWS")
async def check_authenticity_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_text()
        url = data

        if not url:
            await websocket.send_text(json.dumps({"step": "error", "message": "URL is required"}))
            await websocket.close()
            return
        
        # Pass the loaded model to the handler
        await handle_request(websocket, url, ml_models.get("whisper"))
        
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except json.JSONDecodeError:
        await websocket.send_text(json.dumps({"step": "error", "message": "Invalid JSON format"}))
    except Exception as e:
        await websocket.send_text(json.dumps({"step": "error", "message": f"An error occurred: {str(e)}"}))
    finally:
        try:
            await websocket.close()
        except:
            pass

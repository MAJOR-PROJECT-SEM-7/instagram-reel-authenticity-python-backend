from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from src.routes import router
from app.flow import check_authenticity, check_authenticity_websocket
import json
from testing_backend.auth import router as auth_router
from testing_backend.entires import router as entries_router
from fastapi.middleware.cors import CORSMiddleware
from websocketbackend.socket import websocket_backend

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:3000", "https://yourdomain.com"]
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, PUT, DELETE...
    allow_headers=["*"],  # Authorization, Content-Type...
)

app.include_router(router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(entries_router, prefix="/api")


@app.post("/api/checkAuthenticity")
async def check_authenticity_endpoint(request_data: dict):
    url = request_data.get("url")
    log = request_data.get("log", False)
    return check_authenticity(url, log)


@app.websocket("/api/checkAuthenticityWS")
async def check_authenticity_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        # Wait for initial message with URL
        data = await websocket.receive_text()
        # request_data = json.loads(data)
        # url = request_data.get("url")
        url = data
        
        if not url:
            await websocket.send_text(json.dumps({"step": "error", "message": "URL is required"}))
            await websocket.close()
            return
        
        # Process the authenticity check with WebSocket updates
        await websocket_backend(websocket, url)
        
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

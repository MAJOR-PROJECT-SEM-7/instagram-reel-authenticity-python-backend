import json
from fastapi.middleware.cors import CORSMiddleware
from src.controller.request_handler import handle_request
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()
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
        await handle_request(websocket, url)
        
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

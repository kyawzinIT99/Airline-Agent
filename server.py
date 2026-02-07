import os
import uvicorn
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Set
import asyncio
import json
from agent_logic import agent

app = FastAPI(title="✈️ Airline Assistant API")

# --- Persistence Layer ---
PROFILE_FILE = "user_profiles.json"

def load_profiles() -> Dict:
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_profile(user_id: str, data: Dict):
    profiles = load_profiles()
    profiles[user_id] = {**profiles.get(user_id, {}), **data}
    with open(PROFILE_FILE, "w") as f:
        json.dump(profiles, f, indent=2)

# --- WebSocket Management ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Message]] = []

# --- Routes ---

@app.websocket("/notifications")
async def notifications_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Notification stream active
        while True:
            await asyncio.sleep(60) # Keep alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/upload")
async def upload_endpoint(file: UploadFile = File(...)):
    try:
        # Simulate OCR processing with persistence
        extracted = {
            "document_type": "Passport",
            "name": "JOHN DOE",
            "passport_number": "A12345678",
            "valid_until": "2030-01-01"
        }
        save_profile("default_user", {"passport": extracted})
        
        return {
            "status": "success",
            "extracted_data": extracted,
            "message": "Document processed. Profile updated securely."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_endpoint(request: ChatRequest, fast_req: Request):
    user_agent = fast_req.headers.get("user-agent", "Unknown")
    print(f"📥 REQUEST FROM: {user_agent[:50]}")
    print(f"   MESSAGE: {request.message}")
    try:
        # Simple history formatting for the agent
        history_list = [{"role": msg.role, "content": msg.content} for msg in request.history] if request.history else []
        print(f"   HISTORY DEPTH: {len(history_list)}")
        
        # Add a timeout to the entire agent processing to prevent hung requests
        response_text = await asyncio.wait_for(agent.get_response(request.message, history_list), timeout=60.0)
        
        print(f"📤 Sending response: {response_text[:50]}...")
        return {
            "response": response_text,
            "status": "success"
        }
    except asyncio.TimeoutError:
        print("❌ Agent processing timed out.")
        return {
            "response": "⏳ I apologize, but the search is taking longer than usual. Please refresh the page or contact our hotline directly (01-8243993) for instant help!",
            "status": "error"
        }
    except Exception as e:
        import traceback
        print(f"❌ CRITICAL ERROR in chat endpoint: {str(e)}")
        traceback.print_exc()
        return {
            "response": f"⚠️ Technical difficulty: {str(e)}. Please contact developer Mr. Kyaw Zin Tun (0949567820).",
            "status": "error"
        }

@app.get("/")
async def read_index():
    return FileResponse("index.html")

# Serve other static files (js, css)
@app.get("/{filename}")
async def get_static(filename: str):
    if os.path.exists(filename):
        return FileResponse(filename)
    return JSONResponse(status_code=404, content={"message": "Not found"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

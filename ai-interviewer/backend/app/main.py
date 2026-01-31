from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "AI Interviewer Backend is running", "project": settings.PROJECT_NAME}

@app.get("/health")
def health_check():
    return {"status": "ok"}

from fastapi import WebSocket, WebSocketDisconnect
from app.services.stream_manager import manager

@app.websocket("/ws/stream/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.process_message(websocket, data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

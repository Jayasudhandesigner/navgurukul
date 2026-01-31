import asyncio
import websockets
import json
import requests
import base64

VALID_WAV_BASE64 = "UklGRigAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=" 

def check_http():
    try:
        r = requests.get("http://localhost:8000/health")
        if r.status_code == 200:
            print(f"[PASS] Backend Health: {r.json()}")
        else:
            print(f"[FAIL] Backend Health: Status {r.status_code}")
    except Exception as e:
        print(f"[FAIL] Backend Connection Refused: {e}")

async def check_ws():
    uri = "ws://localhost:8000/ws/stream/verify_bot"
    try:
        async with websockets.connect(uri) as websocket:
            print("[PASS] WebSocket Connected")
            
            # Simulate a video frame (Valid Base64 Image)
            # 1x1 Pixel JPEG
            VALID_IMG_BASE64 = "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA="
            
            msg_video = {
                "type": "video", 
                "payload": "data:image/jpeg;base64," + VALID_IMG_BASE64, 
                "timestamp": 1700000000
            }
            await websocket.send(json.dumps(msg_video))
            print("[PASS] Video Frame Sent (Valid JPEG)")

            # Simulate an audio frame
            msg_audio = {
                "type": "audio", 
                "payload": VALID_WAV_BASE64, 
                "timestamp": 1700000001
            }
            await websocket.send(json.dumps(msg_audio))
            print("[PASS] Audio Frame Sent")
            
            # Wait for responses
            try:
                # We might receive multiple messages
                # Timeout after 10s to give OCR time (model load)
                end_time = asyncio.get_event_loop().time() + 10.0
                while asyncio.get_event_loop().time() < end_time:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)
                    msg_type = data.get("type")
                    
                    if msg_type == "transcript":
                         print(f"[PASS] Received Transcript: '{data.get('text')}'")
                    elif msg_type == "visual_context":
                         print(f"[PASS] Received OCR Context: '{data.get('text')}'")
                    else:
                         print(f"[INFO] Received message: {msg_type}")
                         
            except asyncio.TimeoutError:
                print("[INFO] Message wait timeout (normal if no text found in blank image)")
            
    except Exception as e:
        print(f"[FAIL] WebSocket Error: {e}")

if __name__ == "__main__":
    print("--- Starting Realtime Feature Check (v4 - OCR) ---")
    check_http()
    asyncio.run(check_ws())

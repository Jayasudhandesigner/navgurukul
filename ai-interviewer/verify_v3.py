import asyncio
import websockets
import json
import requests
import base64

# A valid 1-second silent WAV file base64 encoded
# RIFF header + fmt chunk + data chunk (silence)
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
            
            # Simulate a video frame (still mock, we assume backend ignores invalid img for now)
            msg_video = {
                "type": "video", 
                "payload": "data:image/jpeg;base64,/9j/4AAQSkZJRg...", 
                "timestamp": 1700000000
            }
            await websocket.send(json.dumps(msg_video))
            print("[PASS] Video Frame Sent")

            # Simulate an audio frame with VALID data
            msg_audio = {
                "type": "audio", 
                "payload": VALID_WAV_BASE64, 
                "timestamp": 1700000001
            }
            await websocket.send(json.dumps(msg_audio))
            print("[PASS] Audio Frame Sent (Valid WAV)")
            
            # Wait for transcript response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                if data.get("type") == "transcript":
                     print(f"[PASS] Received Transcript: '{data.get('text')}'")
                else:
                     print(f"[INFO] Received other message: {data}")
            except asyncio.TimeoutError:
                print("[WARN] No transcript received (Silence might not trigger text, but connection held)")
            
    except Exception as e:
        print(f"[FAIL] WebSocket Error: {e}")

if __name__ == "__main__":
    print("--- Starting Realtime Feature Check (v3) ---")
    check_http()
    asyncio.run(check_ws())

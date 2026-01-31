import asyncio
import websockets
import json
import requests

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
            
            # Simulate a video frame
            msg_video = {
                "type": "video", 
                "payload": "data:image/jpeg;base64,/9j/4AAQSkZ...", 
                "timestamp": 1700000000
            }
            await websocket.send(json.dumps(msg_video))
            print("[PASS] Video Frame Sent")

            # Simulate an audio frame
            msg_audio = {
                "type": "audio", 
                "payload": "base64_encoded_audio_chunk...", 
                "timestamp": 1700000001
            }
            await websocket.send(json.dumps(msg_audio))
            print("[PASS] Audio Frame Sent")
            
            # Keep open briefly to ensure server processes it
            await asyncio.sleep(1)
            
    except ConnectionRefusedError:
        print("[FAIL] WebSocket Connection Refused (Is backend running?)")
    except Exception as e:
        print(f"[FAIL] WebSocket Error: {e}")

if __name__ == "__main__":
    print("--- Starting Realtime Feature Check ---")
    check_http()
    asyncio.run(check_ws())

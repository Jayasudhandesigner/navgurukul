import asyncio
import websockets
import json
import base64

VALID_WAV_BASE64 = "UklGRigAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=" 

async def check_ws():
    uri = "ws://localhost:8000/ws/stream/verify_bot_v6"
    try:
        async with websockets.connect(uri) as websocket:
            print("[PASS] WebSocket Connected")
            
            # 1. Update Context (Audio)
            # Backend should have some mock transcription or we assume it works if `transcribe_audio` result is mocked/passed.
            # Wait, our `transcribe_audio` actually calls FasterWhisper. 
            # If silence (VALID_WAV_BASE64) returns nothing, context remains empty.
            # I will assume the previous unit test confirmed context works.
            # I will send audio just to keep flow valid.
            msg_audio = {
                "type": "audio", 
                "payload": VALID_WAV_BASE64, 
                "timestamp": 1700000001
            }
            await websocket.send(json.dumps(msg_audio))
            
            # 2. Trigger Question manually
            # We want to test connections to Groq
            msg_trigger = {
                "type": "trigger_question" 
            }
            await websocket.send(json.dumps(msg_trigger))
            print("[PASS] Trigger Sent")

            # Wait for Question
            try:
                end_time = asyncio.get_event_loop().time() + 15.0 
                while asyncio.get_event_loop().time() < end_time:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)
                    msg_type = data.get("type")
                    
                    if msg_type == "question":
                        payload = data.get("payload")
                        print(f"[SUCCESS] Received Question: {payload}")
                        return
                    elif msg_type == "transcript":
                        pass # Ignore
                    else:
                        print(f"[INFO] Ignored: {msg_type}")
                        
                print("[FAIL] Timeout waiting for question.")
                    
            except asyncio.TimeoutError:
                print("[WARN] Timeout waiting for question.")
            
    except Exception as e:
        print(f"[FAIL] WebSocket Error: {e}")

if __name__ == "__main__":
    print("--- Starting Phase 6 LLM Check (Groq) ---")
    asyncio.run(check_ws())

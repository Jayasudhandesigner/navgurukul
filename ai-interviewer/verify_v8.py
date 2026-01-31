import asyncio
import websockets
import json
import base64

VALID_WAV_BASE64 = "UklGRigAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=" 

async def check_ws():
    uri = "ws://localhost:8000/ws/stream/verify_bot_v8"
    try:
        async with websockets.connect(uri) as websocket:
            print("[PASS] WebSocket Connected")
            
            # 0. Skip Audio Seed to avoid Whisper blocking/latency during flow test.
            # Context will be empty, but LLM should still generate a generic question.
            
            # 1. Trigger Question
            await websocket.send(json.dumps({"type": "trigger_question"}))
            print("[Sent] Trigger Question")
            
            question_received = False
            
            # Wait for Question
            try:
                end_time = asyncio.get_event_loop().time() + 30.0 # Increased timeout
                while asyncio.get_event_loop().time() < end_time:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(msg)
                    print(f"[RECV] {data.get('type')}") # Print all types
                    
                    if data.get('type') == 'state_update':
                        print(f"       -> State: {data.get('state')}")
                    
                    if data.get('type') == 'question':
                        print(f"[PASS] Question Received: {data['payload']['question_text']}")
                        question_received = True
                        break
            except asyncio.TimeoutError:
                print("[FAIL] Timeout waiting for question")
                return

            if question_received:
                # 2. Simulate User Answering
                # Send explicit answer logic (skip audio processing for speed)
                
                # 3. Submit Answer
                await websocket.send(json.dumps({
                    "type": "submit_answer",
                    "payload": "I would use a cache like Redis." 
                }))
                print("[Sent] Submit Answer")
                
                # 4. Wait for Evaluation
                try:
                    end_time = asyncio.get_event_loop().time() + 20.0
                    while asyncio.get_event_loop().time() < end_time:
                        msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        data = json.loads(msg)
                        if data.get('type') == 'state_update':
                             print(f"[RECV] State: {data.get('state')}")
                        
                        if data.get('type') == 'evaluation':
                            print(f"[SUCCESS] Evaluation Received. Score: {data['payload']['score']}")
                            print(f"Feedback: {data['payload']['feedback']}")
                            return
                except asyncio.TimeoutError:
                    print("[FAIL] Timeout waiting for evaluation")

    except Exception as e:
        print(f"[FAIL] WebSocket Error: {e}")

if __name__ == "__main__":
    print("--- Starting Phase 8 Flow Check ---")
    asyncio.run(check_ws())

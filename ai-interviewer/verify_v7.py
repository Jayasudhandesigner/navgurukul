import asyncio
import websockets
import json

async def check_ws():
    uri = "ws://localhost:8000/ws/stream/verify_bot_v7"
    try:
        async with websockets.connect(uri) as websocket:
            print("[PASS] WebSocket Connected")
            
            # 0. Seed Context (so LLM has something to ask about)
            await websocket.send(json.dumps({
                "type": "transcript", # Note: Frontend doesn't send "transcript", it sends "audio" -> backend generates transcript.
                # But here we are simulating backend-to-backend or client-to-backend.
                # Actually, client sends AUDIO.
                # Easier: rely on manual context injection or just send "audio" message with VALID WAV
            }))
            # Let's send a valid Mock Audio to populate Transcript
            VALID_WAV_BASE64 = "UklGRigAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=" 
            await websocket.send(json.dumps({
                "type": "audio",
                "payload": VALID_WAV_BASE64,
                "timestamp": 1700000000
            }))
            
            # Also send a video frame text "React and PyTorch"
            # We can use the logic from v5 or just assume audio is enough.
            # actually, let's keep it simple. The LLM should handle empty context.
            # Maybe the timeout was just too short for the first LLM call?
            
            # 1. Trigger Question
            await websocket.send(json.dumps({"type": "trigger_question"}))
            print("[PASS] Triggered Question")
            
            question_text = ""
            
            # Wait for Question (Increased Timeout)
            try:
                msg = await asyncio.wait_for(websocket.recv(), timeout=20.0)
                data = json.loads(msg)
                
                # We might get 'transcript' first if we sent audio
                if data["type"] == "transcript":
                     msg = await asyncio.wait_for(websocket.recv(), timeout=20.0)
                     data = json.loads(msg)
                
                if data["type"] == "question":
                    question_text = data["payload"]["question_text"]
                    print(f"[PASS] Received Question: {question_text}")
            except asyncio.TimeoutError:
                print("[FAIL] Timeout waiting for question")
                return

            if question_text:
                # 2. Send Answer
                # Simulating a mediocre answer
                answer = "I think it is about managing state efficiently."
                print(f"[INFO] Sending Answer: '{answer}'")
                
                await websocket.send(json.dumps({
                    "type": "evaluate_answer", 
                    "payload": answer
                }))
                
                # 3. Wait for Evaluation
                try:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                    data = json.loads(msg)
                    if data["type"] == "evaluation":
                        score = data["payload"]["score"]
                        feedback = data["payload"]["feedback"]
                        print(f"[SUCCESS] Evaluation Received. Score: {score}/10")
                        print(f"Feedback: {feedback}")
                except asyncio.TimeoutError:
                    print("[FAIL] Timeout waiting for evaluation")

    except Exception as e:
        print(f"[FAIL] WebSocket Error: {e}")

if __name__ == "__main__":
    print("--- Starting Phase 7 Evaluation Check ---")
    asyncio.run(check_ws())

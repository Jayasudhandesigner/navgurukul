import asyncio
import websockets
import json

async def check_ws():
    uri = "ws://localhost:8000/ws/stream/verify_bot_v9"
    try:
        async with websockets.connect(uri) as websocket:
            print("[PASS] WebSocket Connected")
            
            # 0. Simulate some history (Backend keeps it in memory, but we need to populate context first)
            # Actually, without history, report triggers but might be empty.
            # To test fully, we should trigger a question/answer cycle, but that takes time.
            # Let's simple check if `end_session` returns ANY report.
            
            # 1. Trigger End Session
            await websocket.send(json.dumps({
                "type": "end_session"
            }))
            print("[Sent] End Session")
            
            # 2. Wait for Report
            try:
                # LLM takes time (Groq is fast, but report is long) - 30s timeout
                end_time = asyncio.get_event_loop().time() + 30.0 
                while asyncio.get_event_loop().time() < end_time:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(msg)
                    print(f"[RECV] {data.get('type')}")
                    
                    if data.get('type') == 'report':
                        report_content = data['payload']
                        print(f"[SUCCESS] Report Received ({len(report_content)} chars)")
                        print("--- Preview ---")
                        print(report_content[:200] + "...")
                        return
                        
            except asyncio.TimeoutError:
                print("[FAIL] Timeout waiting for report")

    except Exception as e:
        print(f"[FAIL] WebSocket Error: {e}")

if __name__ == "__main__":
    print("--- Starting Phase 9 Report Check ---")
    asyncio.run(check_ws())

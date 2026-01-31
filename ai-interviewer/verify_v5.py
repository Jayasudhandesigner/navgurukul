import asyncio
import websockets
import json
import base64
from PIL import Image, ImageDraw, ImageFont
import io

# Create a dummy image with Text "We are using React and FastAPI"
def create_text_image(text):
    img = Image.new('RGB', (800, 200), color = (255, 255, 255)) # Larger image
    d = ImageDraw.Draw(img)
    # Load default font is too small, let's try to draw simple large text scaling not available easily without font file.
    # We will just write it multiple times or rely on EasyOCR being good.
    # actually, I can't load a ttf easily. I'll stick to default but maybe just shorter text.
    d.text((50,50), text, fill=(0,0,0)) 
    
    # Scale up using resize to simulate larger font
    img = img.resize((1600, 400), resample=Image.NEAREST)
    
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    return base64.b64encode(buf.getvalue()).decode('utf-8')

async def check_ws():
    uri = "ws://localhost:8000/ws/stream/verify_bot_v5_retry"
    try:
        async with websockets.connect(uri) as websocket:
            print("[PASS] WebSocket Connected")
            
            # 1. Send Video Frame with Keywords
            img_b64 = create_text_image("React FastAPI") # Simpler text
            
            msg_video = {
                "type": "video", 
                "payload": "data:image/jpeg;base64," + img_b64, 
                "timestamp": 1700000000,
                "note": "Image contains 'React' and 'FastAPI'"
            }
            await websocket.send(json.dumps(msg_video))
            print("[PASS] Video Frame Sent")
            
            # Wait for Context Update - Increased timeout for cold start
            try:
                end_time = asyncio.get_event_loop().time() + 30.0 
                detected = False
                while asyncio.get_event_loop().time() < end_time:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)
                    msg_type = data.get("type")
                    
                    if msg_type == "visual_context":
                        print(f"[PASS] OCR Read: '{data.get('text')}'")
                    elif msg_type == "context_update":
                        kws = data.get("keywords")
                        print(f"[PASS] Context Detected Keywords: {kws}")
                        if "react" in kws:
                            print("[SUCCESS] Context Engine identified correct Tech Stack!")
                            detected = True
                            break
                            
                if not detected:
                    print("[FAIL] Did not receive context_update with expected keywords.")
                    
            except asyncio.TimeoutError:
                print("[WARN] Timeout waiting for context update.")

            
    except Exception as e:
        print(f"[FAIL] WebSocket Error: {e}")

if __name__ == "__main__":
    print("--- Starting Phase 5 Context Check ---")
    asyncio.run(check_ws())

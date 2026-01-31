import asyncio
import base64
import os
import sys

# Ensure backend path is in sys.path
sys.path.append(os.path.abspath("a:/Navgurukul/ai-interviewer/backend"))

from app.core.llm_client import llm_client

async def test_vision():
    print("Testing OpenRouter Vision API (Molmo2-8B)...")
    
    # Use a small 1x1 pixel black png base64 for quick testing if no file found
    # Or try to load the artifact if it exists
    image_path = "C:/Users/jayas/.gemini/antigravity/brain/9a93cb97-ac89-452f-ad95-daec018720de/uploaded_media_1769858636466.png"
    
    base64_data = ""
    if os.path.exists(image_path):
        print(f"Loading test image: {image_path}")
        with open(image_path, "rb") as f:
            base64_data = base64.b64encode(f.read()).decode("utf-8")
    else:
        print("Test image not found, using valid 1x1 pixel base64...")
        base64_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="

    try:
        print("Sending request to OpenRouter...")
        result = await llm_client.analyze_image(base64_data)
        
        if result:
            print("\nSUCCESS! Vision API Returned:")
            print("-" * 50)
            print(result)
            print("-" * 50)
        else:
            print("\nFAILURE: Vision API returned None.")
            
    except Exception as e:
        print(f"\nEXCEPTION: {e}")

if __name__ == "__main__":
    asyncio.run(test_vision())

import asyncio
from app.core.llm_client import llm_client
import logging

logging.basicConfig(level=logging.INFO)

async def test_llm():
    print("Testing LLM Client...")
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Output JSON."},
        {"role": "user", "content": "Say hello in JSON format: {'message': '...'}"}
    ]
    
    response = await llm_client.get_chat_completion(messages)
    print(f"Response: {response}")
    
    if response and "hello" in response.lower():
        print("[PASS] LLM Client Operational")
    else:
        print("[FAIL] LLM Client No Response or Invalid")

if __name__ == "__main__":
    asyncio.run(test_llm())

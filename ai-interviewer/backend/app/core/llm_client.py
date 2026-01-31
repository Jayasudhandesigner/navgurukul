import os
from groq import AsyncGroq
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

def log_debug(msg):
    try:
        with open("a:/Navgurukul/ai-interviewer/backend/debug_final.log", "a") as f:
            f.write(f"[LLM] {msg}\n")
    except: pass

from openai import AsyncOpenAI

class LLMClient:
    def __init__(self):
        # Groq Setup
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            logger.warning("GROQ_API_KEY not found!")
            self.groq_client = None
        else:
            self.groq_client = AsyncGroq(api_key=groq_key)
            
        # OpenRouter Setup (for Vision)
        # Using the key provided by user: sk-or-v1-fe83b6d6...
        # Ideally this should be in os.getenv("OPENROUTER_API_KEY")
        or_key = "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"
        self.or_client = AsyncOpenAI(
            api_key=or_key,
            base_url="https://openrouter.ai/api/v1"
        )
        logger.info("Clients initialized (Groq + OpenRouter).")

    async def get_chat_completion(self, messages, model="llama-3.3-70b-versatile", temperature=0.7, json_mode=True):
        if not self.groq_client: return None
        try:
            kwargs = { "messages": messages, "model": model, "temperature": temperature }
            if json_mode: kwargs["response_format"] = {"type": "json_object"}
            chat_completion = await self.groq_client.chat.completions.create(**kwargs)
            return chat_completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq Chat Error: {e}")
            return None

    async def transcribe_audio(self, audio_bytes):
        if not self.groq_client: return None
        try:
            transcription = await self.groq_client.audio.transcriptions.create(
                file=("audio.webm", audio_bytes),
                model="whisper-large-v3",
                response_format="text",
                language="en"
            )
            return transcription
        except Exception as e:
            logger.error(f"Groq Audio Error: {e}")
            return None

    async def analyze_image(self, base64_image):
        if not self.or_client: return None
        try:
            response = await self.or_client.chat.completions.create(
                model="google/gemma-3-27b-it:free",
                extra_headers={
                    "HTTP-Referer": "http://localhost:5173", 
                    "X-Title": "AI Interviewer"
                },
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe the technical content of this screen accurately. Identify any code, diagrams, or slide titles. Be concise."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenRouter Vision Error: {e}")
            log_debug(f"Vision Error: {e}")
            return None

llm_client = LLMClient()

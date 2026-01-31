import logging
import json
from app.core.llm_client import llm_client

logger = logging.getLogger(__name__)

class QuestionEngine:
    def __init__(self):
        pass

    async def generate_question(self, context: dict):
        """
        Generates a question based on the provided context.
        Context keys: 'transcript_summary', 'keywords', 'current_slide', 'topics'
        """
        
        system_prompt = f"""
        You are an expert Technical Interviewer conducting a {context.get('current_phase', 'General')} round.
        Your goal is to ask a relevant question based on the candidate's presentation AND the provided Job Description.
        
        Current Phase: {context.get('current_phase', 'General')}
        Phase Strategy:
        - Introduction: Ask about their background and the project's inspiration.
        - Project Walkthrough: Ask about the architecture, tech stack decisions, and flow.
        - Technical Deep Dive: Ask hard technical questions about specific code/implementation details observed.
        - Behavioral/HR: Ask about challenges faced, conflicts, and soft skills (aligned with JD).
        - Closing: Ask if they have questions or summary thoughts.
        
        Rules:
        1. Keep the question short and conversational.
        2. Focus strictly on the CURRENT PHASE strategy.
        Rules:
        1. Keep the question short and conversational.
        2. Focus strictly on the CURRENT PHASE strategy.
        3. START with a brief 1-sentence acknowledgment or reaction to the candidate's answer (e.g., "That makes sense.", "Interesting approach.", "I see.").
        4. Output MUST be valid JSON with keys: "question_text", "difficulty" (Junior/Mid/Senior), "topic".
        """
        
        jd_text = context.get('job_description', 'Not Provided')
        
        user_prompt = f"""
        Job Description:
        {jd_text[:1000]}... (Truncated)
        
        Current Context:
        - Recent Transcript: {context.get('transcript_summary', '')}
        - Detected Keywords: {', '.join(context.get('keywords', []))}
        - Slide Text: {context.get('current_slide', '')[:500]}...
        - Topics: {', '.join(context.get('topics', []))}
        - Visual Description: {context.get('visual_context', '')}
        
        Last Question Asked: {context.get('previous_question', 'None')}
        Candidate's Last Answer: {context.get('previous_answer', 'None')}
        
        Generate a {context.get('current_phase', 'General')} question now.
        IF the valid Candidate's Last Answer is provided, you MUST ask a follow-up question digging deeper into it.
        """

        logger.info("Requesting Question from LLM...")
        response_json_str = await llm_client.get_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        if response_json_str:
            try:
                data = json.loads(response_json_str)
                logger.info(f"Generated Question: {data}")
                return data
            except json.JSONDecodeError:
                logger.error("Failed to parse LLM JSON response")
                return None
        return None

question_engine = QuestionEngine()

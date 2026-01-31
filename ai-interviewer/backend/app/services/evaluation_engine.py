import logging
import json
from app.core.llm_client import llm_client

logger = logging.getLogger(__name__)

class EvaluationEngine:
    def __init__(self):
        pass

    async def evaluate_answer(self, question: str, answer: str, context: dict):
        """
        Evaluates the candidate's answer against the question.
        """
        
        system_prompt = """
        You are an expert Technical Interviewer. 
        Your goal is to evaluate the candidate's answer to a technical question.
        
        Rules:
        1. Score the answer from 1-10 based on Accuracy, Depth, and Clarity.
        2. Identify key missing points.
        3. Provide a brief "Better Answer" example.
        4. Output MUST be valid JSON with keys: "score" (int), "feedback" (str), "missing_points" (list[str]), "better_answer" (str).
        """
        
        user_prompt = f"""
        Question: {question}
        
        Candidate's Answer: {answer}
        
        Context (What they were presenting):
        - Tech Stack: {', '.join(context.get('keywords', []))}
        
        Evaluate now.
        """

        logger.info("Requesting Evaluation from LLM...")
        response_json_str = await llm_client.get_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        if response_json_str:
            try:
                data = json.loads(response_json_str)
                logger.info(f"Evaluation Result: {data}")
                return data
            except json.JSONDecodeError:
                logger.error("Failed to parse LLM JSON response")
                return None
        return None

evaluation_engine = EvaluationEngine()

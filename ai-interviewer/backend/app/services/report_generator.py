import logging
import json
from app.core.llm_client import llm_client

logger = logging.getLogger(__name__)

class ReportGenerator:
    def __init__(self):
        pass

    async def generate_report(self, session_data: dict) -> str:
        """
        Generates a comprehensive interview report.
        session_data: {
            "transcript_summary": str,
            "q_and_a": list[dict]  # [{"question": "...", "answer": "...", "score": 8, "feedback": "..."}]
            "keywords": list[str]
        }
        Returns: Markdown string
        """
        
        q_a_history = ""
        total_score = 0
        count = 0
        
        for item in session_data.get("q_and_a", []):
            q_a_history += f"""
            Q: {item['question']}
            A: {item['answer']}
            Score: {item['score']}/10
            Feedback: {item['feedback']}
            ---
            """
            total_score += item.get('score', 0)
            count += 1
            
        avg_score = round(total_score / count, 1) if count > 0 else 0

        system_prompt = """
        You are a Senior Technical Hiring Manager.
        Your goal is to write a constructive Interview Feedback Report for a candidate.
        
        Output Format: MARKDOWN
        Structure:
        # Interview Performance Report
        ## Executive Summary
        (Pass/Fail/Training Needed)
        
        ## Scores
        - **Technical Score**: {calculate based on Q&A}
        - **Communication Score**: {assess based on transcript clarity}
        
        ## Key Topics Covered
        (List detected topics)
        
        ## Detailed Feedback
        (Analyze their answers. Highlight strengths and weaknesses.)
        
        ## Recommendations
        (What exactly should they study next? Be specific.)
        """
        
        user_prompt = f"""
        Candidate Context:
        - Detected Tech Stack: {', '.join(session_data.get('keywords', []))}
        - Session Transcript Summary: {session_data.get('transcript_summary', '')}
        
        Q&A History:
        {q_a_history}
        
        Average Technical Score: {avg_score}/10
        
        Generate the report now.
        """

        logger.info("Requesting Report from LLM...")
        report_md = await llm_client.get_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.3-70b-versatile",
            json_mode=False # Request raw Markdown
        )
        
        return report_md

report_generator = ReportGenerator()

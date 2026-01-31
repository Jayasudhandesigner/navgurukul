import base64
import json
import logging
import os
from enum import Enum
from fastapi import WebSocket, WebSocketDisconnect

# from app.services.transcription import transcriber # Removed local transcriber
# from app.services.ocr_service import ocr_engine # Replaced by Molmo2-8B Vision
from app.services.context_engine import context_engine
from app.services.question_engine import question_engine
from app.services.evaluation_engine import evaluation_engine
from app.services.report_generator import report_generator
from app.core.llm_client import llm_client

def log_debug(msg):
    try:
        # Use a safe absolute path or just current dir if writable
        path = "a:/Navgurukul/ai-interviewer/backend/debug_final.log"
        with open(path, "a") as f:
            f.write(msg + "\n")
    except Exception as e:
        pass

logger = logging.getLogger(__name__)

class InterviewState(str, Enum):
    MONITORING = "MONITORING"         
    QUESTIONING = "QUESTIONING"       
    AWAITING_ANSWER = "AWAITING_ANSWER" 
    EVALUATING = "EVALUATING"         

class StreamManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.frame_count = 0 
        self.state = InterviewState.MONITORING
        self.last_asked_question = None
        self.current_answer_buffer = "" 
        self.session_history = [] 
        
        # Interview Phase Management
        self.interview_phases = ["Introduction", "Project Walkthrough", "Technical Deep Dive", "Behavioral/HR", "Closing"]
        self.current_phase_index = 0
        self.questions_asked_in_phase = 0
        self.PHASE_LIMITS = {
            "Introduction": 1,
            "Project Walkthrough": 2,
            "Technical Deep Dive": 3,
            "Behavioral/HR": 2,
            "Closing": 1
        } 

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        await self.send_state_update(websocket)
        logger.info(f"Client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.active_connections)}")

    async def send_state_update(self, websocket: WebSocket):
        await websocket.send_json({
            "type": "state_update",
            "state": self.state
        })

    async def transition_to(self, new_state: InterviewState, websocket: WebSocket):
        logger.info(f"State Transition: {self.state} -> {new_state}")
        self.state = new_state
        await self.send_state_update(websocket)

    async def process_message(self, websocket: WebSocket, data: str):
        try:
            log_debug(f"Processing message: {data[:50]}...")
            message = json.loads(data)
            msg_type = message.get("type")
            
            if msg_type == "audio":
                payload = message.get("payload")
                if payload:
                    if "," in payload:
                        payload = payload.split(",")[1]
                    audio_bytes = base64.b64decode(payload)
                    log_debug(f"Received audio: {len(audio_bytes)} bytes")
                    
                    # Use Groq API (Async)
                    text = await llm_client.transcribe_audio(audio_bytes)
                    log_debug(f"Transcription result: {text}")
                    
                    if text:
                        context_engine.update_transcript(text)
                        
                        if self.state == InterviewState.AWAITING_ANSWER:
                            self.current_answer_buffer += " " + text
                        
                        await websocket.send_json({
                            "type": "transcript",
                            "text": text,
                            "timestamp": message.get("timestamp")
                        })
                        
                        # Voice Trigger for "Done"
                        trigger_phrases = ["done with", "next question", "finished answer", "that's my answer"]
                        if any(phrase in text.lower() for phrase in trigger_phrases):
                            log_debug(f"Voice Trigger Detected: {text}")
                            # Mimic submit_answer payload
                            await self.process_message(websocket, json.dumps({
                                "type": "submit_answer", 
                                "payload": self.current_answer_buffer
                            }))

            elif msg_type == "video":
                self.frame_count += 1
                # Process every 3 frames (approx 3 seconds) -> faster feedback
                if self.frame_count % 3 == 0: 
                    print(f"DEBUG: Processing Video Frame #{self.frame_count}")
                    payload = message.get("payload")
                    if payload:
                        if "," in payload:
                            payload = payload.split(",")[1]
                        
                        # Use LLM Vision (OpenRouter / Molmo2-8B)
                        log_debug(f"Sending frame to Vision Model... ({len(payload)} bytes)")
                        extracted_text = await llm_client.analyze_image(payload)
                        
                        if extracted_text and extracted_text.strip():
                            log_debug(f"Vision Description: {extracted_text[:50]}...")
                            context_engine.update_visuals(extracted_text)
                            
                            await websocket.send_json({
                                "type": "visual_log",
                                "text": f"Visual Context: {extracted_text[:100]}...", 
                                "description": extracted_text, 
                                "image": payload, 
                                "timestamp": message.get("timestamp")
                            })

                if self.state == InterviewState.MONITORING:
                    # Check for context update every 5 seconds
                    if self.frame_count % 5 == 0: 
                         ctx = context_engine.get_context()
                         # Trigger if we have enough context (visuals or audio)
                         if ctx["keywords"] or ctx["transcript_summary"] or ctx.get("visual_context"):
                             await self.transition_to(InterviewState.QUESTIONING, websocket)
                             
                             # Get Current Phase
                             current_phase = self.interview_phases[self.current_phase_index]
                             ctx["current_phase"] = current_phase
                             
                             # Inject Previous Answer for continuity
                             if self.session_history:
                                 last_entry = self.session_history[-1]
                                 ctx["previous_answer"] = last_entry.get("answer", "")
                                 ctx["previous_question"] = last_entry.get("question", "")
                             
                             q_data = await question_engine.generate_question(ctx)
                             if q_data:
                                 self.questions_asked_in_phase += 1
                             if q_data:
                                 self.last_asked_question = q_data.get("question_text")
                                 self.current_answer_buffer = "" 
                                 await websocket.send_json({
                                    "type": "question",
                                    "payload": q_data
                                 })
                                 await self.transition_to(InterviewState.AWAITING_ANSWER, websocket)
                             else:
                                 await self.transition_to(InterviewState.MONITORING, websocket)

            elif msg_type == "job_description":
                text = message.get("payload")
                if text:
                    context_engine.set_job_description(text)
                    log_debug(f"JD Set via WebSocket: {len(text)} chars")
                    
                    # Trigger Greeting (Intro Phase)
                    greeting = "System checks complete. Audio and Video streams are active. I have reviewed the job description. Let's begin the interview. Please start by introducing yourself and your project."
                    await self.transition_to(InterviewState.AWAITING_ANSWER, websocket)
                    self.last_asked_question = greeting
                    self.current_answer_buffer = ""
                    # Reset Phase
                    self.current_phase_index = 0
                    self.questions_asked_in_phase = 1 # Greeting counts as 1
                    
                    await websocket.send_json({
                        "type": "question",
                        "payload": {"question_text": greeting, "difficulty": "Intro", "topic": "Introduction"}
                    })

            elif msg_type == "submit_answer":
                if self.state == InterviewState.AWAITING_ANSWER and self.last_asked_question:
                    await self.transition_to(InterviewState.EVALUATING, websocket)
                    answer_text = message.get("payload") or self.current_answer_buffer
                    ctx = context_engine.get_context()
                    eval_data = await evaluation_engine.evaluate_answer(self.last_asked_question, answer_text, ctx)
                    
                    if eval_data:
                        self.session_history.append({
                            "question": self.last_asked_question,
                            "answer": answer_text,
                            "score": eval_data.get("score"),
                            "feedback": eval_data.get("feedback")
                        })
                        await websocket.send_json({
                            "type": "evaluation",
                            "payload": eval_data
                        })
                        
                    # Advance Phase Logic
                    current_phase = self.interview_phases[self.current_phase_index]
                    limit = self.PHASE_LIMITS.get(current_phase, 2)
                    
                    if self.questions_asked_in_phase >= limit:
                        if self.current_phase_index < len(self.interview_phases) - 1:
                            self.current_phase_index += 1
                            self.questions_asked_in_phase = 0
                            log_debug(f"Advancing Phase to: {self.interview_phases[self.current_phase_index]}")
                        else:
                            log_debug("Interview Complete. Ending Session.")
                            # Could auto-trigger end_session here
                            
                    await self.transition_to(InterviewState.MONITORING, websocket)

            elif msg_type == "end_session":
                log_debug("Received end_session")
                try:
                    ctx = context_engine.get_context()
                    session_data = {
                        "transcript_summary": ctx.get("transcript_summary", ""),
                        "keywords": list(ctx.get("keywords", [])),
                        "q_and_a": self.session_history
                    }
                    log_debug("Calling Report Generator...")
                    report = await report_generator.generate_report(session_data)
                    log_debug(f"Report Generated ({len(report) if report else 0} chars)")
                    
                    if report:
                        await websocket.send_json({
                            "type": "report",
                            "payload": report
                        })
                        log_debug("Report Sent to Client")
                    else:
                        log_debug("Report generation returned None")
                except Exception as e:
                    log_debug(f"Error generating report: {e}")
                    logger.error(f"Report Error: {e}")

            elif msg_type == "trigger_question":
                 print("DEBUG: Received trigger_question")
                 await self.transition_to(InterviewState.QUESTIONING, websocket)
                 ctx = context_engine.get_context()
                 q_data = await question_engine.generate_question(ctx)
                 if q_data:
                    self.last_asked_question = q_data.get("question_text")
                    self.current_answer_buffer = ""
                    await websocket.send_json({
                        "type": "question",
                        "payload": q_data
                    })
                    print("DEBUG: Question Sent")
                    await self.transition_to(InterviewState.AWAITING_ANSWER, websocket)

        except json.JSONDecodeError:
            logger.error("Failed to decode JSON message")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            log_debug(f"DEBUG Error: {e}")

manager = StreamManager()

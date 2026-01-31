# AI Interviewer & Presentation Coach - System Architecture

## 1. Overview
The system is designed to be a real-time AI-powered coach that captures a presenter's screen and audio, processes it to understand the context, and generates relevant interview questions and feedback.

## 2. Technology Stack
- **Frontend**: React (Vite) + TailwindCSS
- **Backend**: Python (FastAPI)
- **Communication**: WebSockets (Real-time streaming)
- **AI Models**:
    - **STT**: OpenAI Whisper
    - **LLM**: Google Gemini / OpenAI GPT-4
    - **OCR**: EasyOCR / Tesseract
- **Database**: SQLite (Development) / PostgreSQL (Production)

## 3. System Components

### 3.1 Client (Frontend)
- **Capture Module**: Uses `getDisplayMedia` and `getUserMedia` to capture screen and microphone.
- **Streaming Module**: Sends audio/video chunks to the backend via WebSockets.
- **UI/UX**: Displays live transcript, generated questions, and final analysis reports.

### 3.2 Server (Backend)
- **Ingestion Service**: FastAPI WebSocket endpoint to receive binary streams.
- **Processing Pipeline**:
    - **Audio Path**: Audio Chunk -> STT Engine -> Text Stream.
    - **Visual Path**: Video Frame -> Frame Extractor -> OCR Engine -> Visual Context.
- **Context Builder**: Aggregates Text Stream and Visual Context into a sliding window of "Current Session Context".
- **Interviewer Agent**: LLM-based agent that monitors Context and decides when to trigger a question.
- **Evaluator**: Post-session analysis of answers.

## 4. Data Flow
1.  **Input**: User starts presentation. Frontend captures Screen + Mic.
2.  **Transmission**: Data streamed to Backend `ws://localhost:8000/ws`.
3.  **Processing**:
    - Audio converted to text (Transcript).
    - Key frames extracted and OCR'd (Visual Data).
4.  **Synthesis**: Data merged into state `{"transcript": "...", "visuals": "..."}`.
5.  **Decision**: AI checks state. If interesting topic found -> Generate Question.
6.  **Output**: Question sent to Frontend. User answers.
7.  **Evaluation**: Answer recorded and scored.

## 5. Directory Structure
```
/project-root
  /frontend       # React Application
  /backend        # FastAPI Application
  /ai-models      # Model weights and inference scripts
  /docs           # Documentation
```

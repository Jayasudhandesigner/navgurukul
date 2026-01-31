import React, { useState, useRef, useEffect } from 'react';

interface MediaCaptureProps {
    onStatusChange?: (status: string) => void;
}

const MediaCapture: React.FC<MediaCaptureProps> = ({ onStatusChange }) => {
    const [report, setReport] = useState<string | null>(null);
    const [currentQuestion, setCurrentQuestion] = useState<string | null>(null);
    const [isCapturing, setIsCapturing] = useState(false);

    // Changed to array for log
    interface TranscriptEntry {
        time: string;
        text: string;
        type: 'audio' | 'visual';
        image?: string; // Base64 image for visual logs
    }
    const [transcriptLog, setTranscriptLog] = useState<TranscriptEntry[]>([]);
    const [visualLog, setVisualLog] = useState<TranscriptEntry[]>([]);
    const [viewMode, setViewMode] = useState<'transcript' | 'visuals'>('transcript');

    const videoRef = useRef<HTMLVideoElement>(null);
    const socketRef = useRef<WebSocket | null>(null);
    const mediaStreamRef = useRef<MediaStream | null>(null);
    const audioRecorderRef = useRef<MediaRecorder | null>(null);
    const intervalRef = useRef<number | null>(null);
    const isRecordingRef = useRef(false);

    // Format seconds into MM:SS
    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    // Track session start time for relative timestamps
    const [sessionStartTime, setSessionStartTime] = useState<number | null>(null);

    // TTS Function
    const speakText = (text: string) => {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel(); // Stop previous
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = 1.0;
            utterance.pitch = 1.0;
            window.speechSynthesis.speak(utterance);
        } else {
            console.error("TTS not supported in this browser.");
        }
    };

    useEffect(() => {
        const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
        const wsUrl = `${protocol}://localhost:8000/ws/stream/client-1`;
        socketRef.current = new WebSocket(wsUrl);

        socketRef.current.onopen = () => {
            console.log('Connected to Backend Stream');
            onStatusChange?.('Connected to Server');
        };

        socketRef.current.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'transcript') {
                    const now = Date.now();
                    const elapsed = sessionStartTime ? Math.floor((now - sessionStartTime) / 1000) : 0;
                    const timeStr = formatTime(elapsed);
                    setTranscriptLog(prev => [...prev, { time: timeStr, text: data.text, type: 'audio' }]);

                } else if (data.type === 'visual_log') {
                    const now = Date.now();
                    const elapsed = sessionStartTime ? Math.floor((now - sessionStartTime) / 1000) : 0;
                    const timeStr = formatTime(elapsed);
                } else if (data.type === 'visual_log') {
                    const now = Date.now();
                    const elapsed = sessionStartTime ? Math.floor((now - sessionStartTime) / 1000) : 0;
                    const timeStr = formatTime(elapsed);
                    setVisualLog(prev => [...prev, { time: timeStr, text: data.text, type: 'visual', image: data.image }]);
                    // Do NOT add to transcriptLog

                } else if (data.type === 'evaluation') {
                    // Speak the feedback to "reply" to the user
                    if (data.payload?.feedback) {
                        speakText(data.payload.feedback);
                    }
                } else if (data.type === 'question') {
                    const qText = data.payload.question_text;
                    setCurrentQuestion(qText);
                    speakText(qText); // Trigger TTS
                } else if (data.type === 'report') {
                    setReport(data.payload);
                    onStatusChange?.('Report Received');
                }
            } catch (e) {
                console.error("Error parsing message", e);
            }
        };

        socketRef.current.onclose = () => {
            console.log('Disconnected from Backend');
            onStatusChange?.('Disconnected');
        };

        return () => {
            socketRef.current?.close();
        };
    }, [onStatusChange, sessionStartTime]);

    const [jobDescription, setJobDescription] = useState<string>("");

    const startCapture = async () => {
        setReport(null);
        setTranscriptLog([]);
        setVisualLog([]);
        setCurrentQuestion(null);
        setSessionStartTime(Date.now());

        if (socketRef.current?.readyState === WebSocket.OPEN) {
            // JD sending moved to after stream acquisition
        }

        try {
            const screenStream = await navigator.mediaDevices.getDisplayMedia({
                video: { width: { ideal: 1920 }, height: { ideal: 1080 }, frameRate: { ideal: 30 } },
                audio: true
            });

            const micStream = await navigator.mediaDevices.getUserMedia({ audio: true });

            const combinedStream = new MediaStream([
                ...screenStream.getVideoTracks(),
                ...micStream.getAudioTracks()
            ]);

            mediaStreamRef.current = combinedStream;

            if (videoRef.current) {
                videoRef.current.srcObject = combinedStream;
            }

            setIsCapturing(true);
            onStatusChange?.('Presenting...');

            startFrameExtraction(screenStream.getVideoTracks()[0]);
            startAudioStreaming(micStream);

            // Send JD ONLY after successful stream acquisition
            if (socketRef.current?.readyState === WebSocket.OPEN && jobDescription.trim()) {
                console.log("Sending Job Description...");
                socketRef.current.send(JSON.stringify({ type: 'job_description', payload: jobDescription }));
            }

        } catch (err) {
            console.error("Error starting capture:", err);
            onStatusChange?.('Error starting capture');
        }
    };

    const submitAnswer = () => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify({ type: 'submit_answer', payload: "" })); // Payload empty to use buffer
            setCurrentQuestion(null); // Clear question from UI
        }
    };

    const startAudioStreaming = (stream: MediaStream) => {
        isRecordingRef.current = true;
        const options = { mimeType: 'audio/webm' };

        // VAD Setup
        const audioContext = new AudioContext();
        const source = audioContext.createMediaStreamSource(stream);
        const analyser = audioContext.createAnalyser();
        analyser.fftSize = 256;
        source.connect(analyser);
        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        let hasSpeech = false;
        const SPEECH_THRESHOLD = 20;

        const checkVolume = () => {
            if (!isRecordingRef.current) return;
            analyser.getByteFrequencyData(dataArray);
            const volume = dataArray.reduce((src, a) => src + a, 0) / bufferLength;
            if (volume > SPEECH_THRESHOLD) hasSpeech = true;
            requestAnimationFrame(checkVolume);
        };
        checkVolume();

        const recordSegment = () => {
            if (!isRecordingRef.current) {
                audioContext.close();
                return;
            }
            try {
                hasSpeech = false;
                const recorder = new MediaRecorder(stream, options);
                const chunks: Blob[] = [];

                recorder.ondataavailable = (e) => {
                    if (e.data.size > 0) chunks.push(e.data);
                };

                recorder.onstop = () => {
                    const blob = new Blob(chunks, { type: 'audio/webm' });
                    if (hasSpeech && blob.size > 0 && socketRef.current?.readyState === WebSocket.OPEN) {
                        const reader = new FileReader();
                        reader.onloadend = () => {
                            const base64data = reader.result as string;
                            socketRef.current?.send(JSON.stringify({ type: 'audio', payload: base64data, timestamp: Date.now() }));
                        };
                        reader.readAsDataURL(blob);
                    }
                    if (isRecordingRef.current) recordSegment();
                };

                recorder.start();
                audioRecorderRef.current = recorder;
                setTimeout(() => {
                    if (recorder.state === "recording") recorder.stop();
                }, 1500);
            } catch (e) {
                console.error(e);
                isRecordingRef.current = false;
                audioContext.close();
            }
        };
        recordSegment();
    };

    const startFrameExtraction = (videoTrack: MediaStreamTrack) => {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const video = document.createElement('video');
        const processingStream = new MediaStream([videoTrack]);
        video.srcObject = processingStream;
        video.play();

        intervalRef.current = window.setInterval(() => {
            if (!ctx || video.videoWidth === 0) return;
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            ctx.drawImage(video, 0, 0);
            const frameData = canvas.toDataURL('image/jpeg', 0.7);
            if (socketRef.current?.readyState === WebSocket.OPEN) {
                socketRef.current.send(JSON.stringify({ type: 'video', payload: frameData, timestamp: Date.now() }));
            }
        }, 1000);
    };

    const stopCapture = () => {
        window.speechSynthesis.cancel(); // Stop speaking immediately
        isRecordingRef.current = false;
        if (socketRef.current?.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify({ type: 'end_session' }));
        }
        if (mediaStreamRef.current) mediaStreamRef.current.getTracks().forEach(track => track.stop());
        if (audioRecorderRef.current && audioRecorderRef.current.state !== "inactive") audioRecorderRef.current.stop();
        if (intervalRef.current) clearInterval(intervalRef.current);
        setIsCapturing(false);
        onStatusChange?.('Stopped. Generating Report...');
    };

    return (
        <div style={{ display: 'flex', gap: '20px', height: '100%' }}>
            {/* Left Side: Video & Controls (65%) */}
            <div className="glass-panel" style={{ flex: 65, padding: '20px', display: 'flex', flexDirection: 'column', position: 'relative' }}>
                <div style={{ marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>

                    {!isCapturing && (
                        <textarea
                            placeholder="Paste Job Description / Context here for the AI..."
                            value={jobDescription}
                            onChange={(e) => setJobDescription(e.target.value)}
                            style={{
                                flex: 1, marginRight: '10px', height: '44px', padding: '10px',
                                borderRadius: '8px', border: '1px solid var(--border-color)',
                                background: 'rgba(0,0,0,0.2)', color: 'white', resize: 'none',
                                fontFamily: 'inherit'
                            }}
                        />
                    )}

                    {/* AI Question - Integrated in Controls */}
                    {isCapturing && currentQuestion && (
                        <div className="glass-panel animate-fade-in" style={{
                            flex: 1, marginRight: '15px', padding: '8px 15px',
                            background: 'rgba(99, 102, 241, 0.1)', border: '1px solid var(--primary)',
                            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                            borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
                        }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: 1, minWidth: 0 }}>
                                <span style={{ color: 'var(--primary)', fontWeight: 'bold', fontSize: '1.2rem', whiteSpace: 'nowrap' }}>AI:</span>
                                <span style={{
                                    fontSize: '1rem',
                                    maxHeight: '60px',
                                    overflowY: 'auto',
                                    whiteSpace: 'normal',
                                    paddingRight: '5px' // Space for scrollbar
                                }}>
                                    {currentQuestion}
                                </span>
                            </div>
                            <button onClick={submitAnswer} className="btn-primary" style={{ padding: '6px 16px', fontSize: '0.85rem', whiteSpace: 'nowrap' }}>
                                Done
                            </button>
                        </div>
                    )}

                    {!isCapturing ? (
                        <button onClick={startCapture} className="btn-primary" style={{ height: '44px' }}>
                            Start Interview
                        </button>
                    ) : (
                        <button onClick={stopCapture} className="btn-danger" style={{ height: '44px' }}>
                            End Session
                        </button>
                    )}
                </div>

                <div style={{ flex: 1, background: '#000', borderRadius: '8px', overflow: 'hidden', position: 'relative', border: '1px solid var(--border-color)' }}>
                    <video ref={videoRef} autoPlay muted playsInline
                        style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                    />

                    {/* Live Indicator */}
                    {isCapturing && (
                        <div style={{
                            position: 'absolute', top: '15px', left: '15px',
                            background: 'rgba(239, 68, 68, 0.9)', color: 'white',
                            padding: '4px 10px', borderRadius: '4px', fontSize: '0.8rem', fontWeight: 'bold'
                        }}>
                            LIVE
                        </div>
                    )}
                </div>
            </div>

            {/* Right Side: Log & Visuals (35%) */}
            <div className="glass-panel" style={{ flex: 35, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                <div style={{ padding: '15px 20px', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h3 style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>SESSION HISTORY</h3>
                    <div style={{ display: 'flex', gap: '8px', background: 'rgba(0,0,0,0.2)', padding: '4px', borderRadius: '6px' }}>
                        <button
                            onClick={() => setViewMode('transcript')}
                            style={{
                                padding: '4px 12px', fontSize: '0.8rem',
                                background: viewMode === 'transcript' ? 'var(--primary)' : 'transparent',
                                color: viewMode === 'transcript' ? 'white' : 'var(--text-muted)',
                                borderRadius: '4px'
                            }}
                        >
                            Transcript
                        </button>
                        <button
                            onClick={() => setViewMode('visuals')}
                            style={{
                                padding: '4px 12px', fontSize: '0.8rem',
                                background: viewMode === 'visuals' ? 'var(--primary)' : 'transparent',
                                color: viewMode === 'visuals' ? 'white' : 'var(--text-muted)',
                                borderRadius: '4px'
                            }}
                        >
                            Visuals
                        </button>
                    </div>
                </div>

                <div className="log-container" style={{ flex: 1, overflowY: 'auto', padding: '20px' }}>
                    {transcriptLog.length === 0 && (
                        <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                            Waiting for session to start...
                        </div>
                    )}

                    {viewMode === 'transcript' ? (
                        transcriptLog.map((entry, index) => (
                            <div key={index} style={{ marginBottom: '15px', animation: 'fadeIn 0.3s ease' }}>
                                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>[{entry.time}]</div>
                                {entry.type === 'visual' ? (
                                    <div style={{ color: '#60a5fa', fontStyle: 'italic', paddingLeft: '10px', borderLeft: '2px solid #60a5fa' }}>
                                        📷 {entry.text}
                                    </div>
                                ) : (
                                    <div style={{ lineHeight: '1.5' }}>{entry.text}</div>
                                )}
                            </div>
                        ))
                    ) : (
                        <VisualGallery entries={visualLog} />
                    )}
                    <div style={{ float: "left", clear: "both" }} ></div>
                </div>
            </div>

            {/* Report Overlay */}
            {report && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(5px)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100
                }}>
                    <div className="glass-panel" style={{ width: '800px', maxHeight: '90vh', overflowY: 'auto', padding: '40px', background: '#0f172a' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
                            <h2 style={{ fontSize: '2rem', color: 'var(--primary)' }}>Interview Report</h2>
                            <button onClick={() => setReport(null)} style={{ color: 'var(--text-muted)', background: 'transparent', fontSize: '1.5rem' }}>×</button>
                        </div>
                        <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'var(--font-family)', lineHeight: '1.6', color: '#e2e8f0' }}>{report}</pre>
                    </div>
                </div>
            )}
        </div>
    );
};

// Sub-component for Visual Gallery (Grid View)
const VisualGallery: React.FC<{ entries: any[] }> = ({ entries }) => {
    const [selectedEntry, setSelectedEntry] = useState<any | null>(null);

    if (entries.length === 0) {
        return <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>No visuals captured yet.</div>;
    }

    return (
        <div style={{ padding: '10px' }}>
            {/* Grid View */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: '15px' }}>
                {entries.map((entry, idx) => (
                    <div key={idx}
                        onClick={() => setSelectedEntry(entry)}
                        className="animate-fade-in"
                        style={{
                            cursor: 'pointer', border: '1px solid var(--border-color)', borderRadius: '8px',
                            overflow: 'hidden', background: 'rgba(255,255,255,0.05)', transition: 'transform 0.2s'
                        }}
                    >
                        <div style={{ height: '100px', width: '100%', overflow: 'hidden', background: '#000' }}>
                            <img src={entry.image} alt="Frame" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                        </div>
                        <div style={{ padding: '8px', fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'center' }}>
                            {entry.time}
                        </div>
                    </div>
                ))}
            </div>

            {/* Modal for Full View */}
            {selectedEntry && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 200,
                    background: 'rgba(0,0,0,0.9)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                    padding: '40px'
                }}>
                    <button
                        onClick={() => setSelectedEntry(null)}
                        style={{ position: 'absolute', top: '20px', right: '30px', background: 'transparent', color: 'white', fontSize: '2rem', border: 'none', cursor: 'pointer' }}
                    >
                        &times;
                    </button>

                    <div style={{ maxHeight: '70vh', maxWidth: '90vw', marginBottom: '20px', border: '1px solid var(--primary)', borderRadius: '8px', overflow: 'hidden' }}>
                        <img src={selectedEntry.image} alt="Full Frame" style={{ maxHeight: '70vh', maxWidth: '100%', objectFit: 'contain' }} />
                    </div>

                    <div className="glass-panel" style={{ maxWidth: '800px', width: '100%', padding: '20px', maxHeight: '150px', overflowY: 'auto' }}>
                        <div style={{ color: 'var(--primary)', marginBottom: '5px', fontSize: '0.9rem' }}>Analyzed at {selectedEntry.time}</div>
                        <div style={{ fontSize: '1rem', lineHeight: '1.5' }}>{selectedEntry.text.replace("Visual Context: ", "")}</div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default MediaCapture;

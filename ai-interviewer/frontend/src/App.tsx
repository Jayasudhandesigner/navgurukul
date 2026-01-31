import { useState } from 'react'
import './App.css'
import MediaCapture from './components/MediaCapture'

function App() {
  const [status, setStatus] = useState("Idle");

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '20px', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header className="glass-panel" style={{
        padding: '20px 30px',
        marginBottom: '20px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <div style={{ width: '40px', height: '40px', background: 'linear-gradient(135deg, #6366f1, #a855f7)', borderRadius: '8px' }}></div>
          <h1 style={{ fontSize: '1.5rem', background: 'linear-gradient(to right, #fff, #94a3b8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            AI Interviewer <span style={{ opacity: 0.5, fontWeight: 400 }}>& Coach</span>
          </h1>
        </div>
        <div style={{
          padding: '8px 16px',
          background: 'rgba(99, 102, 241, 0.1)',
          color: '#818cf8',
          borderRadius: '20px',
          fontSize: '0.9rem',
          fontWeight: 600,
          border: '1px solid rgba(99, 102, 241, 0.2)'
        }}>
          Status: {status}
        </div>
      </header>

      <main style={{ flex: 1, overflow: 'hidden' }}>
        <MediaCapture onStatusChange={setStatus} />
      </main>
    </div>
  )
}

export default App

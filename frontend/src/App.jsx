import React, { useState, useRef, useEffect } from 'react';
import { summarizeVideo, chatWithVideo } from './services/api';
import '../src/index.css';

/* ─────────────────────────────────────────
   BACKGROUND SHAPES (replacing Tailwind hero)
───────────────────────────────────────── */
function BgCanvas() {
  return (
    <>
      <div className="glow-top" />
      <div className="glow-bottom" />
      <div className="bg-canvas">
        <div className="shape shape-1" />
        <div className="shape shape-2" />
        <div className="shape shape-3" />
        <div className="shape shape-4" />
      </div>
    </>
  );
}

/* ─────────────────────────────────────────
   SVG ICONS
───────────────────────────────────────── */
const PlayIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
    <path d="M8 5v14l11-7z"/>
  </svg>
);
const SparkleIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6z"/>
  </svg>
);
const SendIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
  </svg>
);
const CopyIcon = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
  </svg>
);
const CheckIcon = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#4ade80" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12"/>
  </svg>
);
const BotIcon = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="11" width="18" height="11" rx="2"/><path d="M12 2v4M8 7h8M9 11v4M15 11v4"/>
  </svg>
);
const UserIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/>
  </svg>
);

/* ─────────────────────────────────────────
   SUMMARY CARD
───────────────────────────────────────── */
function SummaryCard({ summary }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(summary);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <div className="glass-card" style={{ height: '520px', display: 'flex', flexDirection: 'column' }}>
      <div className="card-header">
        <span className="card-title">✨ AI Summary</span>
        <button className="copy-btn" onClick={handleCopy}>
          {copied ? <CheckIcon /> : <CopyIcon />}
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>
      <div className="card-body" style={{ overflowY: 'auto', flex: 1 }}>
        <p className="summary-text">{summary}</p>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────
   CHAT CARD
───────────────────────────────────────── */
function ChatCard({ onSendMessage }) {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'ai', content: "Hi! I've analyzed the video. Ask me anything about it!" }
  ]);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const query = input.trim();
    setInput('');
    const withUser = [...messages, { role: 'user', content: query }];
    setMessages([...withUser, { role: 'ai', content: null, typing: true }]);
    setLoading(true);
    try {
      const answer = await onSendMessage(query);
      setMessages([...withUser, { role: 'ai', content: answer }]);
    } catch {
      setMessages([...withUser, { role: 'ai', content: 'Sorry, something went wrong.', error: true }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-card chat-card">
      <div className="card-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div className="avatar ai"><BotIcon /></div>
          <div>
            <div className="card-title">Chat with Video</div>
            <div className="rag-badge">RAG Pipeline Active</div>
          </div>
        </div>
      </div>
      <div className="card-body">
        {messages.map((msg, i) => (
          <div key={i} className={`msg-row ${msg.role}`}>
            <div className={`avatar ${msg.role}`}>
              {msg.role === 'ai' ? <BotIcon /> : <UserIcon />}
            </div>
            <div className={`bubble ${msg.role}${msg.error ? ' error' : ''}`}>
              {msg.typing ? (
                <div className="typing-dots">
                  <span /><span /><span />
                </div>
              ) : msg.content}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      <div className="chat-footer">
        <form className="chat-input-row" onSubmit={handleSend}>
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Ask anything about the video..."
            disabled={loading}
          />
          <button type="submit" className="send-btn" disabled={!input.trim() || loading}>
            <SendIcon />
          </button>
        </form>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────
   MAIN APP
───────────────────────────────────────── */
function extractVideoId(url) {
  try {
    if (url.includes('youtube.com/watch')) return new URLSearchParams(new URL(url).search).get('v');
    if (url.includes('youtu.be/')) return url.split('youtu.be/')[1].split('?')[0];
    return null;
  } catch { return null; }
}

export default function App() {
  const [url, setUrl] = useState('');
  const [videoId, setVideoId] = useState('');
  const [activeUrl, setActiveUrl] = useState('');
  const [summary, setSummary] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url.trim()) return;
    setError('');
    setLoading(true);
    setSummary('');
    setVideoId('');
    setActiveUrl(url.trim());
    const id = extractVideoId(url.trim());
    if (id) setVideoId(id);
    try {
      const data = await summarizeVideo(url.trim());
      setSummary(data.summary);
      if (!id && data.video_id) setVideoId(data.video_id);
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong — please try another video.');
    } finally {
      setLoading(false);
    }
  };

  const handleChat = async (query) => {
    const data = await chatWithVideo(activeUrl, query);
    return data.answer;
  };

  const showResults = (summary || videoId) && !loading;

  return (
    <div className="app">
      <BgCanvas />

      {/* ── HERO ── */}
      <div className="hero">
        <div className="hero-badge">
          <PlayIcon />
          <SparkleIcon />
          <span>AgentTube AI · RAG Powered</span>
        </div>
        <h1>
          <span className="line1">Elevate Your Video</span>
          <span className="line2">Experience with AI</span>
        </h1>
        <p>
          Paste any YouTube URL to instantly get a comprehensive summary
          and ask questions with bot.
        </p>
      </div>

      {/* ── URL INPUT ── */}
      <div className="url-form">
        <label className="url-form-label">Paste your YouTube link here</label>
        <div className="input-glow-wrapper">
          <form className="url-input-row" onSubmit={handleSubmit}>
            <input
              type="url"
              value={url}
              onChange={e => setUrl(e.target.value)}
              placeholder="https://youtube.com/watch?v=..."
              required
              disabled={loading}
            />
            <button type="submit" className="summarize-btn" disabled={loading || !url.trim()}>
              {loading ? (
                <>
                  <div className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
                  Processing...
                </>
              ) : (
                <>✨ Summarize</>
              )}
            </button>
          </form>
        </div>
      </div>

      {/* ── ERROR ── */}
      {error && <div className="error-banner">⚠️ {error}</div>}

      {/* ── LOADING ── */}
      {loading && (
        <div className="loader-wrap">
          <div className="spinner" />
          <p>Analyzing transcript &amp; building RAG index…</p>
        </div>
      )}

      {/* ── RESULTS ── */}
      {showResults && (
        <div className="results">
          {videoId && (
            <div className="video-wrap">
              <iframe
                src={`https://www.youtube.com/embed/${videoId}`}
                title="YouTube video"
                frameBorder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            </div>
          )}
          <div className="result-grid">
            <SummaryCard summary={summary} />
            <ChatCard onSendMessage={handleChat} />
          </div>
        </div>
      )}
    </div>
  );
}

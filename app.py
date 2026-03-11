import streamlit as st
import streamlit.components.v1 as components
import re
from summarizer_logic import run_summarization

# ─────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="YouTube Video Summarizer",
    page_icon="🎥",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────
# MATRIX BACKGROUND via st.components.v1.html()
# Streamlit strips <script> from st.markdown — scripts only execute
# inside components.html() which renders an unrestricted iframe.
# We position the iframe fixed/full-screen behind everything with CSS.
# ─────────────────────────────────────────────────────────────────
MATRIX_HTML = """
<!DOCTYPE html>
<html>
<head>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  html, body { width: 100%; height: 100%; overflow: hidden; background: transparent; }
  canvas { display: block; }
</style>
</head>
<body>
<canvas id="c"></canvas>
<script>
  const canvas = document.getElementById('c');
  const ctx    = canvas.getContext('2d');

  const CHARS = ('ABCDEFアイウエオカキクケコサシスセソ01アカサタナハマヤラワΩ∑∆∞≠01{}[]<>/\\\\|=+-*#@!?;').split('');
  const FONT_SIZE = 15;
  const COLORS    = ['#00aaff','#00ccff','#0088dd','#33bbff','#00eeff','#0055cc'];

  let cols, drops, colColors, speeds;

  function resize() {
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
    cols      = Math.floor(canvas.width / FONT_SIZE);
    drops     = Array.from({ length: cols }, () => Math.random() * -(canvas.height / FONT_SIZE));
    colColors = Array.from({ length: cols }, () => COLORS[Math.floor(Math.random() * COLORS.length)]);
    speeds    = Array.from({ length: cols }, () => 0.3 + Math.random() * 0.55);
  }

  function draw() {
    ctx.fillStyle = 'rgba(2, 9, 18, 0.048)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.font = FONT_SIZE + 'px monospace';

    for (let i = 0; i < drops.length; i++) {
      const char = CHARS[Math.floor(Math.random() * CHARS.length)];
      const y    = drops[i] * FONT_SIZE;

      // Bright leading head
      if (Math.random() > 0.92) {
        ctx.fillStyle    = '#aaddff';
        ctx.shadowColor  = '#ffffff';
        ctx.shadowBlur   = 10;
        ctx.globalAlpha  = 1.0;
      } else {
        ctx.fillStyle    = colColors[i];
        ctx.shadowColor  = colColors[i];
        ctx.shadowBlur   = 5;
        ctx.globalAlpha  = 0.35 + Math.random() * 0.65;
      }

      ctx.fillText(char, i * FONT_SIZE, y);
      ctx.globalAlpha = 1.0;
      ctx.shadowBlur  = 0;

      if (y > canvas.height && Math.random() > 0.97) {
        drops[i]     = 0;
        colColors[i] = COLORS[Math.floor(Math.random() * COLORS.length)];
        speeds[i]    = 0.3 + Math.random() * 0.55;
      }
      drops[i] += speeds[i];
    }
  }

  resize();
  window.addEventListener('resize', resize);
  setInterval(draw, 38);
</script>
</body>
</html>
"""

# Inject the iframe — height=0 makes it take no layout space,
# the CSS below makes it cover the full viewport behind everything.
components.html(MATRIX_HTML, height=0, scrolling=False)

# ─────────────────────────────────────────────────────────────────
# GLOBAL CSS
# Target the iframe rendered by components.html and push it
# to fixed full-screen behind all Streamlit content (z-index: -1).
# ─────────────────────────────────────────────────────────────────
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700;900&family=Exo+2:wght@300;400;600&display=swap" rel="stylesheet">

<style>
/* ── Force dark background on every Streamlit layer ── */
html, body,
[data-testid="stApp"],
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
section.main,
.stMainBlockContainer,
[data-testid="block-container"] {
    background: #020912 !important;
    background-color: #020912 !important;
}

/* ── Position the components iframe as a fixed full-screen backdrop ── */
iframe[title="st_components_v1.html.html"] {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    border: none !important;
    z-index: 0 !important;
    pointer-events: none !important;
    opacity: 1 !important;
}

/* ── All Streamlit content above the canvas ── */
[data-testid="block-container"] {
    position: relative;
    z-index: 10;
    max-width: 780px !important;
    padding-top: 2.5rem !important;
    padding-bottom: 5rem !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] { display: none !important; }

/* ── Scanline CRT atmosphere ── */
body::after {
    content: '';
    position: fixed;
    inset: 0;
    background: repeating-linear-gradient(
        0deg, transparent, transparent 3px,
        rgba(0,8,18,0.06) 3px, rgba(0,8,18,0.06) 4px
    );
    pointer-events: none;
    z-index: 5;
}

/* ══════════════ HEADER ══════════════ */
.yt-badge {
    display: inline-block;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.28em;
    color: #00aaff;
    border: 1px solid rgba(0,170,255,0.3);
    background: rgba(0,170,255,0.07);
    padding: 0.28rem 1rem;
    border-radius: 2px;
    text-transform: uppercase;
    margin-bottom: 1.1rem;
}
.yt-title {
    font-family: 'Orbitron', sans-serif;
    font-weight: 900;
    font-size: 2.6rem;
    color: #dff0ff;
    letter-spacing: 0.04em;
    line-height: 1.15;
    margin: 0 0 0.6rem 0;
    text-shadow: 0 0 40px rgba(0,170,255,0.45), 0 0 100px rgba(0,100,200,0.2);
}
.yt-title em { color: #00aaff; font-style: normal; }
.yt-subtitle {
    font-family: 'Exo 2', sans-serif;
    font-weight: 300;
    font-size: 1rem;
    color: rgba(150,200,240,0.65);
    letter-spacing: 0.07em;
    margin: 0;
}
.header-wrap { text-align: center; margin-bottom: 2.2rem; }

/* ══════════════ GLASS CARD ══════════════ */
.glass-card {
    background: rgba(4, 16, 32, 0.78);
    border: 1px solid rgba(0,170,255,0.16);
    border-radius: 14px;
    padding: 2rem 2.2rem 2.2rem;
    backdrop-filter: blur(22px) saturate(150%);
    -webkit-backdrop-filter: blur(22px) saturate(150%);
    box-shadow:
        0 0 0 1px rgba(0,170,255,0.05),
        0 10px 50px rgba(0,0,0,0.6),
        0 0 90px rgba(0,90,180,0.07) inset;
    position: relative;
    overflow: hidden;
}
.glass-card::before {
    content: '';
    position: absolute;
    top: 0; left: 10%; right: 10%;
    height: 1px;
    background: linear-gradient(90deg,
        transparent, rgba(0,170,255,0.6) 40%,
        rgba(100,220,255,0.9) 50%,
        rgba(0,170,255,0.6) 60%, transparent);
}
.glass-card::after {
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(ellipse at 50% 0%, rgba(0,120,220,0.06) 0%, transparent 65%);
    pointer-events: none;
}

/* ── Field label ── */
.field-label {
    display: block;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.22em;
    color: #00aaff;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}

/* ── Streamlit text input override ── */
[data-testid="stTextInput"] > div > div {
    background: rgba(0,12,28,0.85) !important;
    border: 1px solid rgba(0,170,255,0.28) !important;
    border-radius: 7px !important;
}
[data-testid="stTextInput"] input {
    background: transparent !important;
    border: none !important;
    color: #b8deff !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.87rem !important;
    letter-spacing: 0.03em;
    caret-color: #00aaff;
}
[data-testid="stTextInput"] input:focus {
    box-shadow: none !important;
    outline: none !important;
}
[data-testid="stTextInput"] > div > div:focus-within {
    border-color: rgba(0,170,255,0.65) !important;
    box-shadow: 0 0 0 3px rgba(0,170,255,0.1), 0 0 25px rgba(0,170,255,0.08) !important;
}
[data-testid="stTextInput"] input::placeholder { color: rgba(80,140,190,0.4) !important; }
[data-testid="stTextInput"] label { display: none !important; }

/* ── Button ── */
[data-testid="stButton"] > button {
    width: 100% !important;
    margin-top: 1.1rem !important;
    padding: 0.8rem 2rem !important;
    background: linear-gradient(135deg, #0055bb 0%, #0088ee 45%, #00aaff 100%) !important;
    border: 1px solid rgba(0,180,255,0.4) !important;
    border-radius: 7px !important;
    color: #ffffff !important;
    font-family: 'Orbitron', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 28px rgba(0,140,255,0.3), 0 1px 0 rgba(255,255,255,0.08) inset !important;
}
[data-testid="stButton"] > button:hover {
    background: linear-gradient(135deg, #0066cc 0%, #009aff 45%, #22ccff 100%) !important;
    box-shadow: 0 6px 40px rgba(0,170,255,0.5), 0 0 70px rgba(0,170,255,0.12) !important;
    transform: translateY(-2px) !important;
    border-color: rgba(0,200,255,0.6) !important;
}
[data-testid="stButton"] > button:active {
    transform: translateY(0px) !important;
}

/* ── Spinner ── */
[data-testid="stSpinner"] > div {
    color: #00aaff !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.1em;
}
[data-testid="stSpinner"] svg circle { stroke: #00aaff !important; }

/* ══════════════ RESULT CARD ══════════════ */
.result-wrap {
    margin-top: 1.8rem;
    background: rgba(2, 12, 26, 0.88);
    border: 1px solid rgba(0,170,255,0.18);
    border-radius: 12px;
    padding: 1.8rem 2rem;
    backdrop-filter: blur(14px);
    position: relative;
    overflow: hidden;
}
.result-wrap::before {
    content: '';
    position: absolute;
    top: 0; left: 8%; right: 8%;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0,170,255,0.5), transparent);
}
.res-tag {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.28em;
    color: #00aaff;
    text-transform: uppercase;
    margin-bottom: 1.1rem;
    display: flex;
    align-items: center;
    gap: 0.7rem;
}
.res-tag::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(0,170,255,0.35), transparent);
}
.res-body {
    color: #c0ddf5;
    font-family: 'Exo 2', sans-serif;
    font-size: 0.97rem;
    line-height: 1.8;
    font-weight: 400;
}
.res-body h2 {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.78rem;
    letter-spacing: 0.2em;
    color: #00ccff;
    text-transform: uppercase;
    margin: 1.5rem 0 0.6rem 0;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid rgba(0,170,255,0.15);
}
.res-body ul { padding-left: 1.3rem; margin: 0.4rem 0; }
.res-body li { margin-bottom: 0.4rem; }
.res-body strong { color: #7dd3fc; font-weight: 600; }
.res-body p { margin-bottom: 0.7rem; }

/* ── Error card ── */
.err-card {
    margin-top: 1.5rem;
    background: rgba(35, 4, 4, 0.75);
    border: 1px solid rgba(220, 50, 50, 0.28);
    border-radius: 9px;
    padding: 1.1rem 1.5rem;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.8rem;
    color: #ff7070;
    letter-spacing: 0.04em;
    line-height: 1.65;
}

/* ── Footer ── */
.yt-footer {
    text-align: center;
    margin-top: 2.8rem;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 0.22em;
    color: rgba(0,140,200,0.22);
    text-transform: uppercase;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-wrap">
  <div class="yt-badge">⬡ &nbsp; AI · CrewAI · Gemini · v2.0</div>
  <h1 class="yt-title">🎥 YouTube<br><em>Video Summarizer</em></h1>
  <p class="yt-subtitle">Paste a YouTube video link below and get an AI-generated summary.</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# INPUT GLASS CARD
# ─────────────────────────────────────────────────────────────────
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown('<span class="field-label">⬡ &nbsp; YouTube Video URL</span>', unsafe_allow_html=True)

url = st.text_input(
    label="url",
    placeholder="https://www.youtube.com/watch?v=...",
    key="yt_url",
    label_visibility="collapsed",
)

generate = st.button("⟶ &nbsp; Generate Summary", key="gen_btn")
st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# LOGIC
# ─────────────────────────────────────────────────────────────────
if generate:
    raw = (url or "").strip()

    if not raw:
        st.markdown('<div class="err-card">⚠ &nbsp; No URL detected — please paste a YouTube link above.</div>', unsafe_allow_html=True)

    elif "youtube.com" not in raw and "youtu.be" not in raw:
        st.markdown('<div class="err-card">⚠ &nbsp; That does not look like a YouTube URL. Please check and try again.</div>', unsafe_allow_html=True)

    else:
        with st.spinner("⟳  AI agents are analyzing the video..."):
            try:
                result      = run_summarization(raw)
                result_text = str(result).strip()

                is_error = (
                    result_text.startswith("Summary cannot be generated") or
                    result_text.startswith("Transcript Error") or
                    result_text.startswith("**Error")
                )

                if is_error:
                    st.markdown(f'<div class="err-card">⚠ &nbsp; {result_text}</div>', unsafe_allow_html=True)
                else:
                    # Light markdown → HTML conversion
                    styled = result_text
                    styled = re.sub(r'^#{1,2} (.+)$',  r'<h2>\1</h2>', styled, flags=re.MULTILINE)
                    styled = re.sub(r'^#{3,} (.+)$',   r'<h2>\1</h2>', styled, flags=re.MULTILINE)
                    styled = re.sub(r'\*\*(.+?)\*\*',  r'<strong>\1</strong>', styled)
                    styled = re.sub(r'^\* (.+)$',       r'<li>\1</li>', styled, flags=re.MULTILINE)
                    styled = re.sub(r'^- (.+)$',        r'<li>\1</li>', styled, flags=re.MULTILINE)
                    styled = re.sub(r'(<li>.*</li>\n?)+', lambda m: f'<ul>{m.group(0)}</ul>', styled)
                    styled = re.sub(r'\n\n+', '</p><p>', styled)
                    styled = f'<p>{styled}</p>'

                    st.markdown(f"""
                    <div class="result-wrap">
                      <div class="res-tag">▸ &nbsp; Summary Output</div>
                      <div class="res-body">{styled}</div>
                    </div>
                    """, unsafe_allow_html=True)

            except Exception as exc:
                st.markdown(f'<div class="err-card">✖ &nbsp; Unexpected error:<br><br>{exc}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="yt-footer">
  Powered by CrewAI &nbsp;·&nbsp; Gemini 2.5 Flash &nbsp;·&nbsp; youtube-transcript-api
</div>
""", unsafe_allow_html=True)
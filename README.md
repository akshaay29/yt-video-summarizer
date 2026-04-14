# AgentTube AI 🎬🤖

A production-grade AI application to **summarize YouTube videos** and **chat with their content** using a RAG (Retrieval-Augmented Generation) pipeline powered by Google Gemini.

---

## ✨ Features

- 🎯 Paste any YouTube URL and get an instant AI-generated summary
- 🤖 Chat with the video using RAG (FAISS + Google Gemini Embeddings)
- 🌍 Supports videos in any language (summarized in English)
- 🎨 Beautiful dark UI with animated floating shapes
- ⚡ FastAPI backend + React frontend

---

## 🧱 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite + Pure CSS |
| Backend | FastAPI (Python) |
| AI / LLM | Google Gemini 2.5 Flash |
| RAG | LangChain + FAISS |
| Transcripts | youtube-transcript-api |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- A [Google Gemini API Key](https://aistudio.google.com/app/apikey)

---

### 1. Clone the repo
```bash
git clone https://github.com/akshaay29/yt-video-summarizer.git
cd yt-video-summarizer
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it (Windows PowerShell)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo GOOGLE_API_KEY=your_api_key_here > .env

# Start the server
uvicorn main:app --reload
```
Backend runs at: `http://localhost:8000`

---

### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```
Frontend runs at: `http://localhost:5173`

---

## 📁 Project Structure

```
├── backend/
│   ├── main.py                  # FastAPI app (routes)
│   ├── requirements.txt
│   ├── .env                     # Your API key (not committed)
│   └── services/
│       ├── transcript_loader.py # YouTube transcript extraction
│       ├── summarizer.py        # Gemini summarization
│       └── rag_pipeline.py      # FAISS + RAG chat
│
└── frontend/
    ├── src/
    │   ├── App.jsx              # Main app component
    │   ├── index.css            # All styles (pure CSS)
    │   └── services/
    │       └── api.js           # Axios API calls
    └── package.json
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/summarize` | Extract transcript + generate summary + build RAG index |
| POST | `/chat` | Answer query using RAG pipeline |

---

## ⚙️ Environment Variables

Create `backend/.env`:
```
GOOGLE_API_KEY=your_gemini_api_key_here
```

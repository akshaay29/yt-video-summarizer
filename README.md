<div align="center">
  <img src="https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/React-Dark.svg" width="60" />
  <img src="https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/Vite-Dark.svg" width="60" />
  <img src="https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/Python-Dark.svg" width="60" />
  <img src="https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/FastAPI-Dark.svg" width="60" />
  <br/>
  
  # 🚀 AgentTube AI

  **Elevate Your Video Experience with AI**
  
  [**Live Website (agentube-ai.vercel.app)**](https://agentube-ai.vercel.app/) • [**Report Bug**](https://github.com/akshaay29/yt-video-summarizer/issues)

</div>

<br/>

AgentTube AI is a production-grade application that intelligently extracts transcripts from any YouTube video and leverages the power of **Google Gemini 2.5 Flash** to provide crisp summaries and an interactive chat interface. 

It handles everything from raw extraction to advanced RAG (Retrieval-Augmented Generation) so you can directly "talk" to your videos.

## ✨ Key Features
- **🌐 Cloud-Bypass Architecture**: Intelligent multi-tiered transcript extraction (Native API -> `yt-dlp` -> Free Proxies -> Native Gemini Integration) to bypass YouTube data-center blocks.
- **🇮🇳 Multi-Language Support**: Automatically detects and processes content in Hindi, English, and other languages seamlessly.
- **🤖 Powered by Gemini 2.5**: High accuracy parsing and response generation using Google's fastest LLM.
- **💬 RAG Chatbot**: Don't just read the summary—ask specific questions about the video and get context-aware answers.
- **💎 Premium UI**: Built with React & Vite using modern Glassmorphism, animations, and beautiful dark modes.

## 🛠️ Tech Stack
* **Frontend:** React, Vite, Custom Animated CSS
* **Backend:** FastAPI, Python
* **AI/Embeddings:** Google GenAI SDK (`gemini-2.5-flash`, `gemini-embedding-001`)
* **Vector Store:** FAISS (In-Memory Document Retrieval)
* **Deployment:** Vercel (Frontend), Render (Backend)

---

## 💻 Run Locally

To get a local instance running, follow these simple steps.

### Prerequisites
- Python 3.10+
- Node.js 18+
- [Google Gemini API Key](https://aistudio.google.com/)

### 1. Start the Backend
```bash
# Navigate to backend 
cd backend

# Create a virtual environment
python -m venv venv

# Activate it (Windows)
.\venv\Scripts\activate
# Activate it (Mac/Linux)
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file and add your API Key
echo 'GOOGLE_API_KEY="your_api_key_here"' > .env

# Run the FastAPI server
uvicorn main:app --reload
```

### 2. Start the Frontend
```bash
# Open a new terminal and navigate to frontend
cd frontend

# Install packages
npm install

# Start the Vite development server
npm run dev
```
The application will launch at `http://localhost:5173`.

---

<div align="center">
  <i>Developed with ❤️ by Akshay</i>
</div>

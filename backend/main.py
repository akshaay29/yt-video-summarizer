from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv

from services.transcript_loader import load_transcript, get_video_id
from services.summarizer import generate_summary
from services.rag_pipeline import index_transcript, chat_with_video, has_index

# Load environment variables (API Key)
load_dotenv()

app = FastAPI(title="AgentTube AI API")

# Configure CORS — reads from ALLOWED_ORIGINS env var, defaults to allow all.
raw_origins = os.environ.get("ALLOWED_ORIGINS", "*")
if raw_origins == "*":
    allowed_origins = ["*"]
else:
    allowed_origins = [o.strip() for o in raw_origins.split(",")]

# Always allow this project's Vercel deployments (production + preview URLs)
# AND local dev servers, regardless of the ALLOWED_ORIGINS value. The live
# frontend origin has drifted from what ALLOWED_ORIGINS was pinned to (e.g.
# agentube-ai.vercel.app vs the older -eta URL), which silently CORS-blocked
# every browser request. Matching *.vercel.app by regex makes the backend
# resilient to that drift; the localhost / 127.0.0.1 alternatives let a
# locally-run frontend (any Vite port) talk to this deployed backend in dev.
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://([a-z0-9-]+\.)*vercel\.app|http://localhost(:\d+)?|http://127\.0\.0\.1(:\d+)?",
    # allow_credentials MUST be False here: the CORS spec forbids pairing
    # credentialed requests with a wildcard ("*") origin, and browsers reject
    # it. This app sends no cookies/credentials, so False is both correct and
    # keeps allow_origins=["*"] / the vercel regex valid.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class SummarizeRequest(BaseModel):
    video_url: str

class ChatRequest(BaseModel):
    video_url: str
    query: str

@app.get("/")
def root():
    return {"message": "Welcome to AgentTube AI API"}

@app.post("/summarize")
def summarize_video(user_req: SummarizeRequest):
    try:
        # 1. Get Transcript
        transcript_data = load_transcript(user_req.video_url)
        video_id = transcript_data["video_id"]
        text = transcript_data["text"]
        
        # 2. Generate Summary
        summary = generate_summary(text)
        
        # 3. Index Transcript for RAG
        index_transcript(video_id, text)
        
        return {
            "video_id": video_id,
            "summary": summary
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
def chat_video(user_req: ChatRequest):
    try:
        video_id = get_video_id(user_req.video_url)

        # Self-heal: the RAG index is in-memory and is lost whenever the
        # server restarts or cold-starts (Render free tier spins down after
        # ~15 min idle). If it's gone, rebuild it on demand from the
        # transcript instead of forcing the user to click Summarize again.
        if not has_index(video_id):
            transcript_data = load_transcript(user_req.video_url)
            index_transcript(transcript_data["video_id"], transcript_data["text"])

        answer = chat_with_video(video_id, user_req.query)
        return {"answer": answer}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv

from services.transcript_loader import load_transcript, get_video_id
from services.summarizer import generate_summary
from services.rag_pipeline import index_transcript, chat_with_video

# Load environment variables (API Key)
load_dotenv()

app = FastAPI(title="AgentTube AI API")

# Configure CORS — reads from ALLOWED_ORIGINS env var, defaults to allow all
raw_origins = os.environ.get("ALLOWED_ORIGINS", "*")
if raw_origins == "*":
    allowed_origins = ["*"]
else:
    allowed_origins = [o.strip() for o in raw_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
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
        answer = chat_with_video(video_id, user_req.query)
        return {"answer": answer}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

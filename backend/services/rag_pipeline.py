import os
from google import genai
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# In-memory store: video_id → FAISS vectorstore
vector_stores: dict = {}

def index_transcript(video_id: str, transcript_text: str) -> bool:
    """Chunk the transcript, embed it, and store in FAISS."""
    # 1. Split text into chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    docs = splitter.create_documents([transcript_text])

    # 2. Create embeddings using Google
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

    # 3. Build FAISS index
    vectorstore = FAISS.from_documents(docs, embeddings)
    vector_stores[video_id] = vectorstore
    return True

def chat_with_video(video_id: str, query: str) -> str:
    """Answer a query using the indexed transcript chunks + Gemini."""
    if video_id not in vector_stores:
        raise ValueError(
            "This video has not been summarized yet. "
            "Please click Summarize first to build the knowledge index."
        )

    vectorstore = vector_stores[video_id]
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    # Retrieve relevant context chunks
    relevant_docs = retriever.invoke(query)
    context = "\n\n".join([doc.page_content for doc in relevant_docs])

    # Call Gemini directly with the retrieved context
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is not set in the environment.")

    client = genai.Client(api_key=api_key)

    prompt = (
        "You are an AI assistant that answers questions about a specific YouTube video.\n"
        "Use ONLY the context below (extracted from the video transcript) to answer.\n"
        "If the answer is not in the context, say so clearly — don't make things up.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {query}\n\n"
        "Answer:"
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text
    except Exception as e:
        raise ValueError(f"Failed to generate answer: {str(e)}")

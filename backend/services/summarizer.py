import os
from google import genai
from google.genai import types

def generate_summary(transcript_text: str) -> str:
    """Generate a summary of the provided transcript using Gemini directly."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is not set in the environment.")

    client = genai.Client(api_key=api_key)

    prompt = (
        "You are an expert content summarizer. Below is the transcript of a YouTube video.\n"
        "The transcript may be in any language — always respond in English.\n"
        "Please provide a comprehensive and well-structured summary of the video.\n"
        "Include:\n"
        "- Main topics discussed\n"
        "- Key takeaways\n"
        "- Important conclusions\n\n"
        f"Transcript:\n{transcript_text[:30000]}\n\n"
        "Summary (in English):"
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text
    except Exception as e:
        raise ValueError(f"Failed to generate summary: {str(e)}")

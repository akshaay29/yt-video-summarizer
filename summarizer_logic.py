import os
import re
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool

# FIX: Import specific exceptions for precise error handling instead of bare except
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
    CouldNotRetrieveTranscript,
)

load_dotenv()


# ---------------------------
# Extract YouTube Video ID
# ---------------------------
def get_video_id(youtube_url: str) -> str:
    """Extract 11-character video ID from any YouTube URL format."""
    regex_patterns = [
        r'(?:v=|\/videos\/|embed\/|\.be\/|shorts\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})',
        r'youtu\.be\/([a-zA-Z0-9_-]{11})',
    ]
    for pattern in regex_patterns:
        match = re.search(pattern, youtube_url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from URL: {youtube_url}")


# ---------------------------
# TOOL: Fetch Transcript
#
# FIXES APPLIED:
#   1. v1.x removed class-method style. Must instantiate YouTubeTranscriptApi()
#      then call ytt_api.fetch(video_id) and ytt_api.list(video_id).
#
#   2. Primary path: ytt_api.fetch(video_id, languages=[...]) — tries language
#      groups in order. No need for TranscriptList unless all groups fail.
#
#   3. Fallback path: ytt_api.list() → find_transcript() to discover language_code
#      → re-fetch via ytt_api.fetch([lang_code]). We do NOT call
#      transcript_obj.fetch() directly — that internal path may require PoToken.
#
#   4. FetchedTranscript iterates FetchedTranscriptSnippet dataclasses (.text attr).
#      Removed legacy dict-style access entirely.
#
#   5. URL cleaning handles prose-wrapped URLs the agent may pass.
# ---------------------------
@tool("YouTube Transcript Extractor")
def fetch_youtube_transcript(youtube_url: str) -> str:
    """
    Fetch the full plain-text transcript from a YouTube video.
    Accepts any standard YouTube URL format.
    Returns the transcript as a single string, or 'Transcript Error: ...' on failure.
    """
    try:
        # Strip any surrounding prose the LLM agent may have added
        url_match = re.search(r'https?://[^\s"\'<>]+', youtube_url)
        if url_match:
            youtube_url = url_match.group(0).rstrip('.,)')
        else:
            return "Transcript Error: No valid URL found in input."

        video_id = get_video_id(youtube_url)

        # FIX 1: v1.x requires an instance — class-method calls no longer exist
        ytt_api = YouTubeTranscriptApi()

        fetched = None

        # --- Primary: direct fetch with preferred language groups ---
        # FIX 2: ytt_api.fetch() picks the first matching language from the list.
        for lang_group in (
            ['en', 'en-US', 'en-GB', 'en-AU', 'en-CA'],
            ['en-IN', 'hi'],
        ):
            try:
                fetched = ytt_api.fetch(video_id, languages=lang_group)
                break
            except (NoTranscriptFound, CouldNotRetrieveTranscript):
                continue

        # --- Fallback: discover available language via TranscriptList ---
        # FIX 3: Use .list() only to discover the language_code, then re-fetch
        # via ytt_api.fetch([lang_code]) on the supported instance-method path.
        if fetched is None:
            transcript_list = ytt_api.list(video_id)

            lang_code = None
            try:
                t = transcript_list.find_transcript(
                    ['en', 'en-US', 'en-GB', 'en-IN', 'hi']
                )
                lang_code = t.language_code
            except NoTranscriptFound:
                pass

            if lang_code is None:
                try:
                    t = transcript_list.find_generated_transcript(
                        ['en', 'en-US', 'en-GB', 'en-IN', 'hi']
                    )
                    lang_code = t.language_code
                except NoTranscriptFound:
                    pass

            if lang_code is None:
                return (
                    "Transcript Error: No English or Hindi transcript available for "
                    f"video '{video_id}'. Captions may not be enabled on this video."
                )

            fetched = ytt_api.fetch(video_id, languages=[lang_code])

        # FIX 4: In v1.x, FetchedTranscript yields FetchedTranscriptSnippet dataclasses.
        # Access .text attribute directly — no dict keys, no getitem fallback needed.
        text_parts = [snippet.text for snippet in fetched]

        if not text_parts:
            return f"Transcript Error: Transcript for '{video_id}' was empty."

        return " ".join(text_parts)

    except VideoUnavailable:
        return "Transcript Error: Video is unavailable (private, deleted, or geo-blocked)."
    except TranscriptsDisabled:
        return "Transcript Error: Transcripts/captions are disabled for this video."
    except ValueError as ve:
        return f"Transcript Error: {ve}"
    except Exception as e:
        return f"Transcript Error: Unexpected — {type(e).__name__}: {e}"


# ---------------------------
# MAIN SUMMARIZATION PIPELINE
# ---------------------------
def run_summarization(youtube_url: str):

    # Early validation before spinning up agents
    try:
        get_video_id(youtube_url)
    except ValueError:
        return "**Error:** Not a valid YouTube URL."

    gemini_llm = LLM(
        model="gemini/gemini-2.5-flash",
        api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.3,
    )

    extractor = Agent(
        role="YouTube Transcript Specialist",
        goal="Extract the raw, complete transcript text from the given YouTube video URL.",
        backstory=(
            "You are an expert at retrieving captions from YouTube videos. "
            "You MUST call the 'YouTube Transcript Extractor' tool with the exact URL. "
            "If the tool returns a message starting with 'Transcript Error:', return "
            "that exact error message verbatim — do NOT invent or paraphrase content."
        ),
        tools=[fetch_youtube_transcript],
        llm=gemini_llm,
        verbose=True,
        allow_delegation=False,
    )

    summarizer = Agent(
        role="Senior Content Analyst",
        goal="Produce a clear, structured summary from a video transcript.",
        backstory=(
            "You excel at distilling long transcripts into concise insights. "
            "CRITICAL RULE: If the transcript starts with 'Transcript Error:', "
            "do NOT summarize. Respond only with: "
            "'Summary cannot be generated: ' followed by the error. "
            "Never fabricate content."
        ),
        llm=gemini_llm,
        verbose=True,
        allow_delegation=False,
    )

    # FIX 5: URL embedded directly via f-string in the task description.
    # Using crew.kickoff(inputs={"youtube_url": url}) with a {youtube_url}
    # placeholder is unreliable — CrewAI doesn't always substitute template
    # vars into tool call arguments, causing the agent to pass the literal
    # placeholder string to the tool instead of the real URL.
    extract_task = Task(
        description=(
            f"Use the 'YouTube Transcript Extractor' tool to fetch the transcript "
            f"for this exact URL: {youtube_url}\n\n"
            f"Return the full transcript text as-is. If the tool returns an error, "
            f"return it verbatim without modification."
        ),
        expected_output=(
            "Complete transcript as plain text, OR an error message starting with "
            "'Transcript Error:' if extraction failed."
        ),
        agent=extractor,
    )

    # FIX 6: Error-guard instructions in both description and expected_output
    # to prevent the LLM from summarizing error strings.
    summarize_task = Task(
        description="""
You will receive the output of the transcript extraction step.

STEP 1 — Error check (MANDATORY):
If the text starts with "Transcript Error:", stop and respond with ONLY:
"Summary cannot be generated: <the exact error message>"

STEP 2 — If the transcript is valid, produce a structured Markdown summary:

## Overview
2-3 sentences describing the video's subject and purpose.

## Key Points
- Bullet list of the most important arguments, findings, or facts.

## Detailed Insights
A paragraph on methodologies, examples, or solutions discussed.

## Key Takeaways
- Actionable conclusions or things the viewer should remember.

Target length: 250–350 words.
""",
        expected_output=(
            "A structured Markdown summary (250–350 words) with Overview, Key Points, "
            "Detailed Insights, and Key Takeaways — OR 'Summary cannot be generated: <error>' "
            "if the transcript was invalid."
        ),
        agent=summarizer,
        context=[extract_task],
    )

    crew = Crew(
        agents=[extractor, summarizer],
        tasks=[extract_task, summarize_task],
        process=Process.sequential,
        verbose=True,
    )

    # FIX 7: No inputs={} argument — URL is already baked into the task description.
    result = crew.kickoff()
    return result

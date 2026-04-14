from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled
from urllib.parse import urlparse, parse_qs

def get_video_id(url: str) -> str:
    """Extract YouTube video ID from URL."""
    try:
        parsed_url = urlparse(url)
        if "youtube.com" in parsed_url.netloc:
            return parse_qs(parsed_url.query)["v"][0]
        elif "youtu.be" in parsed_url.netloc:
            return parsed_url.path[1:].split("?")[0]
        else:
            raise ValueError("Invalid YouTube URL")
    except Exception as e:
        raise ValueError(f"Could not extract video ID from URL: {url}. Error: {str(e)}")


def load_transcript(video_url: str) -> dict:
    """
    Fetch transcript for a given YouTube URL.
    Tries English first, then auto-generated English, then falls back to
    any available language. Gemini can summarize and answer in English
    regardless of the transcript language.
    """
    video_id = get_video_id(video_url)

    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)

        # Priority order: manual English → generated English → any language
        fetched = None
        language_used = None

        # 1. Try manual or generated English
        for lang in ["en", "en-US", "en-GB"]:
            try:
                fetched = transcript_list.find_transcript([lang]).fetch()
                language_used = lang
                break
            except NoTranscriptFound:
                continue

        # 2. Fall back to any available transcript
        if fetched is None:
            try:
                # get the first available transcript (generated or manual)
                first = next(iter(transcript_list))
                fetched = first.fetch()
                language_used = first.language_code
            except StopIteration:
                raise ValueError("No transcripts of any language are available for this video.")

        full_transcript = " ".join([snippet.text for snippet in fetched.snippets])

        return {
            "video_id": video_id,
            "text": full_transcript,
            "language": language_used,
        }

    except TranscriptsDisabled:
        raise ValueError(
            f"Transcripts/subtitles are completely disabled for this video ({video_id}). "
            "Please try a different video."
        )
    except Exception as e:
        raise ValueError(
            f"Could not retrieve transcript for video '{video_id}'. "
            f"Error: {str(e)}"
        )

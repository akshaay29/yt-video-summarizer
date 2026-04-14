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


import requests
import random

def get_free_proxies():
    """Fetch a list of free HTTP proxies to bypass Cloud IP blocks."""
    try:
        response = requests.get(
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt", 
            timeout=5
        )
        if response.status_code == 200:
            proxies = response.text.strip().split("\n")
            # Filter empty lines and shuffle
            proxies = [p.strip() for p in proxies if p.strip()]
            random.shuffle(proxies)
            return proxies
    except Exception:
        pass
    return []

def fetch_with_api(video_id: str, proxies_dict=None):
    """Helper to fetch transcript using the API, optionally with a proxy."""
    api = YouTubeTranscriptApi()
    transcript_list = api.list(video_id, proxies=proxies_dict)

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
        first = next(iter(transcript_list))
        fetched = first.fetch()
        language_used = first.language_code

    full_transcript = " ".join([snippet.text for snippet in fetched.snippets])
    return {
        "video_id": video_id,
        "text": full_transcript,
        "language": language_used,
    }

def load_transcript(video_url: str) -> dict:
    """
    Fetch transcript for a given YouTube URL.
    Includes an automatic fallback to free residential proxies if the primary Cloud IP is blocked.
    """
    video_id = get_video_id(video_url)

    # 1. Try directly first (fastest, works on local development)
    try:
        return fetch_with_api(video_id)
    except TranscriptsDisabled:
        raise ValueError(
            f"Transcripts/subtitles are completely disabled for this video ({video_id}). "
            "Please try a different video."
        )
    except Exception as direct_err:
        # If the error is likely an IP ban, we try proxies
        err_msg = str(direct_err).lower()
        if "blocking requests from your ip" not in err_msg and "too many requests" not in err_msg:
            # If it's not an IP ban, it's likely a real error (like video deleted or no subs created yet)
            raise ValueError(f"Could not retrieve transcript for video '{video_id}'. Error: {str(direct_err)}")

    # 2. IP Ban detected! Try fallback proxies
    proxies = get_free_proxies()
    if not proxies:
        raise ValueError("YouTube blocked the server IP and no backup proxies were available. Please try again later.")

    # Try up to 8 different free proxies
    max_retries = min(8, len(proxies))
    for i in range(max_retries):
        proxy_url = f"http://{proxies[i]}"
        try:
            return fetch_with_api(video_id, proxies_dict={"http": proxy_url, "https": proxy_url})
        except Exception:
            continue # Try next proxy

    raise ValueError("YouTube blocked the server IP and all backup proxies failed. Please try again later.")

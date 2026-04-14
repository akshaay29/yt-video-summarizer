import random
import requests as http_requests
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled


# ─── Helpers ───────────────────────────────────────────────


def get_video_id(url: str) -> str:
    """Extract YouTube video ID from URL."""
    try:
        parsed = urlparse(url)
        if "youtube.com" in parsed.netloc:
            return parse_qs(parsed.query)["v"][0]
        elif "youtu.be" in parsed.netloc:
            return parsed.path[1:].split("?")[0]
        else:
            raise ValueError("Not a recognisable YouTube URL.")
    except Exception as e:
        raise ValueError(f"Could not extract video ID from: {url}. ({e})")


def _ytt_api_fetch(video_id: str) -> dict:
    """
    Attempt transcript retrieval via youtube-transcript-api.
    Works perfectly on local machines and non-blocked IPs.
    """
    api = YouTubeTranscriptApi()
    transcript_list = api.list(video_id)

    fetched, lang_used = None, None
    for lang in ["en", "en-US", "en-GB"]:
        try:
            fetched = transcript_list.find_transcript([lang]).fetch()
            lang_used = lang
            break
        except NoTranscriptFound:
            continue

    if fetched is None:
        first = next(iter(transcript_list))
        fetched = first.fetch()
        lang_used = first.language_code

    text = " ".join(s.text for s in fetched.snippets)
    return {"video_id": video_id, "text": text, "language": lang_used}


def _ytdlp_fetch(video_url: str, video_id: str) -> dict:
    """
    Fallback: use yt-dlp to get the CDN subtitle URL, then download it.
    yt-dlp rotates its own cookies/headers and the CDN URLs themselves
    are not IP-restricted, so this bypasses cloud IP bans.
    """
    try:
        import yt_dlp
    except ImportError:
        raise ValueError("yt-dlp is not installed.")

    ydl_opts = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)

    # Manual subs override auto-captions
    auto = info.get("automatic_captions", {})
    manual = info.get("subtitles", {})
    all_subs = {**auto, **manual}

    if not all_subs:
        raise ValueError("No subtitle tracks found for this video.")

    priority = ["en", "en-US", "en-GB", "en-orig"] + list(all_subs.keys())

    for lang in priority:
        if lang not in all_subs:
            continue
        formats = all_subs[lang]
        # Prefer json3 (easiest to parse), then vtt, then any
        for preferred_ext in ("json3", "vtt", None):
            for fmt in formats:
                if preferred_ext is None or fmt.get("ext") == preferred_ext:
                    try:
                        r = http_requests.get(fmt["url"], timeout=15)
                        if r.status_code != 200:
                            continue

                        if fmt.get("ext") == "json3":
                            data = r.json()
                            pieces = []
                            for event in data.get("events", []):
                                for seg in event.get("segs", []):
                                    t = seg.get("utf8", "").strip()
                                    if t and t != "\n":
                                        pieces.append(t)
                            text = " ".join(pieces)
                        else:
                            # Strip VTT timing lines naively
                            import re
                            text = re.sub(
                                r"(\d{2}:)?\d{2}:\d{2}\.\d{3} --> .*|WEBVTT.*|<[^>]+>",
                                "",
                                r.text,
                            )
                            text = " ".join(text.split())

                        if text:
                            return {"video_id": video_id, "text": text, "language": lang}
                    except Exception:
                        continue

    raise ValueError("yt-dlp found subtitle tracks but could not download any.")


# ─── Public API ────────────────────────────────────────────


def load_transcript(video_url: str) -> dict:
    """
    Fetch transcript using a three-tier strategy:
      1. youtube-transcript-api directly (fast, local)
      2. yt-dlp CDN fetch (bypasses cloud IP bans)
      3. youtube-transcript-api with free proxy fallback
    """
    video_id = get_video_id(video_url)

    # ── Tier 1: direct ─────────────────────────────────────
    try:
        return _ytt_api_fetch(video_id)
    except TranscriptsDisabled:
        raise ValueError(
            f"Subtitles are disabled for this video ({video_id}). Try a different video."
        )
    except Exception as e1:
        ip_blocked = any(k in str(e1).lower() for k in ("blocking requests", "too many requests", "ipblocked", "requestblocked"))
        if not ip_blocked:
            raise ValueError(f"Could not retrieve transcript: {e1}")

    # ── Tier 2: yt-dlp CDN ─────────────────────────────────
    try:
        return _ytdlp_fetch(video_url, video_id)
    except Exception:
        pass

    # ── Tier 3: free proxy fallback ────────────────────────
    try:
        r = http_requests.get(
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            timeout=5,
        )
        proxies = [p.strip() for p in r.text.strip().split("\n") if p.strip()]
        random.shuffle(proxies)
    except Exception:
        proxies = []

    for proxy in proxies[:5]:
        try:
            api = YouTubeTranscriptApi(proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"})
            transcript_list = api.list(video_id)
            fetched, lang_used = None, None
            for lang in ["en", "en-US", "en-GB"]:
                try:
                    fetched = transcript_list.find_transcript([lang]).fetch()
                    lang_used = lang
                    break
                except NoTranscriptFound:
                    continue
            if fetched is None:
                first = next(iter(transcript_list))
                fetched = first.fetch()
                lang_used = first.language_code
            text = " ".join(s.text for s in fetched.snippets)
            return {"video_id": video_id, "text": text, "language": lang_used}
        except Exception:
            continue

    # ── Tier 4: Gemini Native YouTube Parsing (Ultimate Fallback)
    import os
    import time
    from google import genai
    api_key = os.environ.get("GOOGLE_API_KEY")
    gemini_error_msg = None
    if api_key:
        client = genai.Client(api_key=api_key)
        prompt = f"Return the raw, exact, word-for-word transcript of this video, nothing else: {video_url}"
        
        # Retry logic for 503 UNAVAILABLE errors during high load
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash", 
                    contents=prompt
                )
                if response.text and len(response.text) > 100:
                    print(f"Successfully loaded transcript via Gemini native integration on attempt {attempt+1}!")
                    return {"video_id": video_id, "text": response.text, "language": "en"}
            except Exception as e:
                err_str = str(e)
                if "503" in err_str or "demand" in err_str.lower():
                    gemini_error_msg = "Google Gemini API is experiencing high demand (503). Retrying..."
                    print(gemini_error_msg)
                    time.sleep(2)  # Wait before retry
                    continue
                else:
                    gemini_error_msg = f"Gemini fallback failed: {err_str}"
                    print(gemini_error_msg)
                    break # Break on non-503 errors

    # If we reached here, ALL TIERS FAILED.
    # Determine the most accurate error message to show the user.
    if gemini_error_msg and ("503" in gemini_error_msg or "demand" in gemini_error_msg.lower()):
        raise ValueError("Google Gemini API is currently overloaded (503). Please wait a few moments and try again.")
    elif gemini_error_msg:
        raise ValueError(f"Could not retrieve transcript. YouTube IP block active, and Gemini fallback failed: {gemini_error_msg}")
    else:
        raise ValueError("Could not retrieve transcript — YouTube is blocking server IPs and fallback systems failed. Try again later.")


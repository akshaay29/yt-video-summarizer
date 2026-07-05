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


# Refusal-SPECIFIC phrases that mark a Gemini "I can't read this video" reply
# rather than a real transcript. These are deliberately multi-word and rare in
# ordinary speech — bare fragments like "i cannot" match real dialogue (e.g.
# "I cannot predict the future") and cause false rejections, so they are avoided.
_REFUSAL_MARKERS = (
    "unable to retrieve", "unable to provide", "unable to access",
    "unable to fulfill", "cannot access", "can't access", "cannot provide",
    "can't provide", "cannot retrieve", "can't retrieve", "cannot fulfill",
    "can't fulfill", "provide the transcript", "invalid or non-existent",
    "as an ai", "i'm sorry, but", "i am sorry, but", "no transcript is available",
)


def _looks_like_real_transcript(text: str) -> bool:
    """True only when text looks like actual video content — not empty or a refusal.

    A refusal is a short meta-message declining to transcribe; it opens with one of
    the refusal-specific phrases above. We scan only the opening (first ~200 chars)
    for those phrases so a genuine transcript that merely says "I cannot ..." mid-
    sentence is not falsely rejected.
    """
    if not text or len(text.strip()) < 60:
        return False
    head = text.strip().lower()[:200]
    return not any(marker in head for marker in _REFUSAL_MARKERS)


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

    # ── Tier 4: Gemini native video understanding (Ultimate Fallback)
    # Pass the YouTube URL to Gemini as a VIDEO input (file_data/file_uri) so the
    # model ingests the actual public video. Previously the URL was embedded in a
    # text prompt — the text API can't watch the video, so Gemini hallucinated a
    # transcript or returned a refusal, which then got summarized as garbage.
    # (YouTube-URL input is public-videos-only, preview/free tier.)
    import os
    import time
    from google import genai
    from google.genai import types
    api_key = os.environ.get("GOOGLE_API_KEY")
    gemini_error_msg = None
    if api_key:
        client = genai.Client(api_key=api_key)
        # Pass the CANONICAL watch URL (not the raw, param-laden input) as a video
        # part so Gemini ingests the real video. Ask for a faithful transcript
        # rather than strict "verbatim" to reduce RECITATION/safety blocks.
        canonical_url = f"https://www.youtube.com/watch?v={video_id}"
        contents = types.Content(
            parts=[
                types.Part(file_data=types.FileData(file_uri=canonical_url)),
                types.Part(text=(
                    "Provide a faithful, detailed transcript of what is actually said "
                    "in this video — the spoken words, in order. No commentary or headings."
                )),
            ]
        )

        # Retry transient failures (503 overload, and empty/blocked responses).
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=contents,
                )
                # `.text` can RAISE (not just be None) when a candidate is blocked
                # (safety / recitation) — mirror summarizer.py & rag_pipeline.py.
                try:
                    text = response.text
                except Exception:
                    text = None
                if _looks_like_real_transcript(text):
                    print(f"Successfully loaded transcript via Gemini video understanding on attempt {attempt+1}!")
                    return {"video_id": video_id, "text": text, "language": "en"}
                # Empty / blocked / refusal-like → may be transient, so retry;
                # if all attempts fail we fall through to the ValueError below.
                gemini_error_msg = "Gemini could not produce a usable transcript for this video."
                print(gemini_error_msg)
                continue
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
                    break  # Break on non-503 errors

    # If we reached here, ALL TIERS FAILED.
    # Determine the most accurate error message to show the user.
    if gemini_error_msg and ("503" in gemini_error_msg or "demand" in gemini_error_msg.lower()):
        raise ValueError("Google Gemini API is currently overloaded (503). Please wait a few moments and try again.")
    else:
        raise ValueError(
            "Could not obtain a real transcript for this video. YouTube is blocking "
            "the server's IP and the video could not be read directly (it may be "
            "private, unlisted, region-locked, or have no speech). Try a different video."
        )


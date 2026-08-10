from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)
import re


def extract_video_id(url: str) -> str:
    """YouTube URL मधून video ID काढ (सगळे common URL formats handle करतो)."""
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"youtu\.be\/([0-9A-Za-z_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError("Valid YouTube video ID सापडला नाही.")


def get_youtube_transcript(url: str, languages: list = None) -> str:
    """
    Video ला captions असतील तर थेट transcript text परत देतो.
    Audio download/whisper ची अजिबात गरज नाही.
    """
    video_id = extract_video_id(url)
    languages = languages or ["en", "hi", "en-US", "en-IN"]

    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(
            video_id, languages=languages
        )
    except (TranscriptsDisabled, NoTranscriptFound):
        raise RuntimeError(
            "या video ला captions/transcript उपलब्ध नाहीत. "
            "कृपया local file upload वापर."
        )
    except VideoUnavailable:
        raise RuntimeError("Video उपलब्ध नाही किंवा private/restricted आहे.")

    full_text = " ".join(segment["text"] for segment in transcript_list)
    return full_text.strip()
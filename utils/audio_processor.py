import os
import re
from pathlib import Path

import yt_dlp
from pydub import AudioSegment
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)


# ==========================================================
# Download Directory
# ==========================================================

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ==========================================================
# YouTube Transcript / Captions (audio download टाळण्यासाठी — cloud-safe)
# ==========================================================

def extract_video_id(url: str) -> str:
    """YouTube URL मधून video ID काढ (सगळे common formats handle करतो)."""
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
    Audio download/Whisper/Sarvam ची गरज नाही — 403 चा धोका टळतो.
    Captions नसतील तर RuntimeError raise होतो — caller ने audio-download वर fallback करावं.
    """
    video_id = extract_video_id(url)
    languages = languages or ["en", "hi", "en-US", "en-IN"]

    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(
            video_id, languages=languages
        )
    except (TranscriptsDisabled, NoTranscriptFound):
        raise RuntimeError(
            "या video ला captions/transcript उपलब्ध नाहीत."
        )
    except VideoUnavailable:
        raise RuntimeError("Video उपलब्ध नाही किंवा private/restricted आहे.")

    full_text = " ".join(segment["text"] for segment in transcript_list)
    return full_text.strip()


# ==========================================================
# Download YouTube Audio (fallback — captions नसतील तेव्हाच वापरलं जातं)
# ==========================================================

def download_youtube_audio(url: str) -> str:

    output_template = str(DOWNLOAD_DIR / "%(title)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "outtmpl": output_template,

        "quiet": False,
        "no_warnings": False,

        "noplaylist": True,
        "geo_bypass": True,

        "retries": 10,
        "fragment_retries": 10,

        "extractor_args": {
            "youtube": {
                "player_client": [
                    "web",
                    "web_creator",
                    "android",
                ]
            }
        },

        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_file = ydl.prepare_filename(info)
            wav_file = os.path.splitext(downloaded_file)[0] + ".wav"
            return wav_file

    except Exception as e:
        if "403" in str(e):
            raise Exception(
                "❌ YouTube blocked this download (HTTP 403).\n\n"
                "Try:\n"
                "• Another public video\n"
                "• Upload MP4 directly\n"
                "• Run locally"
            )
        raise Exception(str(e))


# ==========================================================
# Convert Local File
# ==========================================================

def convert_to_wav(input_path: str):

    output_path = os.path.splitext(input_path)[0] + "_converted.wav"

    audio = AudioSegment.from_file(input_path)

    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)

    audio.export(output_path, format="wav")

    return output_path


# ==========================================================
# Chunk Audio
# ==========================================================

def chunk_audio(wav_path, chunk_minutes=10):

    audio = AudioSegment.from_wav(wav_path)

    chunk_ms = chunk_minutes * 60 * 1000

    chunks = []

    for i in range(0, len(audio), chunk_ms):

        chunk = audio[i:i + chunk_ms]

        chunk_path = (
            os.path.splitext(wav_path)[0]
            + f"_chunk_{len(chunks)}.wav"
        )

        chunk.export(chunk_path, format="wav")

        chunks.append(chunk_path)

    return chunks


# ==========================================================
# Main Function (local file साठी वापरायचं — YouTube साठी app.py आधी
# get_youtube_transcript() try करतो, तो fail झाला तरच हे function वापरलं जातं)
# ==========================================================

def process_input(source: str):

    if source.startswith(("http://", "https://")):

        print("Downloading YouTube Audio...")

        wav_path = download_youtube_audio(source)

    else:

        print("Processing Local File...")

        wav_path = convert_to_wav(source)

    print("Creating Audio Chunks...")

    chunks = chunk_audio(wav_path)

    print(f"Done. {len(chunks)} chunk(s) created.")

    return chunks
import os
import tempfile
import shutil
import yt_dlp
from pydub import AudioSegment

try:
    import streamlit as st
except ImportError:
    st = None

FFMPEG_DIR = os.getenv("FFMPEG_DIR", "")
SYSTEM_FFMPEG = shutil.which("ffmpeg")
SYSTEM_FFPROBE = shutil.which("ffprobe")

if FFMPEG_DIR:
    os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ["PATH"]
    exe_ext = ".exe" if os.name == "nt" else ""
    FFMPEG_PATH = os.path.join(FFMPEG_DIR, f"ffmpeg{exe_ext}")
    FFPROBE_PATH = os.path.join(FFMPEG_DIR, f"ffprobe{exe_ext}")
else:
    FFMPEG_PATH = SYSTEM_FFMPEG or "ffmpeg"
    FFPROBE_PATH = SYSTEM_FFPROBE or "ffprobe"

AudioSegment.converter = FFMPEG_PATH
AudioSegment.ffprobe = FFPROBE_PATH

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def _get_cookies_file():
    """Streamlit secrets मधून cookies वाचून temp file मध्ये लिही."""
    cookies_content = None

    if st is not None:
        try:
            cookies_content = st.secrets.get("YT_COOKIES")
        except Exception:
            cookies_content = None

    if not cookies_content:
        cookies_content = os.getenv("YT_COOKIES")

    if not cookies_content:
        return None

    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
    tmp.write(cookies_content)
    tmp.close()
    return tmp.name


def download_youtube_audio(url: str) -> str:

    output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "ffmpeg_location": os.path.dirname(FFMPEG_PATH) if FFMPEG_DIR else None,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
        "noplaylist": True,
        "extractor_args": {
            "youtube": {"player_client": ["android", "web"]}
        },
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            )
        },
    }

    cookies_file = _get_cookies_file()
    if cookies_file:
        ydl_opts["cookiefile"] = cookies_file

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    filename = (
        filename.replace(".webm", ".wav")
        .replace(".m4a", ".wav")
        .replace(".mp4", ".wav")
    )

    return filename
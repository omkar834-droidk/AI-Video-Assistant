import os
import shutil
import yt_dlp
from pydub import AudioSegment

# -------------------------------
# FFmpeg Configuration (portable — local Windows + Streamlit Cloud/Linux दोन्हीवर चालतं)
# -------------------------------
FFMPEG_DIR = os.getenv("FFMPEG_DIR", "")          # फक्त local dev साठी .env मध्ये set कर
SYSTEM_FFMPEG = shutil.which("ffmpeg")             # cloud/Linux वर system ffmpeg auto-detect
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

# -------------------------------
# Download Folder
# -------------------------------
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# -------------------------------
# Download YouTube Audio
# -------------------------------
def download_youtube_audio(url: str) -> str:

    output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",           # rigid "140" ऐवजी — जास्त reliable
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

    cookies_file = os.getenv("YT_COOKIES_FILE")
    if cookies_file and os.path.exists(cookies_file):
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


# -------------------------------
# Convert Local File to WAV
# -------------------------------
def convert_to_wav(input_path: str) -> str:

    output_path = os.path.splitext(input_path)[0] + "_converted.wav"

    audio = AudioSegment.from_file(input_path)

    audio = (
        audio
        .set_channels(1)
        .set_frame_rate(16000)
    )

    audio.export(output_path, format="wav")

    return output_path


# -------------------------------
# Split Audio
# -------------------------------
def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list:

    audio = AudioSegment.from_wav(wav_path)

    chunk_ms = chunk_minutes * 60 * 1000

    chunks = []

    for i, start in enumerate(range(0, len(audio), chunk_ms)):

        chunk = audio[start:start + chunk_ms]

        chunk_path = f"{wav_path}_chunk_{i}.wav"

        chunk.export(chunk_path, format="wav")

        chunks.append(chunk_path)

    return chunks


# -------------------------------
# Main Entry
# -------------------------------
def process_input(source: str) -> list:

    if source.startswith("http://") or source.startswith("https://"):

        print("Detected YouTube URL. Downloading audio...")

        wav_path = download_youtube_audio(source)

    else:

        print("Detected local file. Converting to WAV...")

        wav_path = convert_to_wav(source)

    print("Chunking audio...")

    chunks = chunk_audio(wav_path)

    print(f"Audio ready — {len(chunks)} chunk(s) created.")

    return chunks
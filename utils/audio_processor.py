import os
import yt_dlp
from pydub import AudioSegment

# -------------------------------
# Download Folder
# -------------------------------

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# -------------------------------
# Download YouTube Audio
# -------------------------------

def download_youtube_audio(url: str) -> str:

    output_path = os.path.join(
        DOWNLOAD_DIR,
        "%(title)s.%(ext)s"
    )

    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio",

        "outtmpl": output_path,

        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0 Safari/537.36"
            )
        },

        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"]
            }
        },

        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],

        "quiet": False,
        "noplaylist": True,
        "geo_bypass": True,
    }

    try:

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(
                url,
                download=True
            )

            filename = ydl.prepare_filename(
                info
            )

    except Exception as e:

        print(
            f"YT-DLP Error: {e}"
        )

        raise

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

    output_path = (
        os.path.splitext(input_path)[0]
        + "_converted.wav"
    )

    audio = AudioSegment.from_file(input_path)

    audio = (
        audio
        .set_channels(1)
        .set_frame_rate(16000)
    )

    audio.export(
        output_path,
        format="wav"
    )

    return output_path


# -------------------------------
# Split Audio into Chunks
# -------------------------------

def chunk_audio(
    wav_path: str,
    chunk_minutes: int = 10
) -> list:

    audio = AudioSegment.from_wav(wav_path)

    chunk_ms = (
        chunk_minutes
        * 60
        * 1000
    )

    chunks = []

    for i, start in enumerate(
        range(
            0,
            len(audio),
            chunk_ms
        )
    ):

        chunk = audio[
            start:start + chunk_ms
        ]

        chunk_path = (
            f"{wav_path}_chunk_{i}.wav"
        )

        chunk.export(
            chunk_path,
            format="wav"
        )

        chunks.append(chunk_path)

    return chunks


# -------------------------------
# Main Function
# -------------------------------

def process_input(
    source: str
) -> list:

    if source.startswith(
        ("http://", "https://")
    ):

        print(
            "Detected YouTube URL..."
        )

        wav_path = download_youtube_audio(
            source
        )

    else:

        print(
            "Detected local file..."
        )

        wav_path = convert_to_wav(
            source
        )

    print("Chunking audio...")

    chunks = chunk_audio(
        wav_path
    )

    print(
        f"Audio ready — "
        f"{len(chunks)} chunk(s)"
    )

    return chunks

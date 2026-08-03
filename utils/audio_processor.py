import os
from pathlib import Path

import yt_dlp
from pydub import AudioSegment

# -------------------------------------------------------------------
# Download Directory
# -------------------------------------------------------------------

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


# -------------------------------------------------------------------
# Download YouTube Audio
# -------------------------------------------------------------------

def download_youtube_audio(url: str) -> str:

    output_path = str(DOWNLOAD_DIR / "%(title)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "noplaylist": True,
        "quiet": False,
        "no_warnings": False,
        "geo_bypass": True,

        "extractor_args": {
            "youtube": {
                "player_client": ["android"]
            }
        },

        "retries": 10,
        "fragment_retries": 10,
        "skip_unavailable_fragments": True,

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

            filename = os.path.splitext(
                ydl.prepare_filename(info)
            )[0] + ".wav"

            return filename

    except Exception as e:
        raise RuntimeError(f"YouTube Download Failed:\n{e}")


# -------------------------------------------------------------------
# Convert Local File
# -------------------------------------------------------------------

def convert_to_wav(input_path: str) -> str:

    output_path = os.path.splitext(input_path)[0] + "_converted.wav"

    audio = AudioSegment.from_file(input_path)

    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)

    audio.export(output_path, format="wav")

    return output_path


# -------------------------------------------------------------------
# Chunk Audio
# -------------------------------------------------------------------

def chunk_audio(
    wav_path: str,
    chunk_minutes: int = 10,
):

    audio = AudioSegment.from_wav(wav_path)

    chunk_ms = chunk_minutes * 60 * 1000

    chunks = []

    for i, start in enumerate(range(0, len(audio), chunk_ms)):

        chunk = audio[start:start + chunk_ms]

        chunk_path = (
            f"{os.path.splitext(wav_path)[0]}"
            f"_chunk_{i}.wav"
        )

        chunk.export(chunk_path, format="wav")

        chunks.append(chunk_path)

    return chunks


# -------------------------------------------------------------------
# Main Processor
# -------------------------------------------------------------------

def process_input(source: str):

    if source.startswith(("http://", "https://")):

        print("Downloading YouTube Audio...")

        wav_path = download_youtube_audio(source)

    else:

        print("Processing Local File...")

        wav_path = convert_to_wav(source)

    print("Chunking Audio...")

    chunks = chunk_audio(wav_path)

    print(f"Created {len(chunks)} chunk(s).")

    return chunks
import os
from pathlib import Path

import yt_dlp
from pydub import AudioSegment

# Create download directory
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)


def download_youtube_audio(url: str) -> str:
    """
    Download YouTube audio and convert it to WAV.
    Returns the path to the downloaded WAV file.
    """

    output_template = str(DOWNLOAD_DIR / "%(title)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "extractaudio": True,
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
        raise RuntimeError(f"Failed to download YouTube audio: {e}")


def convert_to_wav(input_path: str) -> str:
    """
    Convert any audio/video file to WAV.
    """

    output_path = os.path.splitext(input_path)[0] + "_converted.wav"

    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)

    audio.export(output_path, format="wav")

    return output_path


def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list[str]:
    """
    Split WAV into chunks.
    """

    audio = AudioSegment.from_wav(wav_path)

    chunk_ms = chunk_minutes * 60 * 1000

    chunk_paths = []

    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start:start + chunk_ms]

        chunk_path = f"{os.path.splitext(wav_path)[0]}_chunk_{i}.wav"

        chunk.export(chunk_path, format="wav")

        chunk_paths.append(chunk_path)

    return chunk_paths


def process_input(source: str) -> list[str]:
    """
    Process either a YouTube URL or a local file.
    Returns list of chunk paths.
    """

    if source.startswith(("http://", "https://")):
        print("Downloading YouTube audio...")
        wav_path = download_youtube_audio(source)
    else:
        print("Converting local file...")
        wav_path = convert_to_wav(source)

    print("Creating chunks...")

    chunks = chunk_audio(wav_path)

    print(f"Done! Created {len(chunks)} chunk(s).")

    return chunks
import asyncio
import json
import logging
import os
import tempfile

logger = logging.getLogger(__name__)


async def extract_audio(youtube_url: str) -> tuple[str, dict]:
    """
    Extract audio from YouTube video using yt-dlp.
    Returns (audio_file_path, metadata_dict).
    The caller is responsible for cleaning up the temp file.
    """
    temp_dir = tempfile.mkdtemp(prefix="repurpose_")
    output_path = os.path.join(temp_dir, "audio.mp3")

    cmd = [
        "yt-dlp",
        "--no-playlist",
        "--extract-audio",
        "--audio-format",
        "mp3",
        "--audio-quality",
        "48K",
        "--print-json",
        "--output",
        output_path,
        youtube_url,
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        error_msg = stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"yt-dlp failed: {error_msg}")

    metadata = {}
    try:
        info = json.loads(stdout.decode("utf-8"))
        metadata = {
            "title": info.get("title", ""),
            "duration": info.get("duration"),
            "uploader": info.get("uploader", ""),
            "thumbnail": info.get("thumbnail", ""),
        }
    except (json.JSONDecodeError, UnicodeDecodeError):
        logger.warning("Could not parse yt-dlp metadata JSON")

    actual_path = output_path
    if not os.path.exists(actual_path):
        for f in os.listdir(temp_dir):
            if f.endswith(".mp3"):
                actual_path = os.path.join(temp_dir, f)
                break
        else:
            raise RuntimeError("Audio file not found after extraction")

    return actual_path, metadata


async def split_audio(
    file_path: str, max_size_bytes: int = 24 * 1024 * 1024
) -> list[str]:
    """
    Split audio file into chunks if it exceeds max_size_bytes.
    Uses ffmpeg (required by yt-dlp anyway).
    Returns list of chunk file paths.
    """
    file_size = os.path.getsize(file_path)
    if file_size <= max_size_bytes:
        return [file_path]

    import subprocess

    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            file_path,
        ],
        capture_output=True,
        text=True,
    )
    total_duration = float(result.stdout.strip())

    num_chunks = (file_size // max_size_bytes) + 1
    chunk_duration = total_duration / num_chunks

    temp_dir = os.path.dirname(file_path)
    chunks = []

    for i in range(num_chunks):
        start = i * chunk_duration
        chunk_path = os.path.join(temp_dir, f"chunk_{i}.mp3")

        process = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-y",
            "-i",
            file_path,
            "-ss",
            str(start),
            "-t",
            str(chunk_duration),
            "-acodec",
            "libmp3lame",
            "-ab",
            "48k",
            chunk_path,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await process.communicate()
        if os.path.exists(chunk_path):
            chunks.append(chunk_path)

    return chunks

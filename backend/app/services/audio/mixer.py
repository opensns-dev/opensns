"""Audio mixer using ffmpeg for combining narration, BGM, and video."""

import asyncio
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Optional

import httpx

from app.services.audio.interfaces import AudioMixRequest, AudioMixResult

logger = logging.getLogger(__name__)


def _check_ffmpeg() -> bool:
    """Check if ffmpeg is available on the system."""
    return shutil.which("ffmpeg") is not None


async def _download_file(url: str, dest: Path) -> bool:
    """Download a file from URL to local path, or copy if local."""
    try:
        if url.startswith(("http://", "https://")):
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                dest.write_bytes(response.content)
        else:
            # Local file path — validate it's in temp directory
            src = Path(url).resolve()
            tmp_dir = Path(tempfile.gettempdir()).resolve()
            if not src.is_relative_to(tmp_dir):
                logger.warning("Rejected non-temp local path: %s", url)
                return False
            if not src.exists():
                logger.warning("Local file not found: %s", url)
                return False
            await asyncio.to_thread(shutil.copy2, str(src), str(dest))
        return True
    except Exception as e:
        logger.warning("Failed to download %s: %s", url, e)
        return False


async def ffmpeg_mix_audio(request: AudioMixRequest) -> AudioMixResult:
    """Mix narration and/or BGM into a video using ffmpeg.

    Filter chain:
    1. Narration volume normalization
    2. BGM volume reduction
    3. Sidechain compression (ducking) — BGM ducks under narration
    4. Mix narration + ducked BGM
    5. Loudness normalization (EBU R128: -16 LUFS)
    6. Mux with video (replace original audio)
    """
    if not _check_ffmpeg():
        logger.error("ffmpeg not found on system PATH")
        return AudioMixResult()

    work_dir = Path(tempfile.mkdtemp(prefix="opensns_mix_"))
    try:
        # Download inputs
        video_path = work_dir / "input_video.mp4"
        if not await _download_file(request.video_url, video_path):
            return AudioMixResult()

        narration_path: Optional[Path] = None
        bgm_path: Optional[Path] = None

        if request.narration_url:
            narration_path = work_dir / "narration.mp3"
            if not await _download_file(request.narration_url, narration_path):
                narration_path = None

        if request.bgm_url:
            bgm_path = work_dir / "bgm.mp3"
            if not await _download_file(request.bgm_url, bgm_path):
                bgm_path = None

        if not narration_path and not bgm_path:
            logger.warning("No audio tracks to mix, returning original video")
            return AudioMixResult()

        output_path = work_dir / "output.mp4"

        cmd = _build_ffmpeg_command(
            video_path=video_path,
            narration_path=narration_path,
            bgm_path=bgm_path,
            output_path=output_path,
            narration_volume=request.narration_volume,
            bgm_volume=request.bgm_volume,
            ducking_enabled=request.ducking_enabled,
            preserve_original_audio=request.preserve_original_audio,
        )

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            logger.error(
                "ffmpeg failed (code %d): %s", process.returncode, stderr.decode()[:500]
            )
            return AudioMixResult()

        video_data = output_path.read_bytes()
        return AudioMixResult(
            video_data=video_data,
            metadata={
                "engine": "ffmpeg",
                "has_narration": narration_path is not None,
                "has_bgm": bgm_path is not None,
            },
        )

    except Exception as e:
        logger.error("Audio mixing failed: %s", e)
        return AudioMixResult()
    finally:
        # Clean up temp directory
        shutil.rmtree(work_dir, ignore_errors=True)


def _build_ffmpeg_command(
    video_path: Path,
    narration_path: Optional[Path],
    bgm_path: Optional[Path],
    output_path: Path,
    narration_volume: float,
    bgm_volume: float,
    ducking_enabled: bool,
    preserve_original_audio: bool = False,
) -> list[str]:
    """Build the ffmpeg command for audio mixing.

    Args:
        preserve_original_audio: If True, mix BGM with the video's existing audio
            track instead of replacing it. Used for UGC videos that already have
            avatar speech.
    """
    cmd = ["ffmpeg", "-y", "-i", str(video_path)]
    inputs = []  # Track input indices (0 = video)
    input_idx = 1

    if narration_path:
        cmd.extend(["-i", str(narration_path)])
        inputs.append(("narration", input_idx))
        input_idx += 1

    if bgm_path:
        cmd.extend(["-i", str(bgm_path)])
        inputs.append(("bgm", input_idx))
        input_idx += 1

    has_narration = any(name == "narration" for name, _ in inputs)
    has_bgm = any(name == "bgm" for name, _ in inputs)
    narr_idx = next((idx for name, idx in inputs if name == "narration"), None)
    bgm_idx = next((idx for name, idx in inputs if name == "bgm"), None)

    filter_parts = []

    if has_narration and has_bgm and ducking_enabled:
        # Full pipeline: narration + BGM with ducking
        filter_parts.append(f"[{narr_idx}:a]volume={narration_volume}[narr]")
        filter_parts.append(f"[{bgm_idx}:a]volume={bgm_volume}[bgm_raw]")
        filter_parts.append(
            "[bgm_raw][narr]sidechaincompress=threshold=0.02:ratio=6:attack=200:release=1000[bgm_ducked]"
        )
        filter_parts.append(
            "[narr][bgm_ducked]amix=inputs=2:duration=first:dropout_transition=2[mixed]"
        )
        filter_parts.append("[mixed]loudnorm=I=-16:LRA=11:TP=-1.5[out]")
        filter_complex = ";".join(filter_parts)
        cmd.extend(["-filter_complex", filter_complex, "-map", "0:v", "-map", "[out]"])

    elif has_narration and has_bgm:
        # Narration + BGM without ducking
        filter_parts.append(f"[{narr_idx}:a]volume={narration_volume}[narr]")
        filter_parts.append(f"[{bgm_idx}:a]volume={bgm_volume}[bgm]")
        filter_parts.append(
            "[narr][bgm]amix=inputs=2:duration=first:dropout_transition=2[mixed]"
        )
        filter_parts.append("[mixed]loudnorm=I=-16:LRA=11:TP=-1.5[out]")
        filter_complex = ";".join(filter_parts)
        cmd.extend(["-filter_complex", filter_complex, "-map", "0:v", "-map", "[out]"])

    elif has_narration:
        # Narration only
        filter_complex = f"[{narr_idx}:a]volume={narration_volume},loudnorm=I=-16:LRA=11:TP=-1.5[out]"
        cmd.extend(["-filter_complex", filter_complex, "-map", "0:v", "-map", "[out]"])

    elif has_bgm and preserve_original_audio:
        # BGM only, preserve original audio (UGC with avatar speech)
        filter_parts.append(
            f"[0:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[orig]"
        )
        filter_parts.append(
            f"[{bgm_idx}:a]volume={bgm_volume},aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[bgm]"
        )
        filter_parts.append(
            "[orig][bgm]amix=inputs=2:duration=first:dropout_transition=2[mixed]"
        )
        filter_parts.append("[mixed]loudnorm=I=-16:LRA=11:TP=-1.5[out]")
        filter_complex = ";".join(filter_parts)
        cmd.extend(["-filter_complex", filter_complex, "-map", "0:v", "-map", "[out]"])

    elif has_bgm:
        # BGM only, replace audio
        filter_complex = (
            f"[{bgm_idx}:a]volume={bgm_volume},loudnorm=I=-16:LRA=11:TP=-1.5[out]"
        )
        cmd.extend(["-filter_complex", filter_complex, "-map", "0:v", "-map", "[out]"])

    cmd.extend(
        [
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            str(output_path),
        ]
    )

    return cmd

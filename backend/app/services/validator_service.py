import re
import subprocess
from pathlib import Path
from typing import List, Optional
import imageio_ffmpeg

from app.models.quality import ValidationResult
from app.services.storage_service import StorageService


class ValidatorService:
    """Performs technical validation on rendered video files using FFmpeg."""

    def __init__(self):
        self.storage = StorageService()
        self.ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    def validate_video_file(self, file_path: Path) -> ValidationResult:
        """Inspects codec, streams, resolution, fps, and detects container errors."""
        if not file_path.exists():
            return ValidationResult(
                file_exists=False,
                is_valid=False,
                issues=["Video file does not exist on disk."]
            )

        file_size = file_path.stat().st_size
        if file_size == 0:
            return ValidationResult(
                file_exists=True,
                is_valid=False,
                file_size_bytes=0,
                issues=["Video file is empty (0 bytes)."]
            )

        # Run FFmpeg inspection
        cmd = [self.ffmpeg_exe, "-hide_banner", "-i", str(file_path)]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        probe_output = res.stderr  # FFmpeg outputs stream info to stderr

        issues = []
        video_codec = None
        resolution = None
        fps = None
        has_audio = False
        audio_codec = None
        duration_seconds = None

        # 1. Parse Duration
        dur_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", probe_output)
        if dur_match:
            hrs, mins, secs = dur_match.groups()
            duration_seconds = int(hrs) * 3600 + int(mins) * 60 + float(secs)
        else:
            issues.append("Could not determine video duration.")

        # 2. Parse Video Stream
        vid_match = re.search(r"Stream #\d+:\d+.*Video:\s*([a-zA-Z0-9_\-]+).*?(\d{3,4}x\d{3,4})", probe_output)
        if vid_match:
            video_codec = vid_match.group(1)
            resolution = vid_match.group(2)
        else:
            issues.append("No valid video stream found in container.")

        # Parse FPS
        fps_match = re.search(r"(\d+(?:\.\d+)?)\s*fps", probe_output)
        if fps_match:
            fps = float(fps_match.group(1))

        # 3. Parse Audio Stream
        aud_match = re.search(r"Stream #\d+:\d+.*Audio:\s*([a-zA-Z0-9_\-]+)", probe_output)
        if aud_match:
            has_audio = True
            audio_codec = aud_match.group(1)

        is_valid = len(issues) == 0 and video_codec is not None

        return ValidationResult(
            file_exists=True,
            is_valid=is_valid,
            format_name="MP4 / QuickTime",
            duration_seconds=duration_seconds,
            file_size_bytes=file_size,
            video_codec=video_codec,
            resolution=resolution,
            fps=fps,
            has_audio=has_audio,
            audio_codec=audio_codec,
            issues=issues,
        )

    def validate_project_output(self, project_id: str) -> ValidationResult:
        """Validates the latest rendered video file for a project."""
        target_file = self.storage.get_full_path(f"{project_id}/output/final_video.mp4")
        return self.validate_video_file(target_file)


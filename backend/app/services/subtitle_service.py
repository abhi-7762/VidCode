from pathlib import Path
from typing import List, Dict, Any


def _format_srt_timestamp(seconds: float) -> str:
    """Format seconds into SRT timestamp (HH:MM:SS,mmm)."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    msecs = int(round((seconds - int(seconds)) * 1000))
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{msecs:03d}"


def _format_vtt_timestamp(seconds: float) -> str:
    """Format seconds into VTT timestamp (HH:MM:SS.mmm)."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    msecs = int(round((seconds - int(seconds)) * 1000))
    return f"{hrs:02d}:{mins:02d}:{secs:02d}.{msecs:03d}"


class SubtitleService:
    """Generates timestamped SRT and VTT subtitles aligned with scene narrations."""

    def generate_srt(self, scenes: List[Dict[str, Any]], output_path: Path) -> Path:
        """
        Builds a standard .srt subtitle file from storyboard scene narration cues.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        srt_entries = []
        current_time = 0.0

        subtitle_idx = 1
        for scene in scenes:
            duration = float(scene.get("duration_seconds", 5.0))
            text = (scene.get("narration_cue") or scene.get("narration") or "").strip()

            if text:
                start_str = _format_srt_timestamp(current_time)
                end_str = _format_srt_timestamp(current_time + duration)
                entry = f"{subtitle_idx}\n{start_str} --> {end_str}\n{text}\n"
                srt_entries.append(entry)
                subtitle_idx += 1

            current_time += duration

        content = "\n".join(srt_entries)
        output_path.write_text(content, encoding="utf-8")
        return output_path

    def generate_vtt(self, scenes: List[Dict[str, Any]], output_path: Path) -> Path:
        """
        Builds a WebVTT (.vtt) subtitle file.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        vtt_entries = ["WEBVTT\n"]
        current_time = 0.0

        for scene in scenes:
            duration = float(scene.get("duration_seconds", 5.0))
            text = (scene.get("narration_cue") or scene.get("narration") or "").strip()

            if text:
                start_str = _format_vtt_timestamp(current_time)
                end_str = _format_vtt_timestamp(current_time + duration)
                entry = f"{start_str} --> {end_str}\n{text}\n"
                vtt_entries.append(entry)

            current_time += duration

        content = "\n".join(vtt_entries)
        output_path.write_text(content, encoding="utf-8")
        return output_path


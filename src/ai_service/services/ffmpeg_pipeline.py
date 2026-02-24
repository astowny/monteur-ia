from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class FFmpegPipelineService:
    def __init__(self, ffmpeg_bin: str = "ffmpeg") -> None:
        self.ffmpeg_bin = ffmpeg_bin

    def is_available(self) -> bool:
        return shutil.which(self.ffmpeg_bin) is not None

    def probe_metadata(self, input_path: str) -> dict[str, str]:
        path = Path(input_path)
        if not path.exists():
            raise FileNotFoundError(f"Input video not found: {input_path}")
        return {
            "path": str(path),
            "size_bytes": str(path.stat().st_size),
            "name": path.name,
        }

    def build_export_command(
        self,
        input_path: str,
        output_path: str,
        aspect_ratio: str,
        add_subtitles: bool = False,
        subtitle_path: str | None = None,
    ) -> list[str]:
        vf_map = {
            "9:16": "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
            "1:1": "scale=1080:1080:force_original_aspect_ratio=decrease,pad=1080:1080:(ow-iw)/2:(oh-ih)/2",
            "16:9": "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
        }
        if aspect_ratio not in vf_map:
            raise ValueError(f"Unsupported ratio: {aspect_ratio}")

        filters = [vf_map[aspect_ratio]]
        if add_subtitles and subtitle_path:
            filters.append(f"subtitles={subtitle_path}")

        return [
            self.ffmpeg_bin,
            "-y",
            "-i",
            input_path,
            "-vf",
            ",".join(filters),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-c:a",
            "aac",
            output_path,
        ]

    def run_export(self, command: list[str]) -> subprocess.CompletedProcess:
        if not self.is_available():
            raise RuntimeError("ffmpeg is not available in PATH")
        return subprocess.run(command, capture_output=True, text=True, check=False)

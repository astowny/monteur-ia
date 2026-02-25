from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from urllib import request

from ai_service.models.schemas import TranscriptSegment


class WhisperService:
    def __init__(self, whisper_bin: str = "whisper") -> None:
        self.whisper_bin = whisper_bin

    def transcribe_local(self, audio_path: str, language: str) -> list[TranscriptSegment]:
        if not Path(audio_path).exists():
            raise FileNotFoundError(audio_path)

        cmd = [
            self.whisper_bin,
            audio_path,
            "--language",
            language,
            "--output_format",
            "json",
            "--model",
            "base",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=900)
        if proc.returncode != 0:
            raise RuntimeError(f"whisper local failed: {proc.stderr.strip()}")

        json_path = Path(audio_path).with_suffix(".json")
        if not json_path.exists():
            raise RuntimeError("Whisper completed but json output was not found")

        data = json.loads(json_path.read_text())
        return [
            TranscriptSegment(
                start=float(seg.get("start", 0.0)),
                end=float(seg.get("end", 0.0)),
                text=str(seg.get("text", "")).strip(),
                confidence=0.9,
                speaker="S1",
            )
            for seg in data.get("segments", [])
        ]

    def transcribe_api(self, audio_path: str, language: str) -> list[TranscriptSegment]:
        api_url = os.getenv("WHISPER_API_URL", "")
        api_key = os.getenv("WHISPER_API_KEY", "")
        if not api_url:
            raise RuntimeError("WHISPER_API_URL is not configured")

        payload = json.dumps({"audio_path": audio_path, "language": language}).encode()
        req = request.Request(
            api_url,
            data=payload,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )

        last_error: Exception | None = None
        for attempt in range(3):
            try:
                with request.urlopen(req, timeout=30) as response:  # noqa: S310
                    content = json.loads(response.read().decode())
                segments = content.get("segments", [])
                return [
                    TranscriptSegment(
                        start=float(seg.get("start", 0.0)),
                        end=float(seg.get("end", 0.0)),
                        text=str(seg.get("text", "")),
                        confidence=float(seg.get("confidence", 0.85)),
                        speaker=seg.get("speaker", "S1"),
                    )
                    for seg in segments
                ]
            except Exception as exc:  # network or parse issues
                last_error = exc
                if attempt < 2:
                    time.sleep(2**attempt)
        raise RuntimeError(f"whisper api failed after retries: {last_error}")

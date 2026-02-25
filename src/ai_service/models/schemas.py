from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str
    confidence: float
    speaker: str | None = None


@dataclass
class TranscribeRequest:
    video_path: str
    language: str = "fr"


@dataclass
class TranscribeResponse:
    segments: list[TranscriptSegment]


@dataclass
class DetectSilencesRequest:
    durations: list[float] = field(default_factory=list)
    amplitudes: list[float] = field(default_factory=list)
    silence_threshold: float = 0.12


@dataclass
class SilenceSegment:
    start: float
    end: float


@dataclass
class DetectSilencesResponse:
    silences: list[SilenceSegment]


@dataclass
class MomentCandidate:
    start: float
    end: float
    score: float
    reasons: list[str]


@dataclass
class ScoreMomentsRequest:
    transcript: list[TranscriptSegment] = field(default_factory=list)
    audio_peaks: list[float] = field(default_factory=list)
    speech_rates: list[float] = field(default_factory=list)


@dataclass
class ScoreMomentsResponse:
    candidates: list[MomentCandidate]


@dataclass
class GenerateHooksRequest:
    transcript: list[TranscriptSegment]
    style: Literal["business", "podcast", "story", "generic"] = "generic"
    limit: int = 3


@dataclass
class GenerateHooksResponse:
    hooks: list[str]


@dataclass
class ProjectCreateRequest:
    video_path: str
    project_id: str


@dataclass
class ProjectCreateResponse:
    project_id: str
    metadata: dict[str, str | int | float]


@dataclass
class ExportRequest:
    input_path: str
    output_path: str
    aspect_ratio: Literal["9:16", "1:1", "16:9"]
    add_subtitles: bool = False
    subtitle_path: str | None = None


@dataclass
class ExportResponse:
    command: list[str]
    output_path: str


@dataclass
class WhisperApiRequest:
    audio_path: str
    language: str = "fr"


@dataclass
class CloudJobRequest:
    operation: Literal["viral-score", "hook-generation", "transcribe"]
    payload: dict


@dataclass
class CloudJob:
    id: str
    operation: str
    payload: dict
    status: Literal["queued", "processing", "done", "failed"]
    result: dict | None = None


@dataclass
class CloudJobResponse:
    job: CloudJob


@dataclass
class AnalyticsEvent:
    name: str
    properties: dict[str, str | int | float]


@dataclass
class ExportPlatformRequest:
    platform: Literal["youtube", "tiktok"]
    file_path: str
    title: str


@dataclass
class ExportPlatformResponse:
    platform: str
    status: str
    external_id: str

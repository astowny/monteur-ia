from pathlib import Path

import pytest

from ai_service.core.config import Settings, validate_settings
from ai_service.main import (
    create_project,
    enqueue_cloud_job,
    export_to_platform,
    get_analytics,
    get_cloud_job,
    prepare_export,
    process_cloud_job,
)
from ai_service.models.schemas import (
    CloudJobRequest,
    ExportPlatformRequest,
    ExportRequest,
    ProjectCreateRequest,
    ScoreMomentsRequest,
    TranscriptSegment,
)
from ai_service.services.hooks import HookService
from ai_service.services.silence import SilenceDetectionService
from ai_service.services.transcription import TranscriptionService
from ai_service.services.viral import ViralScoringService


def test_silence_detection_returns_segments():
    service = SilenceDetectionService()
    silences = service.detect(
        durations=[0.1, 0.2, 0.3, 0.5, 0.2],
        amplitudes=[0.9, 0.1, 0.05, 0.8, 0.01],
        threshold=0.12,
    )
    assert len(silences) == 1
    assert silences[0].start == 0.1


def test_viral_scoring_orders_by_score_desc():
    service = ViralScoringService()
    transcript = [
        TranscriptSegment(start=0, end=2, text="c'est important", confidence=0.9),
        TranscriptSegment(start=2, end=5, text="phrase neutre", confidence=0.9),
    ]
    result = service.score(transcript, audio_peaks=[0.9, 0.1], speech_rates=[0.8, 0.1])
    assert result[0].score >= result[1].score


def test_hooks_generation_limit():
    hooks = HookService().generate(
        transcript=[
            TranscriptSegment(start=0, end=2, text="J'ai fait une erreur majeure.", confidence=0.9),
            TranscriptSegment(start=2, end=4, text="Puis j'ai trouvé un système.", confidence=0.9),
        ],
        style="story",
        limit=1,
    )
    assert len(hooks) == 1


def test_request_model_defaults():
    req = ScoreMomentsRequest()
    assert req.transcript == []
    assert req.audio_peaks == []


def test_project_create_and_export_command(tmp_path: Path):
    video = tmp_path / "input.mp4"
    video.write_bytes(b"fake")

    project = create_project(ProjectCreateRequest(video_path=str(video), project_id="p1"))
    assert project.project_id == "p1"
    assert project.metadata["name"] == "input.mp4"

    export = prepare_export(
        ExportRequest(
            input_path=str(video),
            output_path=str(tmp_path / "out.mp4"),
            aspect_ratio="9:16",
            add_subtitles=True,
            subtitle_path="captions.srt",
        )
    )
    assert export.command[0] == "ffmpeg"
    assert "subtitles=captions.srt" in export.command[5]


def test_cloud_job_and_platform_export():
    queued = enqueue_cloud_job(CloudJobRequest(operation="viral-score", payload={"clip": "a"}))
    assert queued.job.status == "queued"

    done = process_cloud_job(queued.job.id)
    assert done.job.status == "done"
    assert done.job.result and done.job.result["ok"] is True

    retrieved = get_cloud_job(queued.job.id)
    assert retrieved.status == "done"

    export = export_to_platform(
        ExportPlatformRequest(platform="youtube", file_path="/tmp/x.mp4", title="Test")
    )
    assert export.platform == "youtube"
    assert export.status == "queued"

    events = get_analytics()
    assert len(events) >= 1


def test_validate_settings_forbid_stub_in_prod():
    with pytest.raises(RuntimeError):
        validate_settings(Settings(app_env="prod", transcribe_mode="stub", api_key="k"))


def test_validate_settings_requires_whisper_api_config():
    with pytest.raises(RuntimeError):
        validate_settings(Settings(app_env="prod", transcribe_mode="api", api_key="k"))


def test_transcription_stub_mode(monkeypatch):
    monkeypatch.setenv("MONTEUR_TRANSCRIBE_MODE", "stub")
    service = TranscriptionService()
    segs = service.transcribe("/tmp/does-not-matter.mp4", "fr")
    assert len(segs) == 3
    monkeypatch.delenv("MONTEUR_TRANSCRIBE_MODE", raising=False)

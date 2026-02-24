from __future__ import annotations

import logging
import shutil
from functools import wraps

from ai_service.core.config import Settings, load_settings
from ai_service.core.logging_utils import configure_logging
from ai_service.core.security import AuthService, RateLimiter
from ai_service.models.schemas import (
    CloudJob,
    CloudJobRequest,
    CloudJobResponse,
    DetectSilencesRequest,
    DetectSilencesResponse,
    ExportPlatformRequest,
    ExportPlatformResponse,
    ExportRequest,
    ExportResponse,
    GenerateHooksRequest,
    GenerateHooksResponse,
    ProjectCreateRequest,
    ProjectCreateResponse,
    ScoreMomentsRequest,
    ScoreMomentsResponse,
    TranscriptSegment,
    TranscribeRequest,
    TranscribeResponse,
)
from ai_service.repositories.sqlite_repo import SqliteRepository
from ai_service.services.cloud import AnalyticsService, CloudJobService, PlatformExportService
from ai_service.services.ffmpeg_pipeline import FFmpegPipelineService
from ai_service.services.hooks import HookService
from ai_service.services.silence import SilenceDetectionService
from ai_service.services.transcription import TranscriptionService
from ai_service.services.viral import ViralScoringService

configure_logging()
logger = logging.getLogger("ai_service")

settings: Settings = load_settings()
repository = SqliteRepository(settings.sqlite_path)
transcription_service = TranscriptionService()
silence_service = SilenceDetectionService()
viral_service = ViralScoringService()
hook_service = HookService()
ffmpeg_service = FFmpegPipelineService(settings.ffmpeg_bin)
cloud_jobs = CloudJobService(repository)
analytics = AnalyticsService(repository)
platform_export = PlatformExportService()
auth = AuthService(settings.api_key)
rate_limiter = RateLimiter(max_requests=120, window_seconds=60)


class AppError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


def require_auth_and_quota(client_id: str, api_key: str | None) -> None:
    if not auth.verify_api_key(api_key):
        raise AppError("unauthorized", status_code=401)
    if not rate_limiter.allow(client_id):
        raise AppError("rate_limit_exceeded", status_code=429)


def create_project(req: ProjectCreateRequest) -> ProjectCreateResponse:
    metadata = ffmpeg_service.probe_metadata(req.video_path)
    analytics.track("project_created", {"project_id": req.project_id, "size_bytes": metadata["size_bytes"]})
    logger.info("project_created", extra={"extra_payload": {"project_id": req.project_id}})
    return ProjectCreateResponse(project_id=req.project_id, metadata=metadata)


def prepare_export(req: ExportRequest) -> ExportResponse:
    command = ffmpeg_service.build_export_command(
        input_path=req.input_path,
        output_path=req.output_path,
        aspect_ratio=req.aspect_ratio,
        add_subtitles=req.add_subtitles,
        subtitle_path=req.subtitle_path,
    )
    analytics.track("export_prepared", {"ratio": req.aspect_ratio})
    return ExportResponse(command=command, output_path=req.output_path)


def transcribe(req: TranscribeRequest) -> TranscribeResponse:
    segments = transcription_service.transcribe(req.video_path, req.language)
    analytics.track("transcription_done", {"segments": len(segments)})
    return TranscribeResponse(segments=segments)


def detect_silences(req: DetectSilencesRequest) -> DetectSilencesResponse:
    silences = silence_service.detect(req.durations, req.amplitudes, req.silence_threshold)
    analytics.track("silence_detection_done", {"silences": len(silences)})
    return DetectSilencesResponse(silences=silences)


def score_moments(req: ScoreMomentsRequest) -> ScoreMomentsResponse:
    candidates = viral_service.score(req.transcript, req.audio_peaks, req.speech_rates)
    analytics.track("moments_scored", {"candidates": len(candidates)})
    return ScoreMomentsResponse(candidates=candidates)


def generate_hooks(req: GenerateHooksRequest) -> GenerateHooksResponse:
    hooks = hook_service.generate(req.transcript, req.style, req.limit)
    analytics.track("hooks_generated", {"count": len(hooks)})
    return GenerateHooksResponse(hooks=hooks)


def enqueue_cloud_job(req: CloudJobRequest) -> CloudJobResponse:
    job = cloud_jobs.enqueue(req.operation, req.payload)
    return CloudJobResponse(job=job)


def process_cloud_job(job_id: str) -> CloudJobResponse:
    job = cloud_jobs.process(job_id)
    return CloudJobResponse(job=job)


def get_cloud_job(job_id: str) -> CloudJob:
    try:
        return cloud_jobs.get(job_id)
    except KeyError as exc:
        raise AppError("job_not_found", status_code=404) from exc


def export_to_platform(req: ExportPlatformRequest) -> ExportPlatformResponse:
    res = platform_export.export(req.platform, req.file_path, req.title)
    analytics.track("platform_export_queued", {"platform": req.platform})
    return res


def get_analytics() -> list[dict]:
    return analytics.dump()


def runtime_checks() -> dict[str, str | bool]:
    return {
        "ffmpeg_available": ffmpeg_service.is_available(),
        "whisper_available": shutil.which(settings.whisper_bin) is not None,
        "transcribe_mode": settings.transcribe_mode,
        "environment": settings.app_env,
    }


def create_fastapi_app():
    """Production FastAPI adapter with auth, quota and unified errors."""
    from fastapi import FastAPI, Header, Request
    from fastapi.responses import JSONResponse

    app = FastAPI(title="Monteur IA Local Service", version="0.3.0")

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content={"error": str(exc)})

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_: Request, exc: Exception):
        logger.exception("unhandled_exception", extra={"extra_payload": {"error": str(exc)}})
        return JSONResponse(status_code=500, content={"error": "internal_server_error"})

    def guarded(handler):
        @wraps(handler)
        def wrapper(*args, x_api_key: str | None = Header(default=None), request: Request, **kwargs):
            client_id = request.client.host if request.client else "unknown"
            require_auth_and_quota(client_id, x_api_key)
            return handler(*args, **kwargs)

        return wrapper

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/runtime")
    def health_runtime() -> dict[str, str | bool]:
        return runtime_checks()

    @app.post("/project/create")
    @guarded
    def create_project_http(req: dict) -> dict:
        response = create_project(ProjectCreateRequest(**req))
        return {"project_id": response.project_id, "metadata": response.metadata}

    @app.post("/pipeline/export/prepare")
    @guarded
    def prepare_export_http(req: dict) -> dict:
        response = prepare_export(ExportRequest(**req))
        return {"command": response.command, "output_path": response.output_path}

    @app.post("/transcribe")
    @guarded
    def transcribe_http(req: dict) -> dict:
        response = transcribe(TranscribeRequest(**req))
        return {"segments": [s.__dict__ for s in response.segments]}

    @app.post("/detect-silences")
    @guarded
    def detect_silences_http(req: dict) -> dict:
        response = detect_silences(DetectSilencesRequest(**req))
        return {"silences": [s.__dict__ for s in response.silences]}

    @app.post("/score-moments")
    @guarded
    def score_moments_http(req: dict) -> dict:
        transcript = [TranscriptSegment(**t) for t in req.get("transcript", [])]
        response = score_moments(
            ScoreMomentsRequest(
                transcript=transcript,
                audio_peaks=req.get("audio_peaks", []),
                speech_rates=req.get("speech_rates", []),
            )
        )
        return {"candidates": [c.__dict__ for c in response.candidates]}

    @app.post("/generate-hooks")
    @guarded
    def generate_hooks_http(req: dict) -> dict:
        transcript = [TranscriptSegment(**t) for t in req.get("transcript", [])]
        response = generate_hooks(
            GenerateHooksRequest(
                transcript=transcript,
                style=req.get("style", "generic"),
                limit=req.get("limit", 3),
            )
        )
        return {"hooks": response.hooks}

    @app.post("/cloud/jobs")
    @guarded
    def enqueue_cloud_job_http(req: dict) -> dict:
        response = enqueue_cloud_job(CloudJobRequest(**req))
        return {"job": response.job.__dict__}

    @app.post("/cloud/jobs/{job_id}/process")
    @guarded
    def process_cloud_job_http(job_id: str) -> dict:
        response = process_cloud_job(job_id)
        return {"job": response.job.__dict__}

    @app.get("/cloud/jobs/{job_id}")
    @guarded
    def get_cloud_job_http(job_id: str) -> dict:
        return get_cloud_job(job_id).__dict__

    @app.post("/platform/export")
    @guarded
    def export_to_platform_http(req: dict) -> dict:
        response = export_to_platform(ExportPlatformRequest(**req))
        return response.__dict__

    @app.get("/analytics/events")
    @guarded
    def analytics_http() -> dict:
        return {"events": get_analytics()}

    return app

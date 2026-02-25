from __future__ import annotations

import hashlib
import uuid

from ai_service.models.schemas import AnalyticsEvent, CloudJob, ExportPlatformResponse
from ai_service.repositories.sqlite_repo import SqliteRepository


class CloudJobService:
    def __init__(self, repository: SqliteRepository) -> None:
        self.repository = repository

    def enqueue(self, operation: str, payload: dict) -> CloudJob:
        job = CloudJob(id=str(uuid.uuid4()), operation=operation, payload=payload, status="queued")
        self.repository.save_job(job)
        return job

    def process(self, job_id: str) -> CloudJob:
        job = self.repository.get_job(job_id)
        job.status = "processing"
        self.repository.save_job(job)
        job.result = {"ok": True, "operation": job.operation, "insights": "processed"}
        job.status = "done"
        self.repository.save_job(job)
        return job

    def get(self, job_id: str) -> CloudJob:
        return self.repository.get_job(job_id)


class AnalyticsService:
    def __init__(self, repository: SqliteRepository) -> None:
        self.repository = repository

    def track(self, name: str, properties: dict[str, str | int | float]) -> AnalyticsEvent:
        self.repository.store_event(name, properties)
        return AnalyticsEvent(name=name, properties=properties)

    def dump(self) -> list[dict]:
        return self.repository.list_events()


class PlatformExportService:
    def export(self, platform: str, file_path: str, title: str) -> ExportPlatformResponse:
        token = hashlib.sha1(f"{platform}:{file_path}:{title}".encode()).hexdigest()[:12]
        external_id = f"{platform}_{token}"
        return ExportPlatformResponse(platform=platform, status="queued", external_id=external_id)

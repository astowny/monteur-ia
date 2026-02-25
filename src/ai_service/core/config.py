from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Settings:
    app_env: str = "dev"
    transcribe_mode: str = "stub"
    whisper_api_url: str = ""
    whisper_api_key: str = ""
    api_key: str = ""
    ffmpeg_bin: str = "ffmpeg"
    whisper_bin: str = "whisper"
    sqlite_path: str = "storage/monteur.db"

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {"prod", "production"}


def load_settings() -> Settings:
    settings = Settings(
        app_env=os.getenv("MONTEUR_ENV", "dev"),
        transcribe_mode=os.getenv("MONTEUR_TRANSCRIBE_MODE", "stub"),
        whisper_api_url=os.getenv("WHISPER_API_URL", ""),
        whisper_api_key=os.getenv("WHISPER_API_KEY", ""),
        api_key=os.getenv("MONTEUR_API_KEY", ""),
        ffmpeg_bin=os.getenv("MONTEUR_FFMPEG_BIN", "ffmpeg"),
        whisper_bin=os.getenv("MONTEUR_WHISPER_BIN", "whisper"),
        sqlite_path=os.getenv("MONTEUR_SQLITE_PATH", "storage/monteur.db"),
    )
    validate_settings(settings)
    return settings


def validate_settings(settings: Settings) -> None:
    if settings.transcribe_mode not in {"stub", "local", "api"}:
        raise RuntimeError("MONTEUR_TRANSCRIBE_MODE must be one of: stub, local, api")

    if settings.is_production and settings.transcribe_mode == "stub":
        raise RuntimeError("stub transcription mode is forbidden in production")

    if settings.transcribe_mode == "api":
        if not settings.whisper_api_url:
            raise RuntimeError("WHISPER_API_URL is required when MONTEUR_TRANSCRIBE_MODE=api")
        if not settings.whisper_api_key:
            raise RuntimeError("WHISPER_API_KEY is required when MONTEUR_TRANSCRIBE_MODE=api")

    if settings.is_production and not settings.api_key:
        raise RuntimeError("MONTEUR_API_KEY is required in production")

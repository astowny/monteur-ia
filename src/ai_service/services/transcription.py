from __future__ import annotations

import os

from ai_service.models.schemas import TranscriptSegment
from ai_service.services.whisper import WhisperService


class TranscriptionService:
    """Transcription service with local whisper or API fallback."""

    def __init__(self, whisper_service: WhisperService | None = None) -> None:
        self.whisper = whisper_service or WhisperService()

    def transcribe(self, video_path: str, language: str) -> list[TranscriptSegment]:
        mode = os.getenv("MONTEUR_TRANSCRIBE_MODE", "stub")
        if mode == "local":
            return self.whisper.transcribe_local(video_path, language)
        if mode == "api":
            return self.whisper.transcribe_api(video_path, language)

        return [
            TranscriptSegment(
                start=0.0,
                end=3.1,
                text="Bienvenue, aujourd'hui on transforme une vidéo longue en shorts.",
                confidence=0.94,
                speaker="S1",
            ),
            TranscriptSegment(
                start=3.1,
                end=7.8,
                text="Le vrai levier, ce n'est pas le montage manuel, c'est l'automatisation.",
                confidence=0.92,
                speaker="S1",
            ),
            TranscriptSegment(
                start=7.8,
                end=12.4,
                text="Je te montre les 3 étapes qui font gagner des heures chaque semaine.",
                confidence=0.95,
                speaker="S1",
            ),
        ]

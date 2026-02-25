from __future__ import annotations

from ai_service.models.schemas import MomentCandidate, TranscriptSegment

EMOTIONAL_WORDS = {
    "erreur",
    "secret",
    "incroyable",
    "grave",
    "important",
    "gagner",
    "perdu",
    "levier",
    "étapes",
}


class ViralScoringService:
    """Implements V1 heuristic scoring described in product docs."""

    def score(
        self,
        transcript: list[TranscriptSegment],
        audio_peaks: list[float],
        speech_rates: list[float],
    ) -> list[MomentCandidate]:
        candidates: list[MomentCandidate] = []

        for idx, segment in enumerate(transcript):
            text = segment.text.lower()
            lexical = min(1.0, sum(1 for w in EMOTIONAL_WORDS if w in text) / 3)
            peak = audio_peaks[idx] if idx < len(audio_peaks) else 0.5
            speech_rate_delta = speech_rates[idx] if idx < len(speech_rates) else 0.5
            pause_contrast = 0.7 if idx > 0 and transcript[idx - 1].end < segment.start + 0.1 else 0.3
            visual_motion = 0.4

            score = (
                0.30 * peak
                + 0.25 * lexical
                + 0.20 * speech_rate_delta
                + 0.15 * pause_contrast
                + 0.10 * visual_motion
            )

            reasons: list[str] = []
            if peak > 0.7:
                reasons.append("audio_peak")
            if lexical > 0.4:
                reasons.append("emotional_phrase")
            if speech_rate_delta > 0.7:
                reasons.append("high_speech_rate")
            if not reasons:
                reasons.append("balanced_signal")

            candidates.append(
                MomentCandidate(
                    start=segment.start,
                    end=segment.end,
                    score=round(score, 3),
                    reasons=reasons,
                )
            )

        return sorted(candidates, key=lambda c: c.score, reverse=True)

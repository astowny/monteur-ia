from __future__ import annotations

from ai_service.models.schemas import SilenceSegment


class SilenceDetectionService:
    def detect(self, durations: list[float], amplitudes: list[float], threshold: float) -> list[SilenceSegment]:
        if not durations or not amplitudes or len(durations) != len(amplitudes):
            return []

        silences: list[SilenceSegment] = []
        cursor = 0.0
        active_start: float | None = None

        for duration, amplitude in zip(durations, amplitudes, strict=True):
            next_cursor = cursor + duration
            if amplitude < threshold:
                if active_start is None:
                    active_start = cursor
            elif active_start is not None:
                silences.append(SilenceSegment(start=active_start, end=cursor))
                active_start = None
            cursor = next_cursor

        if active_start is not None:
            silences.append(SilenceSegment(start=active_start, end=cursor))

        return [s for s in silences if (s.end - s.start) >= 0.25]

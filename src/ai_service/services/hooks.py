from __future__ import annotations

from ai_service.models.schemas import TranscriptSegment

STYLE_PREFIX = {
    "business": ["Les 3 erreurs", "Ce que personne ne te dit", "Le système qui"],
    "podcast": ["Moment clé du podcast", "L'avis qui va diviser", "La phrase à retenir"],
    "story": ["J'ai fait cette erreur", "Le déclic qui m'a tout appris", "Ce qui a tout changé"],
    "generic": ["Tu fais sûrement ça aussi", "Le point clé en 20 secondes", "À ne pas manquer"],
}


class HookService:
    def generate(self, transcript: list[TranscriptSegment], style: str, limit: int) -> list[str]:
        top_phrases = [seg.text for seg in transcript[: max(1, min(len(transcript), limit))]]
        prefixes = STYLE_PREFIX.get(style, STYLE_PREFIX["generic"])

        hooks: list[str] = []
        for idx, phrase in enumerate(top_phrases):
            base = phrase.split(",")[0].strip(" .")
            prefix = prefixes[idx % len(prefixes)]
            hooks.append(f"{prefix} : {base}")

        return hooks[:limit]

# Production readiness checklist — Monteur IA

Ce document décrit ce qui est implémenté et ce qui reste à faire pour un go-live robuste.

## Déjà implémenté

- Validation de configuration au démarrage (`MONTEUR_ENV`, `MONTEUR_TRANSCRIBE_MODE`, API key en prod).
- Interdiction du mode `stub` en production.
- Validation des variables Whisper API en mode `api`.
- Auth API key sur endpoints HTTP métier.
- Rate limiting (fenêtre glissante en mémoire).
- Logs JSON structurés.
- Gestion d’erreurs homogène (`AppError` + handler global).
- Retries + timeout côté Whisper API.
- Persistance SQLite pour jobs cloud et analytics.

## À compléter avant vraie prod multi-instance

- Remplacer le rate limiter en mémoire par Redis.
- Ajouter JWT + RBAC par rôle/plan.
- Brancher object storage (S3/GCS) pour médias et artifacts.
- Brancher vraie queue (Redis/RQ, Celery, SQS, etc.).
- Ajouter tracing OpenTelemetry + alerting (latence, erreurs, saturation).
- Implémenter CI/CD release + E2E FFmpeg/Whisper réels.
- Signer l’exécutable Windows + auto-update sécurisé.

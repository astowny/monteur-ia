# Monteur IA

Implémentation MVP des blocs techniques majeurs définis dans le plan 12 mois :
- shell desktop (scaffold Electron),
- pipeline FFmpeg (import/probe + préparation d'exports 9:16, 1:1, 16:9 + sous-titres burn-in),
- transcription Whisper (local CLI ou API),
- cloud jobs Pro (queue), analytics, export plateformes.

## Structure

- `src/ai_service/main.py` : orchestration + endpoints FastAPI (auth + rate limit + erreurs unifiées).
- `src/ai_service/services/ffmpeg_pipeline.py` : pipeline vidéo FFmpeg.
- `src/ai_service/services/whisper.py` : intégration Whisper local/API (+ retries API).
- `src/ai_service/services/cloud.py` : jobs + analytics avec persistance SQLite.
- `src/ai_service/repositories/sqlite_repo.py` : persistance jobs/events.
- `desktop/electron-shell/` : shell desktop Electron minimal.

## API métier implémentée

- Projet / pipeline
  - `create_project`
  - `prepare_export`
- IA locale
  - `transcribe`
  - `detect_silences`
  - `score_moments`
  - `generate_hooks`
- Cloud Pro
  - `enqueue_cloud_job`
  - `process_cloud_job`
  - `get_cloud_job`
  - `export_to_platform`
  - `get_analytics`

## Endpoints HTTP (FastAPI)

- `GET /health`
- `GET /health/runtime`
- `POST /project/create`
- `POST /pipeline/export/prepare`
- `POST /transcribe`
- `POST /detect-silences`
- `POST /score-moments`
- `POST /generate-hooks`
- `POST /cloud/jobs`
- `POST /cloud/jobs/{job_id}/process`
- `GET /cloud/jobs/{job_id}`
- `POST /platform/export`
- `GET /analytics/events`

> Les endpoints métier exigent le header `x-api-key` quand `MONTEUR_API_KEY` est configurée.

## Tests

```bash
pytest -q
```

## Lancer l'API HTTP

```bash
python -c "from ai_service.main import create_fastapi_app; app=create_fastapi_app(); import uvicorn; uvicorn.run(app, host='127.0.0.1', port=8000)"
```

## Lancer le shell desktop

```bash
cd desktop/electron-shell
npm install
npm start
```

## Variables d'environnement (production)

- `MONTEUR_ENV=prod|staging|dev`
- `MONTEUR_API_KEY` (obligatoire en `prod`)
- `MONTEUR_TRANSCRIBE_MODE=local|api` (`stub` interdit en `prod`)
- `WHISPER_API_URL` (obligatoire si mode `api`)
- `WHISPER_API_KEY` (obligatoire si mode `api`)
- `MONTEUR_FFMPEG_BIN` (default: `ffmpeg`)
- `MONTEUR_WHISPER_BIN` (default: `whisper`)
- `MONTEUR_SQLITE_PATH` (default: `storage/monteur.db`)

## Générer un `.exe` Windows

```bash
cd desktop/electron-shell
npm install
npm run dist:win
```

Guide complet: `docs/windows-build.md`


## Référence production

- Checklist: `docs/production-readiness.md`


## Mode Local / Prod et backend dans le même `.exe`

- Le shell Electron supporte maintenant une config runtime (UI) avec redémarrage backend.
- Le backend est lancé automatiquement par le shell:
  - priorité à `resources/backend/monteur-backend.exe` (release packagée),
  - fallback dev via `python -c ... uvicorn ...`.
- Guide détaillé: `docs/single-exe-runtime.md`.

# backend-dist

Dossier de dépôt du backend packagé pour distribution desktop.

Attendu en build Windows:
- `monteur-backend.exe` (ou équivalent)

Le shell Electron cherchera automatiquement:
- `%resources%/backend/monteur-backend.exe`

Sinon il utilisera un fallback dev (`python -c ... uvicorn ...`).

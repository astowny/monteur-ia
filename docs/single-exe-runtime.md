# Single EXE runtime (Electron + backend)

## Objectif
Avoir une expérience utilisateur où un seul `.exe` lance:
1. l'UI desktop,
2. le backend local API.

## Implémentation actuelle

- Le shell Electron démarre automatiquement le backend au boot.
- La config runtime est stockée dans `%APPDATA%/.../monteur-config.json` via l'API preload.
- Si un backend packagé est trouvé (`resources/backend/monteur-backend.exe`), il est lancé.
- Sinon fallback dev: lancement `python -c ... uvicorn ...`.

## Flux

1. `main.js` charge la config.
2. `main.js` lance backend (`exe` packagé ou python fallback).
3. `main.js` attend `GET /health`.
4. L'UI s'ouvre.
5. Quand l'utilisateur sauve config, backend redémarre avec nouvelles variables d'env.

## Packaging

- `desktop/electron-shell/package.json` inclut `extraResources` depuis `desktop/backend-dist`.
- Pour un vrai release, placer le binaire backend (`monteur-backend.exe`) dans `desktop/backend-dist/` avant `npm run dist:win`.

## Variables gérées via UI

- `MONTEUR_ENV`
- `MONTEUR_TRANSCRIBE_MODE`
- `MONTEUR_API_KEY`
- `WHISPER_API_URL`
- `WHISPER_API_KEY`

## Notes

- En mode `prod`, le backend refuse `stub`.
- En mode `api`, `WHISPER_API_URL` + `WHISPER_API_KEY` sont requis.

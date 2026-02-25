# Build Windows (.exe) — Monteur IA

Ce guide permet de générer un exécutable Windows du shell desktop Electron.

## 1) Prérequis

Sur une machine Windows (ou CI Windows):

- Node.js 20+
- npm 10+
- Git

> Pour un build `.exe` Windows fiable, il est recommandé de builder sur Windows.

## 2) Installation

```bash
cd desktop/electron-shell
npm install
```

## 3) Build exécutable

### Option A — Installateur NSIS (`.exe`)

```bash
npm run dist:win
```

Sortie attendue: dossier `desktop/electron-shell/dist/` avec un installateur `.exe`.

### Option B — Portable (`.exe` sans install)

```bash
npm run pack:win
```

Sortie attendue: `desktop/electron-shell/dist/Monteur IA*.exe`.

## 4) Test local direct de l'exe

1. Lancer l’API backend localement (dans un terminal séparé):

```bash
python -c "from ai_service.main import create_fastapi_app; app=create_fastapi_app(); import uvicorn; uvicorn.run(app, host='127.0.0.1', port=8000)"
```

2. Ouvrir l’exécutable généré (`Monteur IA*.exe`).
3. Vérifier que l’app s’ouvre et qu’elle cible bien `http://127.0.0.1:8000`.

## 5) Notes importantes

- Le shell actuel est un scaffold UI: il ouvre une fenêtre desktop et prépare l’intégration au backend.
- Les fonctions FFmpeg/Whisper dépendent des binaires/outils installés côté machine de test.
- Pour distribution publique, signer l’exécutable Windows est recommandé (code signing).

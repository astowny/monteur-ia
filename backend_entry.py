"""
Entry point PyInstaller pour monteur-backend.exe.
Lance le backend FastAPI via uvicorn sur 127.0.0.1:8000.
"""
import multiprocessing
import os
import pathlib
import sys

# Obligatoire pour PyInstaller + multiprocessing sur Windows
multiprocessing.freeze_support()


def _setup_logging():
    """
    En mode frozen (PyInstaller console=False), sys.stdout et sys.stderr
    sont None — uvicorn crashe au premier log.
    On redirige vers un fichier pour que le serveur démarre et que les
    erreurs soient lisibles.
    Le répertoire de log est fourni par MONTEUR_LOG_DIR (injecté par Electron)
    ou par défaut dans %APPDATA%/Monteur IA.
    """
    if not getattr(sys, "frozen", False):
        return  # dev : on garde les streams normaux

    log_dir = os.environ.get("MONTEUR_LOG_DIR", "")
    if not log_dir:
        log_dir = str(pathlib.Path(os.environ.get("APPDATA", ".")) / "Monteur IA")

    pathlib.Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_path = pathlib.Path(log_dir) / "backend.log"

    # line-buffered pour que les logs arrivent en temps réel
    log_file = open(log_path, "a", encoding="utf-8", buffering=1)
    sys.stdout = log_file
    sys.stderr = log_file


if __name__ == "__main__":
    _setup_logging()

    import uvicorn
    from ai_service.main import create_fastapi_app

    app = create_fastapi_app()
    uvicorn.run(app, host="127.0.0.1", port=8000)


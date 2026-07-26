@echo off
echo ============================================
echo   SLM Code Dataset Builder — Instalacja
echo ============================================
echo.

cd /d "%~dp0"

echo Instalowanie globalnej komendy 'slm-pipeline'...
pip install -e .

echo.
echo Gotowe! Od teraz mozesz uruchamiac z dowolnego miejsca:
echo.
echo   slm-pipeline
echo.
echo Aby odinstalowac:
echo   pip uninstall slm-code-dataset-builder
echo.
pause

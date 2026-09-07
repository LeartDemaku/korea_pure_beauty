@echo off
title Korea Pure Beauty - Dyqani
cd /d "%~dp0"
echo.
echo =====================================================
echo    🌸 Korea Pure Beauty - Duke hapur Dyqanin...
echo =====================================================
echo.
python -m streamlit run client_app.py --server.port 8502 --server.headless false --browser.gatherUsageStats false

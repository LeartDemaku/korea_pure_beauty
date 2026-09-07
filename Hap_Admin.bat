@echo off
title Korea Pure Beauty - Paneli i Administratorit
cd /d "%~dp0"
echo.
echo ========================================================================
echo    🌸 KOREA PURE BEAUTY - PANELI I ADMINISTRATORIT (Admin Terminal)
echo ========================================================================
echo.
echo  ✅ Funksionalitetet e Adminit:
echo     - Shto produkte te reja me Drag ^& Drop
echo     - Modifiko / Fshij produktet ekzistuese
echo     - Shiko te gjitha porositë e klienteve
echo     - Statistikat e inventarit
echo.
echo  🌐 Paneli i Adminit hapet ne: http://localhost:8501
echo  🌐 Dyqani i Klienteve eshte ne: http://localhost:8502
echo.
echo  ⚠️  KUJDES: Ky panel eshte VETEM per administratorin!
echo.
python -m streamlit run app.py --server.port 8501 --server.headless false --browser.gatherUsageStats false
pause

@echo off
chcp 65001 >nul
rem Genera el dashboard de la documentacion (skill dashboard-documentacion del plugin obsidian-docs).
rem La primera vez pregunta la ruta del repositorio de documentacion y la recuerda.
set "SCRIPT=%~dp0plugins\antigravity\obsidian-docs\skills\dashboard-documentacion\scripts\generar_dashboard.py"
where py >nul 2>nul
if %errorlevel%==0 (py -3 "%SCRIPT%" --abrir %*) else (python "%SCRIPT%" --abrir %*)
echo.
pause

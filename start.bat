@echo off
echo.
echo  ==========================================
echo   JarWiz - Local AI Assistant
echo  ==========================================
echo.

:: Check Ollama
curl -s http://localhost:11434 >nul 2>&1
if errorlevel 1 (
    echo  [!] Ollama не запущен. Запускаем...
    start "" "ollama" serve
    timeout /t 3 /nobreak >nul
)

:: Install deps if needed
py -m pip install flask flask-cors requests --quiet

echo  [*] Запускаем JarWiz...
echo  [*] Открываем браузер: http://localhost:5000
echo.
py server.py
pause

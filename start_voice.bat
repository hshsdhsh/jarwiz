@echo off
chcp 65001 >nul
echo.
echo  ==========================================
echo   JarWiz Voice Assistant
echo  ==========================================
echo.
echo  Устанавливаем зависимости...
py -m pip install SpeechRecognition pyttsx3 requests sounddevice --quiet
py -m pip install pyaudio --quiet 2>nul

echo.
echo  ==========================================
echo   Запускаем голосовой режим...
echo   Скажи "Jarwiz" чтобы активировать
echo  ==========================================
echo.

py voice.py
pause

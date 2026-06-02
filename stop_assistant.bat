@echo off
chcp 65001 >nul
echo Выключаем JarWiz...
taskkill /f /im pythonw.exe 2>nul
echo Ассистент успешно выключен.
timeout /t 2 >nul

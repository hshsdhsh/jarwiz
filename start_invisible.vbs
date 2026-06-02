Set WshShell = CreateObject("WScript.Shell")
' Запускает голосового ассистента в скрытом режиме (без окна консоли)
WshShell.Run "pyw voice.py", 0, False

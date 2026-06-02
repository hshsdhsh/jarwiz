# -*- coding: utf-8 -*-
"""
JarWiz Voice Assistant (Sounddevice Version)
Wake word: "jarwiz" / "jarvis" / "джарвиз"
STT: Google Speech Recognition via temp WAV files
TTS: pyttsx3 (100% offline)
AI:  Ollama (local)
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import json
import os
import subprocess
import time
import webbrowser
import asyncio
import threading
import wave
import requests
import speech_recognition as sr
import edge_tts
import soundfile as sf
import sounddevice as sd
import numpy as np

# ─── Config ───────────────────────────────────────────────────────────────────

OLLAMA_URL = "http://localhost:11434"
MODEL      = "qwen2.5:3b"       # Fast 3B model — instant responses!
WAKE_WORDS = [
    "jarwiz", "jarvis", "джарвиз", "жарвиз",
    "джарвис", "жарвис", "джервиз", "джервис",
]
LISTEN_LANG = "ru-RU"

# Temp files
TEMP_WAKE_FILE = "temp_wake.wav"
TEMP_CMD_FILE = "temp_cmd.wav"
TEMP_TTS_FILE = "temp_tts.mp3"

# ─── TTS Engine ───────────────────────────────────────────────────────────────

VOICE_NAME = "ru-RU-SvetlanaNeural"  # Svetlana (Female Neural Voice)
tts_lock = threading.Lock()

def speak(text: str):
    """Speaks text aloud using Edge TTS neural voice (thread-safe)"""
    clean = (text
        .replace("**", "").replace("*", "")
        .replace("#", "").replace("`", "")
        .replace("→", "").replace("•", "")
        .strip()
    )
    if not clean:
        return
    print(f"\n  [JarWiz]: {clean}\n", flush=True)
    
    async def _async_speak():
        try:
            # rate="+8%" makes her speak at a slightly faster, more natural, and energetic pace
            communicate = edge_tts.Communicate(clean, VOICE_NAME, rate="+8%")
            await communicate.save(TEMP_TTS_FILE)
            
            data, fs = sf.read(TEMP_TTS_FILE)
            sd.play(data, fs)
            sd.wait()
        except Exception as e:
            print(f"[TTS Error] {e}", flush=True)
        finally:
            if os.path.exists(TEMP_TTS_FILE):
                try:
                    os.remove(TEMP_TTS_FILE)
                except Exception:
                    pass

    with tts_lock:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_async_speak())
        loop.close()

# ─── System prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Ты JarWiz — голосовой AI-ассистент на ПК пользователя.
Правила:
1. Отвечай КРАТКО — 1-3 предложения максимум (ответ будет произнесён вслух)
2. Не используй markdown, списки со звёздочками, заголовки
3. Говори естественно, как человек
4. Отвечай на том же языке, на котором говорит пользователь

Когда пользователь просит совершить действие, ответь ТОЛЬКО специальной командой:

Для сайтов и приложений:
- Открыть приложение или сайт: ACTION:OPEN:название (например: "открой хром" -> ACTION:OPEN:chrome)
- Поиск в Google: ACTION:SEARCH:запрос (например: "найди погоду в Париже" -> ACTION:SEARCH:погода в Париже)

Для управления системой и браузером:
- Закрыть окно: ACTION:CLOSE_WINDOW
- Свернуть все окна: ACTION:MINIMIZE_ALL
- Громче звук: ACTION:VOLUME_UP
- Тише звук: ACTION:VOLUME_DOWN
- Выключить/включить звук (мутирование): ACTION:MUTE
- Листать/прокрутить вниз: ACTION:SCROLL_DOWN
- Листать/прокрутить вверх: ACTION:SCROLL_UP
- Закрыть текущую вкладку в браузере: ACTION:CLOSE_TAB
- Открыть новую вкладку в браузере: ACTION:NEW_TAB
- Вернуться назад (в браузере): ACTION:BACK
- Заблокировать компьютер/экран: ACTION:LOCK_SCREEN

Примеры:
- "закрой это окно" -> ACTION:CLOSE_WINDOW
- "сделай потише" -> ACTION:VOLUME_DOWN
- "закрой вкладку" -> ACTION:CLOSE_TAB
- "прокрути страницу ниже" -> ACTION:SCROLL_DOWN
- "сверни всё" -> ACTION:MINIMIZE_ALL
- "заблокируй комп" -> ACTION:LOCK_SCREEN
"""

history = []

# ─── Ollama ───────────────────────────────────────────────────────────────────

def get_model() -> str:
    """Returns the first available Ollama model"""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        models = r.json().get("models", [])
        if models:
            return models[0]["name"]
    except Exception:
        pass
    return MODEL

def ask_ollama(prompt: str) -> str:
    """Sends prompt to Ollama and returns response"""
    history.append({"role": "user", "content": prompt})
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history[-12:]

    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={"model": MODEL, "messages": messages, "stream": False},
            timeout=90,
        )
        response = r.json()["message"]["content"].strip()
        history.append({"role": "assistant", "content": response})
        return response
    except requests.exceptions.ConnectionError:
        return "Ollama не запущен. Запусти Ollama и попробуй снова."
    except Exception as e:
        return f"Ошибка: {str(e)}"

# ─── PC Actions ───────────────────────────────────────────────────────────────

APP_MAP = {
    "chrome":      "chrome",
    "firefox":     "firefox",
    "edge":        "msedge",
    "notepad":     "notepad",
    "блокнот":     "notepad",
    "calculator":  "calc",
    "калькулятор": "calc",
    "explorer":    "explorer",
    "проводник":   "explorer",
    "файлы":       "explorer",
    "vscode":      "code",
    "код":         "code",
    "spotify":     "spotify",
    "спотифай":    "spotify",
    "discord":     "discord",
    "дискорд":     "discord",
    "telegram":    "telegram",
    "телеграм":    "telegram",
    "word":        "winword",
    "excel":       "excel",
    "powershell":  "powershell",
    "cmd":         "cmd",
    "terminal":    "wt",
    "терминал":    "wt",
    "youtube":     "https://youtube.com",
    "ютуб":        "https://youtube.com",
    "google":      "https://google.com",
    "гугл":        "https://google.com",
    "github":      "https://github.com",
}

def clean_speech_target(target: str) -> str:
    """Helper to clean URL targets into readable names for speech"""
    if target.startswith("http://") or target.startswith("https://"):
        domain = target.replace("https://", "").replace("http://", "").replace("www.", "")
        domain = domain.split("/")[0].split(".")[0]
        return domain
    return target

def press_key(vk_code: int):
    """Simulates a key press (down and up) using Win32 API"""
    try:
        import ctypes
        ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
        time.sleep(0.05)
        ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0)
    except Exception as e:
        print(f"[Keybd Error] {e}")

def press_hotkey(mod_code: int, vk_code: int):
    """Simulates a modifier + key combination (e.g. Ctrl+W, Alt+F4)"""
    try:
        import ctypes
        ctypes.windll.user32.keybd_event(mod_code, 0, 0, 0)
        time.sleep(0.05)
        ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
        time.sleep(0.05)
        ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0)
        time.sleep(0.05)
        ctypes.windll.user32.keybd_event(mod_code, 0, 2, 0)
    except Exception as e:
        print(f"[Hotkey Error] {e}")

def find_and_run_app(app_name: str) -> bool:
    """Dynamically finds and runs an installed application shortcut from the Start Menu"""
    search_paths = [
        os.path.join(os.environ.get("APPDATA", ""), "Microsoft\\Windows\\Start Menu\\Programs"),
        "C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs",
    ]
    
    q_words = [w for w in app_name.lower().split() if len(w) > 2]
    if not q_words:
        q_words = [app_name.lower()]

    for path in search_paths:
        if not os.path.exists(path):
            continue
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".lnk"):
                    shortcut_name = os.path.splitext(file)[0].lower()
                    
                    # Fuzzy match words (e.g. match "музыку" or "музыка" or "yandex")
                    matched = False
                    for qw in q_words:
                        qw_root = qw[:-1] if len(qw) > 4 else qw
                        for sw in shortcut_name.split():
                            sw_root = sw[:-1] if len(sw) > 4 else sw
                            if qw_root in sw_root or sw_root in qw_root:
                                matched = True
                                break
                        if matched:
                            break
                            
                    if matched or app_name.lower() in shortcut_name or shortcut_name in app_name.lower():
                        shortcut_path = os.path.join(root, file)
                        try:
                            os.startfile(shortcut_path)
                            return True
                        except Exception as e:
                            print(f"[Launcher] Ошибка запуска ярлыка {file}: {e}")
    return False

def execute_action(response: str) -> str:
    """Parses ACTION commands and runs them"""
    if response.startswith("ACTION:OPEN:"):
        target = response.replace("ACTION:OPEN:", "").strip()
        
        # 1. Try predefined maps (Chrome, Edge, calc, etc.)
        url_or_app = APP_MAP.get(target.lower())
        if url_or_app:
            if url_or_app.startswith("http"):
                webbrowser.open(url_or_app)
                speech_name = clean_speech_target(target)
                return f"Открываю {speech_name}"
            else:
                try:
                    subprocess.Popen(url_or_app, shell=True)
                    speech_name = clean_speech_target(target)
                    return f"Запускаю {speech_name}"
                except Exception:
                    pass

        # 2. Try to search Start Menu dynamically (e.g. for Yandex Music)
        if find_and_run_app(target):
            speech_name = clean_speech_target(target)
            return f"Запускаю {speech_name}"

        # 3. Last resort: try direct execution via shell (if target is a raw cmd like 'notepad')
        try:
            subprocess.Popen(target, shell=True)
            speech_name = clean_speech_target(target)
            return f"Запускаю {speech_name}"
        except Exception as e:
            return f"Не удалось открыть {target}"

    elif response.startswith("ACTION:SEARCH:"):
        query = response.replace("ACTION:SEARCH:", "").strip()
        webbrowser.open(f"https://www.google.com/search?q={query}")
        return f"Ищу {query} в Google"

    elif response.startswith("ACTION:CLOSE_WINDOW"):
        press_hotkey(0x12, 0x73)  # Alt + F4
        return "Закрываю окно"

    elif response.startswith("ACTION:MINIMIZE_ALL"):
        subprocess.Popen("powershell -command \"(New-Object -ComObject shell.application).minimizeall()\"", shell=True)
        return "Сворачиваю все окна"

    elif response.startswith("ACTION:VOLUME_UP"):
        for _ in range(5):
            press_key(0xAF)  # VK_VOLUME_UP
        return "Делаю громче"

    elif response.startswith("ACTION:VOLUME_DOWN"):
        for _ in range(5):
            press_key(0xAE)  # VK_VOLUME_DOWN
        return "Делаю тише"

    elif response.startswith("ACTION:MUTE"):
        press_key(0xAD)  # VK_VOLUME_MUTE
        return "Переключаю звук"

    elif response.startswith("ACTION:SCROLL_DOWN"):
        press_key(0x22)  # VK_NEXT (Page Down)
        return "Листаю вниз"

    elif response.startswith("ACTION:SCROLL_UP"):
        press_key(0x21)  # VK_PRIOR (Page Up)
        return "Листаю вверх"

    elif response.startswith("ACTION:CLOSE_TAB"):
        press_hotkey(0x11, 0x57)  # Ctrl + W
        return "Закрываю вкладку"

    elif response.startswith("ACTION:NEW_TAB"):
        press_hotkey(0x11, 0x54)  # Ctrl + T
        return "Открываю новую вкладку"

    elif response.startswith("ACTION:BACK"):
        press_hotkey(0x12, 0x25)  # Alt + Left
        return "Возвращаюсь назад"

    elif response.startswith("ACTION:LOCK_SCREEN"):
        subprocess.Popen("rundll32.exe user32.dll,LockWorkStation", shell=True)
        return "Блокирую компьютер"

    return response

# ─── Audio Recording (no PyAudio!) ────────────────────────────────────────────

def record_to_file(filename: str, duration: float, fs: int = 16000, dynamic_silence: bool = True):
    """Records audio from microphone and saves to a WAV file.
    If dynamic_silence is True, stops automatically when user finishes speaking.
    """
    try:
        # If it's the quick wake word check, record fixed short duration
        if not dynamic_silence or duration < 3.0:
            recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
            sd.wait()
            audio_data = recording.tobytes()
        else:
            # Dynamic recording (VAD)
            chunk_duration = 0.2
            chunk_samples = int(chunk_duration * fs)
            chunks = []
            
            silence_threshold = 450  # Slightly lower threshold to be more sensitive to speech
            silence_limit = 1.8     # Stop after 1.8 seconds of silence to prevent premature cutoff
            
            silence_start = None
            start_time = time.time()
            
            # Open stream
            with sd.InputStream(samplerate=fs, channels=1, dtype='int16') as stream:
                while True:
                    data, overflowed = stream.read(chunk_samples)
                    chunks.append(data)
                    
                    # Calculate volume (max amplitude)
                    volume = np.max(np.abs(data))
                    
                    # Safety stop at max duration
                    if time.time() - start_time > duration:
                        break
                        
                    # Check silence
                    if volume < silence_threshold:
                        if silence_start is None:
                            silence_start = time.time()
                        elif time.time() - silence_start > silence_limit:
                            break
                    else:
                        silence_start = None
            
            recording = np.concatenate(chunks, axis=0)
            audio_data = recording.tobytes()

        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2) # 16-bit is 2 bytes
            wf.setframerate(fs)
            wf.writeframes(audio_data)
    except Exception as e:
        print(f"[Sounddevice] Ошибка записи: {e}")

def transcribe_file(filename: str, recognizer: sr.Recognizer) -> str:
    """Transcribes a WAV file using Google Web Speech API"""
    if not os.path.exists(filename):
        return ""
    
    with sr.AudioFile(filename) as source:
        audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio, language=LISTEN_LANG)
            return text.lower().strip()
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            print(f"[STT] Ошибка сервиса распознавания: {e}")
            return ""

def contains_wake_word(text: str) -> bool:
    """Checks if wake word is present in the text"""
    for word in WAKE_WORDS:
        if word in text:
            return True
    return False

# ─── Main Loop ────────────────────────────────────────────────────────────────

def main():
    global MODEL

    print("\n" + "=" * 52, flush=True)
    print("  JarWiz Voice Assistant (No-PyAudio)", flush=True)
    print("=" * 52, flush=True)

    # Detect model
    MODEL = get_model()
    print(f"  Модель:    {MODEL}", flush=True)
    print(f"  Wake word: jarwiz / джарвиз", flush=True)
    print(f"  Язык STT:  {LISTEN_LANG}", flush=True)
    print("=" * 52 + "\n", flush=True)

    recognizer = sr.Recognizer()

    # Welcome message
    threading.Thread(
        target=speak,
        args=("Я готов к работе. Скажи Джарвиз чтобы активировать.",),
        daemon=True,
    ).start()

    print("  Слушаю фоновый шум (ожидание активации)...", flush=True)
    
    while True:
        # Record 2.5 seconds to check for wake word
        record_to_file(TEMP_WAKE_FILE, duration=2.5)
        text = transcribe_file(TEMP_WAKE_FILE, recognizer)
        
        # Clean up temp wake file
        try:
            if os.path.exists(TEMP_WAKE_FILE):
                os.remove(TEMP_WAKE_FILE)
        except Exception:
            pass

        if not text:
            continue

        print(f"  [Фон] Распознано: '{text}'")

        if contains_wake_word(text):
            print("  [Wake Word Detected!]")
            speak("Джан, Джарвис здесь")
            
            # Record command (5 seconds)
            print("  [Запись команды...]")
            record_to_file(TEMP_CMD_FILE, duration=5.0)
            command = transcribe_file(TEMP_CMD_FILE, recognizer)
            
            # Clean up temp command file
            try:
                if os.path.exists(TEMP_CMD_FILE):
                    os.remove(TEMP_CMD_FILE)
            except Exception:
                pass

            if not command:
                speak("Я ничего не услышал")
                continue

            print(f"  Ты: {command}")

            # Слово отмены (Cancellation words)
            cancel_words = ["отмена", "стоп", "отставить", "забудь", "отменяй", "отменяем", "хватит", "молчи"]
            if any(cw in command for cw in cancel_words):
                speak("Поняла, отменяю")
                continue
            
            # Ask Ollama
            print("  Думаю...")
            response = ask_ollama(command)
            
            # Execute action if any
            result = execute_action(response)
            
            # Speak response
            speak(result)
            
            time.sleep(0.5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  JarWiz остановлен.")
        sys.exit(0)

# -*- coding: utf-8 -*-
"""
JarWiz - Local AI Assistant Backend
Powered by Ollama
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import json
import os
import subprocess
import threading
import webbrowser
from datetime import datetime

import requests
from flask import Flask, Response, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder="ui", static_url_path="/static")
CORS(app)

OLLAMA_URL = "http://localhost:11434"
CONVERSATION_HISTORY = []
MEMORY_FILE = "memory.json"

# ─── Memory ───────────────────────────────────────────────────────────────────

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_memory(history):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history[-100:], f, ensure_ascii=False, indent=2)


# ─── System prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are JarWiz, an advanced AI assistant running locally on the user's computer.
You are helpful, concise, and intelligent. You can:
- Answer any question
- Help with coding, writing, analysis
- Execute system commands when asked (opening apps, files, etc.)
- Remember the conversation context

When the user asks to open something or run a command, respond with a special JSON block like:
<cmd>{"action": "open", "target": "chrome"}</cmd>

Available actions: open (app/url), search (web query).
Always be friendly, direct and helpful. Respond in the same language the user writes in."""


# ─── Ollama integration ───────────────────────────────────────────────────────

def get_available_models():
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if r.status_code == 200:
            return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        pass
    return []


def stream_ollama(prompt: str, model: str, history: list):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in history[-20:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": prompt})

    try:
        with requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={"model": model, "messages": messages, "stream": True},
            stream=True,
            timeout=120,
        ) as resp:
            for line in resp.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        chunk = data.get("message", {}).get("content", "")
                        if chunk:
                            yield chunk
                        if data.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue
    except requests.exceptions.ConnectionError:
        yield "\n\n⚠️ **Ollama не запущен!** Запусти Ollama и попробуй снова."
    except Exception as e:
        yield f"\n\n⚠️ Ошибка: {str(e)}"


# ─── PC Actions ───────────────────────────────────────────────────────────────

APP_MAP = {
    "chrome": "chrome",
    "firefox": "firefox",
    "edge": "msedge",
    "notepad": "notepad",
    "calculator": "calc",
    "explorer": "explorer",
    "vscode": "code",
    "spotify": "spotify",
    "discord": "discord",
    "telegram": "telegram",
    "word": "winword",
    "excel": "excel",
    "powershell": "powershell",
    "cmd": "cmd",
    "terminal": "wt",
}


def execute_action(action_json: str):
    try:
        action = json.loads(action_json)
        act = action.get("action", "")
        target = action.get("target", "")

        if act == "open":
            if target.startswith("http"):
                webbrowser.open(target)
                return f"Открываю {target}"
            app_cmd = APP_MAP.get(target.lower(), target)
            subprocess.Popen(app_cmd, shell=True)
            return f"Запускаю {target}"

        elif act == "search":
            webbrowser.open(f"https://www.google.com/search?q={target}")
            return f"Ищу: {target}"

    except Exception as e:
        return f"Ошибка выполнения команды: {e}"
    return "Команда выполнена"


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("ui", "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    """Serve static files from ui/ directory"""
    return send_from_directory("ui", filename)


@app.route("/api/status")
def status():
    models = get_available_models()
    ollama_online = len(models) > 0
    return jsonify({
        "ollama": ollama_online,
        "models": models,
        "time": datetime.now().strftime("%H:%M"),
        "date": datetime.now().strftime("%d %B %Y"),
    })


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    user_msg = data.get("message", "").strip()
    model = data.get("model", "llama3.1")
    session_id = data.get("session_id", "default")

    if not user_msg:
        return jsonify({"error": "Empty message"}), 400

    history = load_memory()
    history.append({"role": "user", "content": user_msg, "time": datetime.now().isoformat()})

    full_response = []

    def generate():
        for chunk in stream_ollama(user_msg, model, history):
            full_response.append(chunk)
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"

        complete = "".join(full_response)

        # Check for commands in response
        if "<cmd>" in complete and "</cmd>" in complete:
            start = complete.index("<cmd>") + 5
            end = complete.index("</cmd>")
            cmd_json = complete[start:end]
            result = execute_action(cmd_json)
            yield f"data: {json.dumps({'action_result': result})}\n\n"

        history.append({"role": "assistant", "content": complete, "time": datetime.now().isoformat()})
        save_memory(history)
        yield f"data: {json.dumps({'done': True})}\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/api/history")
def get_history():
    return jsonify(load_memory())


@app.route("/api/clear", methods=["POST"])
def clear_history():
    save_memory([])
    return jsonify({"ok": True})


@app.route("/api/action", methods=["POST"])
def manual_action():
    data = request.json
    result = execute_action(json.dumps(data))
    return jsonify({"result": result})


# ─── Launch ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  JarWiz - Local AI Assistant")
    print("  Powered by Ollama")
    print("=" * 50)
    print(f"\n  UI:     http://localhost:5000")
    print(f"  Ollama: {OLLAMA_URL}")
    print("\n  Press Ctrl+C to stop\n")

    def open_browser():
        import time
        time.sleep(1.2)
        webbrowser.open("http://localhost:5000")

    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)

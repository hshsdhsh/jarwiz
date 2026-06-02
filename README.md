<div align="center">

# 🤖 JarWiz — Local AI Assistant

**Your privacy-first, offline AI assistant powered by [Ollama](https://ollama.com)**

![Python](https://img.shields.io/badge/Python-3.10+-3776ab?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=flat-square&logo=flask&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-local%20AI-ff6b35?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)

> Run powerful AI models **100% locally** — no internet, no API keys, no data leaving your PC.

</div>

---

## ✨ Features

- 💬 **Streaming chat** — real-time token-by-token responses
- 🧠 **Conversation memory** — context persists across messages (last 100 messages)
- 🎤 **Voice input** — speak your prompts via Web Speech API
- ⚡ **Quick PC actions** — open Chrome, VS Code, Notepad, Spotify and more in one click
- 🤖 **AI-controlled actions** — ask JarWiz to "open Chrome" and it will execute the command
- 🌙 **Dark glassmorphism UI** — sleek, animated interface
- 📝 **Markdown rendering** — code blocks, bold, lists, headers
- 🕐 **Live clock** — always visible in sidebar
- 🔒 **100% local** — all data stays on your machine

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Link |
|---|---|
| Python 3.10+ | [python.org](https://python.org) |
| Ollama | [ollama.com](https://ollama.com) |

### 1. Install Ollama & pull a model

```bash
# Install from https://ollama.com, then:
ollama pull mistral       # ~4GB, fast & capable
# or
ollama pull llama3.1      # ~5GB, very capable
# or
ollama pull phi3          # ~2GB, lightweight
```

### 2. Clone & install dependencies

```bash
git clone https://github.com/YOUR_USERNAME/jarwiz.git
cd jarwiz
pip install -r requirements.txt
```

### 3. Run JarWiz

```bash
# Windows (double-click or run):
start.bat

# Or directly:
py server.py
```

Then open **http://localhost:5000** in your browser. 🎉

---

## 🗂️ Project Structure

```
jarwiz/
├── server.py          # Flask backend + Ollama integration
├── start.bat          # One-click Windows launcher
├── requirements.txt   # Python dependencies
├── memory.json        # Chat history (auto-created, gitignored)
└── ui/
    ├── index.html     # Main UI
    ├── style.css      # Dark glassmorphism styles
    ├── app.js         # Frontend logic + SSE streaming
    └── markdown.js    # Lightweight markdown renderer
```

---

## 🔧 Configuration

Edit `server.py` to customize:

```python
OLLAMA_URL = "http://localhost:11434"   # Ollama server URL
MEMORY_FILE = "memory.json"             # Where history is saved
```

The **system prompt** (JarWiz's personality) is in the `SYSTEM_PROMPT` variable — feel free to personalize it.

---

## 🤖 Supported Models

Any model available in Ollama works. Recommended:

| Model | Size | Best For |
|---|---|---|
| `mistral` | 4.1GB | General purpose, fast |
| `llama3.1` | 4.7GB | Advanced reasoning |
| `phi3` | 2.3GB | Lightweight, quick |
| `codellama` | 3.8GB | Coding tasks |
| `gemma2` | 5.4GB | Google's model |

```bash
# List your installed models:
ollama list
```

---

## 🎤 Voice Input

Click the **microphone button** in the chat input. Works in Chrome/Edge (uses Web Speech API).
Supported languages: Russian, English, Armenian and any language your browser supports.

---

## ⚡ PC Actions

Ask JarWiz naturally:
- *"Open Chrome"* → opens Chrome
- *"Open VS Code"* → opens VS Code
- *"Search for Python tutorials"* → opens Google search

Or use the **Quick Actions** buttons in the sidebar.

---

## 🛣️ Roadmap

- [ ] Wake word detection ("Hey JarWiz")
- [ ] Text-to-speech responses (pyttsx3 / ElevenLabs)
- [ ] File reading & summarization
- [ ] System tray icon + auto-start
- [ ] Multiple chat sessions
- [ ] Plugin system for custom commands
- [ ] RAG (retrieval-augmented generation) for documents

---

## 📄 License

MIT © 2026 — Free to use, modify and distribute.

---

<div align="center">

Built with ❤️ using Python, Flask & Ollama

</div>

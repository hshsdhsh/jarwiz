/**
 * JarWiz — Main Application Logic
 * Local AI Assistant powered by Ollama
 */

// ── State ──────────────────────────────────────────────────────────────────
const state = {
  model: '',
  isStreaming: false,
  isRecording: false,
  isSpeaking: false,
  ttsEnabled: true,
  recognition: null,
};

// ── Elements ───────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const messagesEl = $('messages');
const messageInput = $('messageInput');
const sendBtn = $('sendBtn');
const modelSelect = $('modelSelect');
const welcomeScreen = $('welcomeScreen');
const voiceBtn = $('voiceBtn');
const voiceIndicator = $('voiceIndicator');

// ── Init ───────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  checkStatus();
  updateClock();
  setInterval(updateClock, 1000);
  setInterval(checkStatus, 30000);
  setupInput();
  setupVoice();
  setupTTS();
  $('newChatBtn').addEventListener('click', newChat);
  $('clearBtn').addEventListener('click', clearHistory);
  loadScript('markdown.js');
});

function loadScript(src) {
  const script = document.createElement('script');
  script.src = src;
  document.head.appendChild(script);
}

// ── Clock ──────────────────────────────────────────────────────────────────
function updateClock() {
  const now = new Date();
  $('timeDisplay').textContent = now.toLocaleTimeString('ru', {
    hour: '2-digit', minute: '2-digit',
  });
  $('dateDisplay').textContent = now.toLocaleDateString('ru', {
    day: 'numeric', month: 'long', year: 'numeric',
  });
}

// ── Status check ───────────────────────────────────────────────────────────
async function checkStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    const dot = $('statusDot');
    const text = $('statusText');
    const sub = $('statusSub');
    const badge = $('modelBadge');

    if (data.ollama) {
      dot.className = 'status-dot online';
      text.textContent = 'Ollama онлайн';
      sub.textContent = `${data.models.length} модел${data.models.length !== 1 ? 'и' : 'ь'}`;
      badge.textContent = state.model || data.models[0] || 'Ollama';
      populateModels(data.models);
    } else {
      dot.className = 'status-dot offline';
      text.textContent = 'Ollama оффлайн';
      sub.textContent = 'Запусти Ollama';
    }
  } catch {
    $('statusDot').className = 'status-dot offline';
    $('statusText').textContent = 'Сервер недоступен';
  }
}

function populateModels(models) {
  if (models.length === 0) {
    modelSelect.innerHTML = '<option value="">Нет моделей</option>';
    return;
  }
  const current = modelSelect.value;
  modelSelect.innerHTML = models.map(m =>
    `<option value="${m}">${m}</option>`
  ).join('');
  if (current && models.includes(current)) {
    modelSelect.value = current;
  }
  state.model = modelSelect.value;
  modelSelect.addEventListener('change', () => {
    state.model = modelSelect.value;
    $('modelBadge').textContent = state.model;
    showToast(`Модель: ${state.model}`);
  });
}

// ── TTS (Text-to-Speech) ───────────────────────────────────────────────────
function setupTTS() {
  if (!window.speechSynthesis) return;

  // Добавляем кнопку TTS в header
  const headerRight = document.querySelector('.header-right');
  if (!headerRight) return;

  const ttsBtn = document.createElement('button');
  ttsBtn.id = 'ttsToggle';
  ttsBtn.className = 'tts-toggle active';
  ttsBtn.title = 'Голос JarWiz (вкл/выкл)';
  ttsBtn.innerHTML = `
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
      <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>
      <path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>
    </svg>
  `;
  ttsBtn.addEventListener('click', () => {
    state.ttsEnabled = !state.ttsEnabled;
    ttsBtn.classList.toggle('active', state.ttsEnabled);
    ttsBtn.title = state.ttsEnabled ? 'Голос вкл' : 'Голос выкл';
    if (!state.ttsEnabled) window.speechSynthesis.cancel();
    showToast(state.ttsEnabled ? '🔊 Голос включён' : '🔇 Голос выключен');
  });

  headerRight.prepend(ttsBtn);
}

function speakText(text) {
  if (!state.ttsEnabled || !window.speechSynthesis) return;

  // Чистим текст от markdown
  const clean = text
    .replace(/```[\s\S]*?```/g, 'код')
    .replace(/`[^`]+`/g, '')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/#{1,6}\s/g, '')
    .replace(/<[^>]+>/g, '')
    .replace(/ACTION:\w+:\S+/g, '')
    .replace(/https?:\/\/\S+/g, '')
    .trim();

  if (!clean) return;

  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(clean);
  utterance.lang = 'ru-RU';
  utterance.rate = 1.05;
  utterance.pitch = 1.0;
  utterance.volume = 1.0;

  // Выбираем лучший голос
  const voices = window.speechSynthesis.getVoices();
  const ruVoice = voices.find(v =>
    v.lang.startsWith('ru') || v.name.toLowerCase().includes('russian')
  );
  if (ruVoice) utterance.voice = ruVoice;

  utterance.onstart = () => { state.isSpeaking = true; };
  utterance.onend = () => { state.isSpeaking = false; };

  window.speechSynthesis.speak(utterance);
}

// Голоса загружаются асинхронно — ждём
if (window.speechSynthesis) {
  window.speechSynthesis.onvoiceschanged = () => {};
}

// ── Input setup ────────────────────────────────────────────────────────────
function setupInput() {
  messageInput.addEventListener('input', () => {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
    sendBtn.disabled = !messageInput.value.trim() || state.isStreaming;
  });

  messageInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!sendBtn.disabled) sendMessage();
    }
  });

  sendBtn.addEventListener('click', sendMessage);
}

// ── Messaging ──────────────────────────────────────────────────────────────
async function sendMessage() {
  const text = messageInput.value.trim();
  if (!text || state.isStreaming) return;

  // Останавливаем TTS если говорит
  if (window.speechSynthesis) window.speechSynthesis.cancel();

  if (welcomeScreen) welcomeScreen.style.display = 'none';

  appendMessage('user', text);
  messageInput.value = '';
  messageInput.style.height = 'auto';
  sendBtn.disabled = true;
  state.isStreaming = true;

  const aiMsgEl = appendMessage('assistant', '', true);
  let fullResponse = '';

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: text,
        model: state.model || modelSelect.value,
        session_id: 'main',
      }),
    });

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    const bubbleEl = aiMsgEl.querySelector('.msg-bubble');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        try {
          const data = JSON.parse(line.slice(6));
          if (data.chunk) {
            fullResponse += data.chunk;
            bubbleEl.innerHTML = typeof renderMarkdown === 'function'
              ? renderMarkdown(fullResponse)
              : escapeText(fullResponse);
            scrollToBottom();
          }
          if (data.action_result) {
            appendActionNotif(aiMsgEl, data.action_result);
          }
          if (data.done) {
            removeTypingIndicator(aiMsgEl);
            // Произносим ответ после завершения
            speakText(fullResponse);
          }
        } catch {}
      }
    }
  } catch (err) {
    const bubbleEl = aiMsgEl.querySelector('.msg-bubble');
    bubbleEl.innerHTML = `<span style="color:#ef4444">⚠️ Ошибка: ${err.message}</span>`;
    removeTypingIndicator(aiMsgEl);
  } finally {
    state.isStreaming = false;
    sendBtn.disabled = !messageInput.value.trim();
    scrollToBottom();
  }
}

function sendSuggestion(text) {
  messageInput.value = text;
  sendMessage();
}

function appendMessage(role, content, withTyping = false) {
  const div = document.createElement('div');
  div.className = `message ${role}`;

  const avatarContent = role === 'user'
    ? '<span>Я</span>'
    : '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="8" r="4"/><path d="M4 20a8 8 0 0116 0"/></svg>';

  const time = new Date().toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' });

  const bubbleContent = withTyping
    ? '<div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>'
    : (typeof renderMarkdown === 'function' && role === 'assistant'
        ? renderMarkdown(content)
        : escapeText(content));

  div.innerHTML = `
    <div class="msg-avatar">${avatarContent}</div>
    <div class="msg-body">
      <div class="msg-bubble">${bubbleContent}</div>
      <span class="msg-time">${time}</span>
    </div>
  `;

  messagesEl.appendChild(div);
  scrollToBottom();
  return div;
}

function removeTypingIndicator(msgEl) {
  const typing = msgEl.querySelector('.typing-indicator');
  if (typing) typing.remove();
}

function appendActionNotif(msgEl, result) {
  const body = msgEl.querySelector('.msg-body');
  const notif = document.createElement('div');
  notif.className = 'action-notif';
  notif.innerHTML = `
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <polyline points="20 6 9 17 4 12"/>
    </svg>
    ${escapeText(result)}
  `;
  body.appendChild(notif);
}

function escapeText(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br/>');
}

function scrollToBottom() {
  const wrap = $('messagesWrap');
  wrap.scrollTop = wrap.scrollHeight;
}

// ── New chat / Clear ───────────────────────────────────────────────────────
function newChat() {
  if (window.speechSynthesis) window.speechSynthesis.cancel();
  fetch('/api/clear', { method: 'POST' });
  messagesEl.innerHTML = '';
  const welcome = document.createElement('div');
  welcome.id = 'welcomeScreen';
  welcome.className = 'welcome';
  welcome.innerHTML = `
    <div class="welcome-icon">
      <svg viewBox="0 0 80 80" fill="none" width="80" height="80">
        <circle cx="40" cy="40" r="36" stroke="url(#wg2)" stroke-width="2" stroke-dasharray="4 2"/>
        <path d="M24 40 L40 24 L56 40 L40 56 Z" fill="url(#wg2)" opacity="0.6"/>
        <circle cx="40" cy="40" r="8" fill="white" opacity="0.9"/>
        <defs>
          <linearGradient id="wg2" x1="0" y1="0" x2="80" y2="80">
            <stop offset="0%" stop-color="#6366f1"/>
            <stop offset="100%" stop-color="#a855f7"/>
          </linearGradient>
        </defs>
      </svg>
    </div>
    <h2 class="welcome-title">Новый чат</h2>
    <p class="welcome-sub">Чем могу помочь?</p>
    <div class="welcome-chips">
      <button class="chip" onclick="sendSuggestion('Напиши простой Python скрипт для сортировки списка')">🐍 Python код</button>
      <button class="chip" onclick="sendSuggestion('Объясни как работает нейросеть простыми словами')">🧠 Как работает AI?</button>
      <button class="chip" onclick="sendSuggestion('Открой Chrome')">🌐 Открой Chrome</button>
      <button class="chip" onclick="sendSuggestion('Придумай идею для стартапа')">💡 Идея стартапа</button>
    </div>
  `;
  messagesEl.appendChild(welcome);
  showToast('Новый чат начат');
}

async function clearHistory() {
  await fetch('/api/clear', { method: 'POST' });
  newChat();
}

// ── Quick PC actions ───────────────────────────────────────────────────────
async function quickAction(action, target) {
  try {
    const res = await fetch('/api/action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, target }),
    });
    const data = await res.json();
    showToast(data.result || 'Выполнено');
  } catch {
    showToast('Ошибка выполнения');
  }
}

// ── Voice input (STT) ──────────────────────────────────────────────────────
function setupVoice() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    voiceBtn.style.opacity = '0.3';
    voiceBtn.title = 'Голосовой ввод не поддерживается в этом браузере';
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = 'ru-RU';
  recognition.continuous = false;
  recognition.interimResults = true;
  state.recognition = recognition;

  recognition.onstart = () => {
    state.isRecording = true;
    voiceBtn.classList.add('recording');
    voiceIndicator.classList.add('active');
    // Останавливаем TTS пока говорит пользователь
    if (window.speechSynthesis) window.speechSynthesis.cancel();
  };

  recognition.onresult = (e) => {
    const transcript = Array.from(e.results)
      .map(r => r[0].transcript).join('');
    messageInput.value = transcript;
    messageInput.dispatchEvent(new Event('input'));
  };

  recognition.onend = () => {
    state.isRecording = false;
    voiceBtn.classList.remove('recording');
    voiceIndicator.classList.remove('active');
    if (messageInput.value.trim()) {
      sendMessage();
    }
  };

  recognition.onerror = (e) => {
    state.isRecording = false;
    voiceBtn.classList.remove('recording');
    voiceIndicator.classList.remove('active');
    if (e.error !== 'aborted') {
      showToast('Ошибка голосового ввода: ' + e.error);
    }
  };

  voiceBtn.addEventListener('click', () => {
    if (state.isRecording) {
      recognition.stop();
    } else {
      try {
        recognition.start();
        showToast('🎤 Говори...');
      } catch {
        showToast('Голосовой ввод уже активен');
      }
    }
  });
}

// ── Toast ──────────────────────────────────────────────────────────────────
let toastTimer;
function showToast(message) {
  const toast = $('toast');
  toast.textContent = message;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 3000);
}

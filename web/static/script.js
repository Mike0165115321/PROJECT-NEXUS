// web/static/script.js
// (V7.5 - Final Audited & Corrected Version)

import { createAudioManager } from './audioManager.js';
import { createThoughtProcessManager } from './thoughtProcessManager.js';

document.addEventListener('DOMContentLoaded', () => {
    const state = {
        isThinking: false,
    };

    const audioManager = createAudioManager();
    const thoughtProcessManager = createThoughtProcessManager();

    const elements = {
        chatLog: document.getElementById('chat-log'),
        chatForm: document.getElementById('chat-form'),
        userInput: document.getElementById('user-input'),
        submitBtn: document.getElementById('submit-btn'),
        micBtn: document.getElementById('mic-btn'),
        promptsPanel: document.getElementById('suggested-prompts-panel'),
    };

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition;
    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.lang = 'th-TH';
        recognition.interimResults = false;
        recognition.onresult = (event) => {
            elements.userInput.value = event.results[0][0].transcript;
            App.handleUserSubmit();
        };
        recognition.onerror = (event) => { 
            console.error("Speech Recognition Error:", event.error); 
            elements.micBtn?.classList.remove('is-listening');
        };
        recognition.onend = () => { 
            elements.micBtn?.classList.remove('is-listening'); 
        };
    } else {
        if (elements.micBtn) elements.micBtn.style.display = 'none';
    }

    const ChatLog = {
        thinkingIndicator: null,
        thinkingTimer: null,
        thinkingStartTime: null,

        addMessage(messageData, sender) {
            const messageContainer = document.createElement('div');
            messageContainer.className = `message ${sender === 'user' ? 'user-message' : 'feng-message'}`;

            if (messageData.text) {
                const messageText = document.createElement('div');
                messageText.innerHTML = sender === 'feng' && window.marked 
                    ? window.marked.parse(messageData.text) 
                    : messageData.text.replace(/</g, "&lt;").replace(/>/g, "&gt;");
                messageContainer.appendChild(messageText);
            }

            if (sender === 'feng' && messageData.image) {
                const imageWrapper = document.createElement('div');
                imageWrapper.className = 'image-wrapper';
                imageWrapper.innerHTML = `
                    <img src="${messageData.image.url}" alt="${messageData.image.description}" class="feng-image">
                    <p class="photographer-credit">
                        Photo by <a href="${messageData.image.profile_url}" target="_blank">${messageData.image.photographer}</a> on <a href="https://unsplash.com" target="_blank">Unsplash</a>
                    </p>`;
                messageContainer.appendChild(imageWrapper);
            }
            
            elements.chatLog.appendChild(messageContainer);
            this.scrollToBottom();
        },

        showThinkingIndicator() {
            const indicatorContainer = document.createElement('div');
            indicatorContainer.className = 'message feng-message thinking-indicator';
            indicatorContainer.innerHTML = `<div class="dot-flashing"></div><span class="timer">0.00s</span>`;
            elements.chatLog.appendChild(indicatorContainer);
            this.thinkingIndicator = indicatorContainer;
            this.scrollToBottom();
            this.thinkingStartTime = Date.now();
            this.thinkingTimer = setInterval(() => {
                if (!this.thinkingIndicator) { clearInterval(this.thinkingTimer); return; }
                const elapsed = ((Date.now() - this.thinkingStartTime) / 1000).toFixed(2);
                const timerSpan = this.thinkingIndicator.querySelector('.timer');
                if (timerSpan) timerSpan.textContent = `${elapsed}s`;
            }, 100);
        },

        replaceThinkingIndicator(messageData) {
            clearInterval(this.thinkingTimer);
            this.thinkingTimer = null;
            if (!this.thinkingIndicator) { this.addMessage(messageData, 'feng'); return; }
            const finalTime = ((Date.now() - this.thinkingStartTime) / 1000).toFixed(2);
            const messageContainer = document.createElement('div');
            messageContainer.className = 'message feng-message';

            if (messageData.text) {
                const messageText = document.createElement('div');
                messageText.innerHTML = window.marked ? window.marked.parse(messageData.text) : messageData.text;
                messageContainer.appendChild(messageText);
            }
            
            if (messageData.image) {
                const imageWrapper = document.createElement('div');
                imageWrapper.className = 'image-wrapper';
                imageWrapper.innerHTML = `
                    <img src="${messageData.image.url}" alt="${messageData.image.description}" class="feng-image">
                    <p class="photographer-credit">
                        Photo by <a href="${messageData.image.profile_url}" target="_blank">${messageData.image.photographer}</a> on <a href="https://unsplash.com" target="_blank">Unsplash</a>
                    </p>`;
                messageContainer.appendChild(imageWrapper);
            }

            const timeElement = document.createElement('div');
            timeElement.className = 'message-time';
            timeElement.textContent = `(ประมวลผลใน ${finalTime} วินาที)`;
            messageContainer.appendChild(timeElement);

            this.thinkingIndicator.replaceWith(messageContainer);
            this.thinkingIndicator = null;
            this.scrollToBottom();
        },

        scrollToBottom() {
            elements.chatLog.scrollTop = elements.chatLog.scrollHeight;
        }
    };

    const App = {
        socket: null,
        init() {
            this.connectWebSocket();
            this.setupEventListeners();
            ChatLog.addMessage({ text: "สวัสดีค่ะ ฉันฟางซิน มีอะไรให้ช่วยไหมคะ" }, 'feng');
            elements.userInput?.focus();
        },
        connectWebSocket() {
            const userId = "default_user";
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/${userId}`;
            this.socket = new WebSocket(wsUrl);
            this.socket.onopen = () => { console.log("✅ WebSocket connection established."); this.setThinkingState(false); };
            this.socket.onmessage = (event) => {
                const response = JSON.parse(event.data);
                if (response.type === 'progress') {
                    thoughtProcessManager.addStep(response.payload);
                } else if (response.type === 'final_response') {
                    const data = response.payload;
                    const messageData = { text: data.answer || 'ขออภัยค่ะ มีการตอบกลับที่ผิดพลาด', image: data.image || null };
                    ChatLog.replaceThinkingIndicator(messageData);
                    if (data.voice_task_id) audioManager.startPolling(data.voice_task_id);
                    this.setThinkingState(false);
                } else if (response.type === 'error') {
                    ChatLog.replaceThinkingIndicator({ text: `ขออภัยค่ะ: ${response.payload.detail}` });
                    this.setThinkingState(false);
                }
            };
            this.socket.onclose = () => { console.warn("WebSocket closed. Reconnecting..."); this.setThinkingState(true, 'กำลังเชื่อมต่อใหม่...'); setTimeout(() => this.connectWebSocket(), 3000); };
            this.socket.onerror = (error) => { console.error("WebSocket Error:", error); this.socket.close(); };
        },
        setupEventListeners() {
            elements.chatForm?.addEventListener('submit', (e) => { e.preventDefault(); this.handleUserSubmit(); });
            elements.userInput?.addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); this.handleUserSubmit(); } });
            if (elements.micBtn && recognition) {
                elements.micBtn.addEventListener('click', () => {
                    if (state.isThinking) return;
                    elements.micBtn.classList.contains('is-listening') ? recognition.stop() : recognition.start();
                    elements.micBtn.classList.toggle('is-listening');
                });
            }
        },
        handleUserSubmit() {
            if (state.isThinking) return;
            const userText = elements.userInput.value.trim();
            if (!userText) return;
            if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                ChatLog.addMessage({ text: userText }, 'user');
                elements.userInput.value = '';
                this.setThinkingState(true);
                thoughtProcessManager.clear(); 
                ChatLog.showThinkingIndicator();
                if (elements.promptsPanel && typeof elements.promptsPanel.hidePrompts === 'function') {
                    elements.promptsPanel.hidePrompts();
                }
                this.socket.send(userText);
            } else {
                ChatLog.addMessage({ text: "ขออภัยค่ะ การเชื่อมต่อกับเซิร์ฟเวอร์ขัดข้อง" }, 'feng');
            }
        },
        setThinkingState(isThinking) {
            state.isThinking = isThinking;
            elements.userInput.disabled = isThinking;
            if (elements.submitBtn) elements.submitBtn.disabled = isThinking;
            if (elements.micBtn) elements.micBtn.disabled = isThinking;
            elements.userInput.placeholder = isThinking ? 'กำลังครุ่นคิด...' : 'เริ่มต้นการสนทนา...';
            if (!isThinking) elements.userInput.focus();
        },
    };

    App.init();
    
    if (audioManager.setupEventListeners) {
        audioManager.setupEventListeners();
    }
    if (thoughtProcessManager.setupEventListeners) {
        thoughtProcessManager.setupEventListeners();
    }
});
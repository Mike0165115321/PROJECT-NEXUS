// web/static/script.js
// (V7.0 - Fully Modular Architecture)

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

    const api = {
        async getFengResponse(query) {
            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query }),
                });
                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
                }
                return await response.json();
            } catch (error) {
                console.error('API Error:', error);
                throw error;
            }
        }
    };

    const ChatLog = {
        addMessage(messageData, sender) {
            const messageContainer = document.createElement('div');
            messageContainer.className = `message ${sender}-message`;

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
        scrollToBottom() {
            elements.chatLog.scrollTop = elements.chatLog.scrollHeight;
        }
    };

    const App = {
        init() {
            this.setupEventListeners();
            ChatLog.addMessage({ text: "สวัสดีค่ะ ฉันฟางซิน มีอะไรให้ช่วยไหมคะ" }, 'feng');
            elements.userInput?.focus();
        },

        setupEventListeners() {
            elements.chatForm?.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleUserSubmit();
            });

            elements.userInput?.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.handleUserSubmit();
                }
            });

            if (elements.micBtn && recognition) {
                elements.micBtn.addEventListener('click', () => {
                    if (state.isThinking) return;
                    if (elements.micBtn.classList.contains('is-listening')) {
                        recognition.stop();
                    } else {
                        recognition.start();
                        elements.micBtn.classList.add('is-listening');
                    }
                });
            }
        },

        async handleUserSubmit() {
            if (state.isThinking) return;
            const userText = elements.userInput.value.trim();
            if (!userText) return;

            ChatLog.addMessage({ text: userText }, 'user');
            elements.userInput.value = '';
            this.setThinkingState(true);
            thoughtProcessManager.clear();
            
            elements.promptsPanel?.hidePrompts?.();

            try {
                const data = await api.getFengResponse(userText);
                
                if (data.thought_process) {
                    await thoughtProcessManager.display(data.thought_process);
                } else {
                    thoughtProcessManager.clear("ไม่มีข้อมูลเบื้องหลังสำหรับคำตอบนี้");
                }

                const messageData = {
                    text: data.answer || 'ขออภัยครับ มีการตอบกลับที่ผิดพลาด',
                    image: data.image || null,
                };
                
                ChatLog.addMessage(messageData, 'feng');
                
                if (data.voice_task_id) {
                    audioManager.startPolling(data.voice_task_id);
                }

            } catch (error) {
                ChatLog.addMessage({ text: "ขออภัยครับ เกิดข้อผิดพลาดร้ายแรง โปรดตรวจสอบ Console" }, 'feng');
            } finally {
                this.setThinkingState(false);
            }
        },

        setThinkingState(isThinking) {
            state.isThinking = isThinking;
            elements.userInput.disabled = isThinking;
            elements.submitBtn.disabled = isThinking;
            elements.micBtn.disabled = isThinking;
            elements.userInput.placeholder = isThinking ? 'กำลังครุ่นคิด...' : 'เริ่มต้นการสนทนา...';
            if (!isThinking) elements.userInput.focus();
        },
    };

    App.init();
});
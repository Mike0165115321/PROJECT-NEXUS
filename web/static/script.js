// web/static/script.js
// (V4.3 - Microphone Repaired and Enhanced)

document.addEventListener('DOMContentLoaded', () => {
    // --- Application State ---
    const state = {
        isThinking: false,
        isSoundEnabled: true,
        isTpVisible: true,
        audio: new Audio(),
    };

    // --- DOM Elements ---
    const elements = {
        chatLog: document.getElementById('chat-log'),
        chatForm: document.getElementById('chat-form'),
        userInput: document.getElementById('user-input'),
        submitBtn: document.getElementById('submit-btn'),
        micBtn: document.getElementById('mic-btn'),
        mainContainer: document.getElementById('main-container'),
        tpToggleBtn: document.getElementById('tp-toggle-btn'),
        tpContent: document.getElementById('tp-content'),
        toggleSoundBtn: document.getElementById('toggle-sound-btn'),
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
    const ThoughtProcess = {
        clear(message = 'กำลังประมวลผลความคิด...') {
            if (!elements.tpContent) return;
            elements.tpContent.innerHTML = `<div class="tp-placeholder"><p>${message}</p></div>`;
        },
        async display(tp) {
            if (!elements.tpContent) return;
            elements.tpContent.innerHTML = '';

            if (tp.error) {
                this.appendSection('เกิดข้อผิดพลาดใน Backend', `<p>Agent พบปัญหา:</p><code>${tp.error}</code>`, 'error');
                return;
            }

            if (tp.search_logs?.length > 0) {
                const list = await this.createAnimatedList(tp.search_logs);
                this.appendSection('เบื้องหลังการค้นหา:', list);
            }
        },
        appendSection(title, content, type = '') {
            const section = document.createElement('div');
            section.className = `tp-section ${type}`;
            section.innerHTML = `<h4>${title}</h4>`;
            if (typeof content === 'string') {
                section.innerHTML += content;
            } else {
                section.appendChild(content);
            }
            elements.tpContent.appendChild(section);
            elements.tpContent.scrollTop = elements.tpContent.scrollHeight;
        },
        async createAnimatedList(items) {
            const ul = document.createElement('ul');
            ul.className = 'search-logs-list';
            for (const item of items) {
                await new Promise(resolve => setTimeout(resolve, 150));
                const li = document.createElement('li');
                li.textContent = item;
                ul.appendChild(li);
                elements.tpContent.scrollTop = elements.tpContent.scrollHeight;
            }
            return ul;
        }
    };

    const App = {
        init() {
            this.setupEventListeners();
            this.updateLayout();
            ThoughtProcess.clear("ถามคำถามในช่องแชทเพื่อดูการเชื่อมโยงข้อมูลของฉันที่นี่");
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

            elements.toggleSoundBtn?.addEventListener('click', () => {
                state.isSoundEnabled = !state.isSoundEnabled;
                elements.toggleSoundBtn.textContent = state.isSoundEnabled ? '🔊' : '🔇';
                if (!state.isSoundEnabled) state.audio.pause();
            });
            
            elements.tpToggleBtn?.addEventListener('click', () => {
                state.isTpVisible = !state.isTpVisible;
                this.updateLayout();
            });

            // --- ⭐️ การซ่อมแซมไมโครโฟน: ส่วนที่ 2 - ปรับปรุง Event Listener ⭐️ ---
            if (elements.micBtn && recognition) {
                elements.micBtn.addEventListener('click', () => {
                    // ไม่ให้กดไมค์ได้ ถ้า AI กำลังคิดอยู่
                    if (state.isThinking) return;
                    
                    // ถ้ากำลังฟังอยู่ ให้สั่งหยุด
                    if (elements.micBtn.classList.contains('is-listening')) {
                        recognition.stop();
                    // ถ้าไม่ได้ฟังอยู่ ให้สั่งเริ่มฟัง
                    } else {
                        recognition.start();
                        // เพิ่มสัญลักษณ์ทันทีที่เริ่มฟัง
                        elements.micBtn.classList.add('is-listening');
                    }
                });
            }
        },

        async handleUserSubmit() {
            // ... (ส่วนนี้เหมือนเดิม) ...
            if (state.isThinking) return;
            const userText = elements.userInput.value.trim();
            if (!userText) return;

            ChatLog.addMessage({ text: userText }, 'user');
            elements.userInput.value = '';
            this.setThinkingState(true);
            ThoughtProcess.clear();
            
            elements.promptsPanel?.hidePrompts?.();

            try {
                const data = await api.getFengResponse(userText);
                
                if (data.thought_process) {
                    await ThoughtProcess.display(data.thought_process);
                } else {
                    ThoughtProcess.clear("ไม่มีข้อมูลเบื้องหลังสำหรับคำตอบนี้");
                }

                const messageData = {
                    text: data.answer || 'ขออภัยครับ มีการตอบกลับที่ผิดพลาด',
                    image: data.image || null,
                    voice_url: data.voice_url || null
                };
                
                ChatLog.addMessage(messageData, 'feng');
                this.playFengsVoice(messageData.voice_url, messageData.text);

            } catch (error) {
                ChatLog.addMessage({ text: "ขออภัยครับ เกิดข้อผิดพลาดร้ายแรง โปรดตรวจสอบ Console" }, 'feng');
            } finally {
                this.setThinkingState(false);
            }
        },

        playFengsVoice(voiceUrl, fallbackText) {
            // ... (ส่วนนี้เหมือนเดิม) ...
            if (!state.isSoundEnabled) return;
            
            if (voiceUrl) {
                state.audio.src = voiceUrl;
                state.audio.playbackRate = 1.15;
                state.audio.play().catch(e => console.error("Audio playback error:", e));
            } 
            else if (fallbackText && 'speechSynthesis' in window) {
                const cleanText = fallbackText.replace(/[*#`\[\]]|(\(http.*?\))/g, '');
                const utterance = new SpeechSynthesisUtterance(cleanText);
                utterance.lang = 'th-TH';
                utterance.rate = 1.2;
                window.speechSynthesis.cancel();
                window.speechSynthesis.speak(utterance);
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

        updateLayout() {
            elements.mainContainer?.classList.toggle('tp-visible', state.isTpVisible);
            elements.mainContainer?.classList.toggle('tp-hidden', !state.isTpVisible);
            elements.tpToggleBtn?.classList.toggle('is-active', state.isTpVisible);
            elements.tpToggleBtn.textContent = state.isTpVisible ? 'ซ่อน' : 'แสดง';
        }
    };

    App.init();
});
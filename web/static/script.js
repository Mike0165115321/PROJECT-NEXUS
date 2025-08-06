// web/static/script.js
// (V3 - With Live Search Log Display)

document.addEventListener('DOMContentLoaded', () => {
    // --- 1. การดึง Element ---
    const chatLog = document.getElementById('chat-log');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const submitBtn = document.getElementById('submit-btn');
    const fengSymbol = document.getElementById('feng-symbol');
    const toggleSoundBtn = document.getElementById('toggle-sound-btn');
    const micBtn = document.getElementById('mic-btn');
    const mainContainer = document.getElementById('main-container');
    const tpToggleBtn = document.getElementById('tp-toggle-btn');
    const tpContent = document.getElementById('tp-content');

    // --- 2. State Management ---
    let isFengThinking = false;
    let isSoundEnabled = true;
    let isTpVisible = true;

    // --- 3. การตั้งค่า Speech Recognition ---
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition;
    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.lang = 'th-TH';
        recognition.interimResults = false;
        recognition.onresult = (event) => {
            userInput.value = event.results[0][0].transcript;
            handleUserSubmit(); 
        };
        recognition.onerror = (event) => { console.error("Speech Recognition Error:", event.error); };
        recognition.onend = () => { if(micBtn) micBtn.classList.remove('is-listening'); };
    } else {
        if (micBtn) micBtn.style.display = 'none';
    }

    // --- 4. Event Listeners & Initializers ---
    const setupEventListeners = () => {
        if (tpToggleBtn) {
            tpToggleBtn.addEventListener('click', () => {
                isTpVisible = !isTpVisible;
                updateLayout();
            });
        }
        if (toggleSoundBtn) {
            toggleSoundBtn.addEventListener('click', () => {
                isSoundEnabled = !isSoundEnabled; 
                toggleSoundBtn.textContent = isSoundEnabled ? '🔊' : '🔇';
                if (!isSoundEnabled) window.speechSynthesis.cancel();
            });
        }
        if (chatForm) {
            chatForm.addEventListener('submit', (e) => { e.preventDefault(); handleUserSubmit(); });
        }
        if (userInput) {
            userInput.addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleUserSubmit(); } });
        }
        if (micBtn && recognition) {
            micBtn.addEventListener('click', () => {
                if (isFengThinking) return;
                micBtn.classList.contains('is-listening') ? recognition.stop() : recognition.start();
                micBtn.classList.toggle('is-listening');
            });
        }
    };

    // --- 5. Core Functions ---
    const handleUserSubmit = async () => {
        if (isFengThinking) return;
        const userText = userInput.value.trim();
        if (!userText) return;

        addMessageToLog(userText, 'user');
        userInput.value = '';
        setThinkingState(true);
        clearThoughtProcess();
        
        try {
            const data = await getFengResponseFromAPI(userText);

            // รอให้การแสดงผล "เบื้องหลังการทำงาน" เสร็จสิ้นก่อน
            const thoughtProcessData = data.thought_process;
            if (thoughtProcessData) {
                await displayThoughtProcess(thoughtProcessData, userText);
            } else {
                clearThoughtProcess("ไม่มีข้อมูลเบื้องหลังสำหรับคำตอบนี้");
            }

            // จากนั้นจึงแสดงคำตอบสุดท้ายในช่องแชท
            if (data && data.answer) {
                addMessageToLog(data.answer, 'feng'); 
                playFengsVoice(data.answer);
            } else {
                 addMessageToLog(data?.answer || 'ขออภัยครับ มีการตอบกลับที่ผิดพลาด', 'feng');
            }

        } catch (error) {
            console.error("Critical error in handleUserSubmit:", error);
            addMessageToLog("ขออภัยครับ เกิดข้อผิดพลาดร้ายแรง โปรดตรวจสอบ Console", 'feng');
        } finally {
            setThinkingState(false);
        }
    };
    
    const addMessageToLog = (text, sender) => {
        const messageContainer = document.createElement('div');
        messageContainer.classList.add('message', `${sender}-message`);
        const messageText = document.createElement('p');

        if (sender === 'feng' && window.marked) {
            messageText.innerHTML = window.marked.parse(text);
        } else {
            messageText.textContent = text;
        }

        messageContainer.appendChild(messageText);
        chatLog.appendChild(messageContainer);
        chatLog.scrollTop = chatLog.scrollHeight;
    };

    const getFengResponseFromAPI = async (userQuery) => {
        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: userQuery })
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
    };
    
    const playFengsVoice = (textToSpeak) => {
        if (!isSoundEnabled || !textToSpeak) return;
        const cleanText = textToSpeak
            .replace(/\*\*(.*?)\*\*/g, '$1').replace(/\*(.*?)\*/g, '$1')
            .replace(/\[(.*?)\]\(.*?\)/g, '$1').replace(/#{1,6}\s/g, '').replace(/`/g, '');
        try {
            const synth = window.speechSynthesis;
            synth.cancel();
            const utterance = new SpeechSynthesisUtterance(cleanText);
            utterance.lang = 'th-TH';
            utterance.rate = 1.05;
            synth.speak(utterance);
        } catch(error) {
            console.error("Text-to-Speech (TTS) Error:", error);
        }
    };

    const setThinkingState = (isThinking) => {
        isFengThinking = isThinking;
        if(userInput) userInput.disabled = isThinking;
        if(submitBtn) submitBtn.disabled = isThinking;
        if(userInput) userInput.placeholder = isThinking ? 'กำลังครุ่นคิด...' : 'เริ่มต้นการสนทนา...';
        if (!isThinking && userInput) userInput.focus();
    };

    // --- 6. Thought Process Panel Functions ---
    const updateLayout = () => {
        if (!mainContainer || !tpToggleBtn) return;
        mainContainer.classList.toggle('tp-visible', isTpVisible);
        mainContainer.classList.toggle('tp-hidden', !isTpVisible);
        tpToggleBtn.classList.toggle('is-active', isTpVisible);
        tpToggleBtn.textContent = isTpVisible ? 'ซ่อน' : 'แสดง';
    };

    const clearThoughtProcess = (message = 'กำลังประมวลผลความคิด...') => {
        if (!tpContent) return;
        tpContent.innerHTML = `<div class="tp-placeholder"><p>${message}</p></div>`;
    };

    // ⭐️⭐️⭐️ ฟังก์ชันที่อัปเกรดทั้งหมดอยู่ที่นี่ ⭐️⭐️⭐️
    const displayThoughtProcess = async (tp, userQuery) => {
        if (!tpContent) return;
        tpContent.innerHTML = ''; // ล้างข้อมูลเก่า

        // --- Section 1: แสดงข้อผิดพลาด (ถ้ามี) ---
        if (tp.error) {
            const errorSection = document.createElement('div');
            errorSection.className = 'tp-section';
            errorSection.innerHTML = `<h4 style="color: #FF453A;">เกิดข้อผิดพลาดใน Backend</h4><p>Agent พบปัญหา:</p><code style="color: #FFB3AE;"></code>`;
            errorSection.querySelector('code').textContent = tp.error;
            tpContent.appendChild(errorSection);
            return;
        }

        // --- Section 2: แสดง Search Logs แบบจำลองเรียลไทม์ ---
        if (tp.search_logs && tp.search_logs.length > 0) {
            const logsSection = document.createElement('div');
            logsSection.className = 'tp-section';
            logsSection.innerHTML = `<h4>เบื้องหลังการค้นหา:</h4>`;
            const ul = document.createElement('ul');
            ul.className = 'search-logs-list';
            logsSection.appendChild(ul);
            tpContent.appendChild(logsSection);

            // วนลูปแสดงผล log แต่ละบรรทัดพร้อมหน่วงเวลา
            for (const logText of tp.search_logs) {
                await new Promise(resolve => setTimeout(resolve, 250)); // หน่วงเวลา 250ms
                const li = document.createElement('li');
                li.textContent = logText;
                ul.appendChild(li);
                tpContent.scrollTop = tpContent.scrollHeight; // เลื่อน panel ลงมาให้เห็น log ล่าสุด
            }
        }

        // --- Section 3: แสดงแผนของ PlannerAgent (ถ้ามี) ---
        if (tp.plan) {
            const planSection = document.createElement('div');
            planSection.className = 'tp-section';
            planSection.innerHTML = `<h4>ขั้นตอนการทำงาน (Planner)</h4>`;
            
            if (tp.plan.sub_queries && tp.plan.sub_queries.length > 0) {
                const subQueriesDiv = document.createElement('div');
                subQueriesDiv.innerHTML = `<p><strong>คำค้นหาย่อย (${tp.plan.sub_queries.length}):</strong></p>`;
                const ul = document.createElement('ul');
                tp.plan.sub_queries.forEach(q => {
                    const li = document.createElement('li');
                    li.textContent = q;
                    ul.appendChild(li);
                });
                subQueriesDiv.appendChild(ul);
                planSection.appendChild(subQueriesDiv);
            }
            tpContent.appendChild(planSection);
        }

        // --- Section 4: แสดงบริบทที่คัดเลือกแล้ว (ถ้ามี) ---
        if (tp.final_context_chunks && tp.final_context_chunks.length > 0) {
            const ragSection = document.createElement('div');
            ragSection.className = 'tp-section';
            ragSection.innerHTML = `<h4>หลักฐานที่ใช้สังเคราะห์คำตอบ (${tp.final_context_chunks.length} ชิ้น)</h4>`;
            
            tp.final_context_chunks.forEach(chunk => {
                const evidenceDiv = document.createElement('div');
                evidenceDiv.className = 'rag-evidence-item';
                
                // ปรับปรุงให้รองรับทั้ง score และ source จาก book และ memory
                const score = chunk.score ? chunk.score.toFixed(4) : 'N/A';
                const source = chunk.source === 'book' ? 'คลังความรู้ (หนังสือ)' : 'ความทรงจำ';
                const text = chunk.embedding_text || chunk.text || '';

                evidenceDiv.innerHTML = `<div class="score">Score: ${score}</div><div class="text"></div><div class="source"></div>`;
                evidenceDiv.querySelector('.text').textContent = `"${text}"`;
                evidenceDiv.querySelector('.source').textContent = `จาก: ${source}`;
                ragSection.appendChild(evidenceDiv);
            });
            tpContent.appendChild(ragSection);
        }
    };

    // --- 7. Initialization ---
    const initializeApp = () => {
        setupEventListeners();
        updateLayout();
        clearThoughtProcess("ถามคำถามในช่องแชทเพื่อดูการเชื่อมโยงข้อมูลของฉันที่นี่");
        addMessageToLog("สวัสดีครับ ผมเฟิง มีสิ่งใดให้เราได้ร่วมไตร่ตรองกันในวันนี้", 'feng');
        if (userInput) userInput.focus();
    };
    
    initializeApp();
});
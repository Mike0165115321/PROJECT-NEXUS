// (V2.2 - Polished with Animations & Agent-Specific Colors)

export function createThoughtProcessManager() {
    const elements = {
        tpContent: document.getElementById('tp-content'),
        tpToggleBtn: document.getElementById('tp-toggle-btn'),
        mainContainer: document.getElementById('main-container'),
    };

    const state = {
        isTpVisible: true,
    };

    const statusMap = new Map([
        ['RECEIVED', { icon: '📥', text: 'ได้รับคำสั่ง' }],
        ['ROUTING', { icon: '🚦', text: 'วิเคราะห์เจตนา' }],
        ['PROCESSING', { icon: '⚙️', text: 'ประมวลผล' }],
        ['DEEP_ANALYSIS', { icon: '🧠', text: 'วิเคราะห์เชิงลึก' }],
        ['FORMATTING', { icon: '✍️', text: 'เรียบเรียงคำตอบ' }],
    ]);

    const agentMap = new Map([
        ['FENG', { color: 'var(--color-highlight)' }], 
        ['PLANNER', { color: 'var(--color-accent)' }],
        ['GENERAL_HANDLER', { color: '#b294c7' }],
        ['FORMATTER', { color: '#8abda0' }], 
        ['NEWS', { color: '#e07a5f' }], 
        ['CODER', { color: '#6a9fb5' }],
        ['COUNSELOR', { color: '#c88ea5' }] // เพิ่มสีสำหรับ Counselor
    ]);

    function setupEventListeners() {
        elements.tpToggleBtn?.addEventListener('click', () => {
            state.isTpVisible = !state.isTpVisible;
            updateLayout();
        });
    }

    function updateLayout() {
        if (!elements.mainContainer || !elements.tpToggleBtn) return;
        elements.mainContainer.classList.toggle('tp-visible', state.isTpVisible);
        elements.mainContainer.classList.toggle('tp-hidden', !state.isTpVisible);
        elements.tpToggleBtn.classList.toggle('is-active', state.isTpVisible);
        elements.tpToggleBtn.textContent = state.isTpVisible ? 'ซ่อน' : 'แสดง';
    }

    function clear(message = 'ถามคำถามในช่องแชทเพื่อดูการทำงานของฉันที่นี่') {
        if (!elements.tpContent) return;
        elements.tpContent.innerHTML = `<div class="tp-placeholder"><p>${message}</p></div>`;
    }

    function addStep(stepData) {
        if (!elements.tpContent) return;
        const placeholder = elements.tpContent.querySelector('.tp-placeholder');
        if (placeholder) {
            placeholder.remove();
        }

        const stepDiv = document.createElement('div');
        stepDiv.className = 'tp-step';

        const agentInfo = agentMap.get(stepData.agent);
        if (agentInfo) {
            stepDiv.style.setProperty('--step-color', agentInfo.color);
        }

        const statusInfo = statusMap.get(stepData.status) || { icon: '🔹', text: stepData.status };
        
        stepDiv.innerHTML = `
            <div class="tp-step-header">
                <span class="tp-step-icon">${statusInfo.icon}</span>
                <span class="tp-step-title">${statusInfo.text}: ${stepData.agent || ''}</span>
            </div>
            <div class="tp-step-detail">${stepData.detail}</div>
        `;
        elements.tpContent.appendChild(stepDiv);
        elements.tpContent.scrollTop = elements.tpContent.scrollHeight;
    }

    setupEventListeners();
    updateLayout();
    clear(); 

    return {
        clear,
        addStep,
    };
}
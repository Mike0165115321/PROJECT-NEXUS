// web/static/thoughtProcessManager.js
// (V1.0 - Dedicated Thought Process UI Management)

export function createThoughtProcessManager() {
    const elements = {
        tpContent: document.getElementById('tp-content'),
        tpToggleBtn: document.getElementById('tp-toggle-btn'),
        mainContainer: document.getElementById('main-container'),
    };

    const state = {
        isTpVisible: true,
    };

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

    function clear(message = 'กำลังประมวลผลความคิด...') {
        if (!elements.tpContent) return;
        elements.tpContent.innerHTML = `<div class="tp-placeholder"><p>${message}</p></div>`;
    }

    async function display(tp) {
        if (!elements.tpContent) return;
        elements.tpContent.innerHTML = '';

        if (tp.error) {
            appendSection('เกิดข้อผิดพลาดใน Backend', `<p>Agent พบปัญหา:</p><code>${tp.error}</code>`, 'error');
            return;
        }

        if (tp.search_logs?.length > 0) {
            const list = await createAnimatedList(tp.search_logs);
            appendSection('เบื้องหลังการค้นหา:', list);
        }
    }

    function appendSection(title, content, type = '') {
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
    }

    async function createAnimatedList(items) {
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

    setupEventListeners();
    updateLayout();
    clear("ถามคำถามในช่องแชทเพื่อดูการเชื่อมโยงข้อมูลของฉันที่นี่");

    return {
        clear,
        display,
    };
}
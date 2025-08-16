// web/static/suggested_prompts.js
// (V4 - Smart Suggestion Panel)

function initializeSuggestedPrompts() {
    const panel = document.getElementById('suggested-prompts-panel');
    const list = document.getElementById('suggested-prompts-list');
    const refreshBtn = document.getElementById('refresh-prompts-btn');
    const pinBtn = document.getElementById('pin-prompts-btn');
    const toggleBtn = document.getElementById('toggle-prompts-btn');
    const userInput = document.getElementById('user-input');
    const chatForm = document.getElementById('chat-form');

    if (!panel || !list || !refreshBtn || !pinBtn || !toggleBtn || !userInput || !chatForm) {
        console.error("Smart Suggestion Panel cannot initialize: Required elements not found.");
        return;
    }

    let isPinned = false;

    const allShowcasePrompts = [
        // --- ⭐️ หมวด 1: การวิเคราะห์และเปรียบเทียบเชิงลึก (PlannerAgent Showcase) ⭐️ ---
        "วิเคราะห์ข้อดีข้อเสียของปรัชญา Stoicism กับ Epicureanism",
        "เปรียบเทียบแนวคิดเรื่อง 'อำนาจ' จากหนังสือ The 48 Laws of Power และ The Prince",
        "วิเคราะห์ความสัมพันธ์ระหว่าง 'ความสุข' และ 'เงิน' จากมุมมองทางจิตวิทยา",
        "ทำไมคนเราถึงผัดวันประกันพรุ่ง และจะเอาชนะมันได้อย่างไรโดยใช้หลักการจากหนังสือ",
        "เปรียบเทียบหนังสือ 'Atomic Habits' กับ 'The Power of Habit'",

        // --- ⭐️ หมวด 2: การวางแผนและการแก้ปัญหา (Planner & Counselor Showcase) ⭐️ ---
        "ช่วยวางแผนการเรียนรู้เรื่อง Machine Learning สำหรับผู้เริ่มต้นหน่อย",
        "ช่วงนี้รู้สึกหมดไฟในการทำงาน ควรจะเริ่มต้นแก้ไขจากจุดไหนดี",
        "จะสร้างนิสัยการอ่านหนังสือให้ต่อเนื่องได้อย่างไร",
        "ช่วยวางแผนการพัฒนาทักษะการสื่อสารสำหรับปีนี้หน่อย",

        // --- ⭐️ หมวด 3: การให้ข้อมูลและความรู้ (Librarian & ProactiveOffer Showcase) ⭐️ ---
        "The Innovator's Dilemma คืออะไร",
        "แนะนำหนังสือที่ดีที่สุด 3 เล่ม เกี่ยวกับการตัดสินใจ",
        "มีหนังสืออะไรบ้างในหมวดหมู่ 'ธุรกิจและภาวะผู้นำ'",

        // --- ⭐️ หมวด 4: การใช้เครื่องมือ (Utility Showcase) ⭐️ ---
        "สรุปข่าวเทคโนโลยีล่าสุดทั่วโลก",
        "หารูปภาพท้องฟ้าสวยๆ",
        "เขียนโค้ด Python ง่ายๆ สำหรับหาค่าเฉลี่ยของ list"
    ];

    const display = () => {
        const shuffled = [...allShowcasePrompts].sort(() => 0.5 - Math.random());
        const selectedPrompts = shuffled.slice(0, 3);

        let promptsHTML = '';
        selectedPrompts.forEach((prompt, index) => {
            promptsHTML += `<li class="prompt-item" style="--delay: ${index * 100}ms">${prompt}</li>`;
        });
        list.innerHTML = promptsHTML;
    };

    const showPanel = () => {
        panel.classList.remove('is-hidden');
        toggleBtn.classList.add('is-active');
    };

    const hidePanel = () => {
        if (isPinned) return; 
        panel.classList.add('is-hidden');
        toggleBtn.classList.remove('is-active');
    };

    toggleBtn.addEventListener('click', () => {
        panel.classList.toggle('is-hidden');
        toggleBtn.classList.toggle('is-active');
    });

    refreshBtn.addEventListener('click', display);

    pinBtn.addEventListener('click', () => {
        isPinned = !isPinned;
        pinBtn.classList.toggle('is-pinned', isPinned);
    });

    list.addEventListener('click', (event) => {
        if (event.target.classList.contains('prompt-item')) {
            if (userInput.disabled) return; 
            userInput.value = event.target.innerText;
            const submitEvent = new Event('submit', { bubbles: true, cancelable: true });
            chatForm.dispatchEvent(submitEvent);
        }
    });

    panel.displayNewPrompts = display;
    panel.hidePrompts = hidePanel;

    hidePanel();
}

document.addEventListener('DOMContentLoaded', initializeSuggestedPrompts);
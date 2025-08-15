// web/static/suggested_prompts.js
// (V3.1 - With Event Listeners)

function initializeSuggestedPrompts() {
    const promptsContainer = document.getElementById('suggested-prompts-container');
    const promptsList = document.getElementById('suggested-prompts-list');
    const hidePromptsBtn = document.getElementById('hide-prompts-btn');
    const userInput = document.getElementById('user-input');
    const chatLog = document.getElementById('chat-log');
    
    if (!promptsContainer || !promptsList || !hidePromptsBtn || !userInput || !chatLog) {
        console.error("Suggested prompts cannot initialize: Required elements not found.");
        return;
    }

    const allShowcasePrompts = [
        "วิเคราะห์ข้อดีข้อเสียของ Stoicism กับ Epicureanism",
        "ช่วยวางแผนการเรียนรู้เรื่อง Machine Learning สำหรับผู้เริ่มต้นหน่อย",
        "สรุปข่าวเทคโนโลยีล่าสุดทั่วโลก",
        "แนะนำหนังสือเกี่ยวกับประวัติศาสตร์ที่น่าสนใจหน่อย",
        "มีหนังสืออะไรบ้างในคลังความรู้ของคุณ",
        "เขียนโค้ด Python สำหรับหาค่าเฉลี่ยของ list",
        "หารูปภูเขาสวยๆ ตอนพระอาทิตย์ขึ้น",
        "เปิดโปรแกรมเครื่องคิดเลข",
        "The Art of War คืออะไร",
        "วันนี้รู้สึกเครียดมากเลย ทำยังไงดี",
        "คุณคิดว่า AI จะครองโลกในอนาคตไหม"
    ];

    const display = () => {
        if (chatLog.children.length > 1) {
            promptsContainer.classList.add('hidden');
            return;
        }

        promptsContainer.classList.remove('hidden');

        const shuffled = [...allShowcasePrompts].sort(() => 0.5 - Math.random());
        const selectedPrompts = shuffled.slice(0, 3);

        let promptsHTML = '';
        selectedPrompts.forEach((prompt, index) => {
            promptsHTML += `<li class="prompt-item" style="--delay: ${index * 100}ms">${prompt}</li>`;
        });
        promptsList.innerHTML = promptsHTML;
    };

    promptsList.addEventListener('click', (event) => {
        if (event.target.classList.contains('prompt-item')) {
            if (userInput.disabled) return; 
            
            const promptText = event.target.innerText;
            userInput.value = promptText;
            
            const submitEvent = new Event('submit', { bubbles: true, cancelable: true });
            document.getElementById('chat-form').dispatchEvent(submitEvent);
        }
    });

    // 2. จัดการการคลิกที่ปุ่มซ่อน
    hidePromptsBtn.addEventListener('click', () => {
        promptsContainer.classList.add('hidden');
    });

    // --- ⭐️ สิ้นสุดส่วนที่เพิ่ม ⭐️ ---

    // ผูกฟังก์ชันไว้กับ Element เพื่อให้ script.js หลักเรียกใช้ได้
    promptsContainer.displayNewPrompts = () => {
        // หลังจากสนทนาแรก เราจะซ่อนกล่องไปเลย
        promptsContainer.classList.add('hidden');
    };
    promptsContainer.hidePrompts = () => { 
        promptsContainer.classList.add('hidden');
    };

    // แสดงผลครั้งแรก
    display();
}

document.addEventListener('DOMContentLoaded', initializeSuggestedPrompts);
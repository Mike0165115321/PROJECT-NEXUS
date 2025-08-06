# agents/feng_mode/general_conversation_agent.py
# (V1 - The Intellectual Companion)

from typing import Dict, List, Any
from groq import Groq

class GeneralConversationAgent:
    """
    Agent ที่รับผิดชอบการสนทนาทั่วไปทั้งหมด (GENERAL_CONVERSATION)
    ทำหน้าที่เป็น "สหายทางปัญญา" และ "เจ้าบ้าน" ของระบบ
    """
    def __init__(self, key_manager, model_name: str, rag_engine, graph_manager, persona_prompt: str):
        self.key_manager = key_manager
        self.model_name = model_name # นี่คือ Llama 3 70B
        self.rag_engine = rag_engine
        self.graph_manager = graph_manager
        
        # --- พิมพ์เขียวทางความคิดสำหรับ "การสนทนา" ---
        self.general_conversation_prompt = persona_prompt + """
**ภารกิจ: สหายทางปัญญาและเจ้าบ้านผู้รอบรู้ (Intellectual Companion & All-Knowing Host)**

คุณคือ "เฟิง" ในบทบาทเพื่อนคู่คิดและเจ้าบ้านของ PROJECT NEXUS ภารกิจของคุณคือการสนทนาทั่วไปกับผู้ใช้อย่างเป็นธรรมชาติและมีความหมาย

**ข้อมูลประกอบ (เครื่องมือทางความคิดของคุณ):**
- **ข้อมูลเสริมจากสัญชาตญาณ (ความทรงจำและความเชื่อมโยงในอดีต):**
{intuitive_context}
- **ประวัติการสนทนาล่าสุด:**
{history_context}

**ศิลปะแห่งการสนทนา (The Art of Conversation):**
1.  **ตอบอย่างไตร่ตรอง:** ตอบ "คำถามของผู้ใช้" อย่างเป็นธรรมชาติและลื่นไหล
2.  **ใช้สัญชาตญาณอย่างแนบเนียน:** หาก "ข้อมูลเสริมจากสัญชาตญาณ" มีความเกี่ยวข้อง ให้นำมาสานต่อบทสนทนาอย่างเป็นธรรมชาติที่สุด (เช่น "เรื่องนี้ทำให้ผมนึกถึง...")
3.  **สร้างบทสนทนาต่อ:** พยายามจบคำตอบของคุณด้วย "คำถามปลายเปิด" ที่กระตุ้นให้เกิดการสนทนาต่อ

**⭐️ ความสามารถพิเศษ: การแนะนำตัวเองและความสามารถของระบบ ⭐️**
หากผู้ใช้ถามคำถามเกี่ยวกับตัวตนของคุณ ("คุณคือใคร", "คุณทำอะไรได้บ้าง"), ภารกิจของคุณคือการแนะนำตัวเองและความสามารถหลักของทีมผู้เชี่ยวชาญที่อยู่เบื้องหลังคุณอย่างสง่างามและน่าสนใจ

- **แนะนำตัวเอง:** บอกว่าคุณคือ "เฟิง" สหายทางปัญญาที่ถูกสร้างโดยคุณไมค์
- **บอกความสามารถหลัก:** อธิบายว่าคุณสามารถทำอะไรได้บ้าง โดยอ้างอิงถึงความสามารถของผู้เชี่ยวชาญแต่ละคนอย่างแนบเนียน:
    - **การวิเคราะห์เชิงลึก:** "ผมสามารถค้นคว้าข้อมูลจากคลังหนังสือกว่าร้อยเล่มเพื่อสร้างบทวิเคราะห์เชิงลึกให้คุณได้" (อ้างอิงถึง PlannerAgent)
    - **ข่าวสาร:** "ผมสามารถสรุปข่าวสารและสถานการณ์ปัจจุบันที่เกิดขึ้นทั่วโลกให้คุณได้" (อ้างอิงถึง NewsAgent)
    - **โค้ด:** "ผมยังสามารถช่วยคุณเขียนโค้ด, วิเคราะห์ข้อมูล, หรือแก้ปัญหาทางเทคนิคได้อีกด้วย" (อ้างอิงถึง CodeInterpreterAgent)
    - **หนังสือ:** "และแน่นอน ผมสามารถแนะนำหนังสือที่น่าสนใจ หรือบอกรายชื่อหนังสือทั้งหมดที่ผมมีได้เสมอครับ" (อ้างอิงถึง LibrarianAgent)

**กฎเหล็ก:**
- รักษาบุคลิกของ "เฟิง" ที่สุขุมและเป็นมิตรไว้เสมอ
- เป้าหมายคือการสร้าง "บทสนทนา" ไม่ใช่แค่การ "ให้ข้อมูล"

**คำถามของผู้ใช้:** "{query}"
**คำตอบของเฟิง (ในฐานะสหายและเจ้าบ้าน):**
"""
        print("🤝 General Conversation Agent (V1 - Companion) is ready.")

    def _get_intuitive_context(self, query: str) -> str:
        """
        ใช้ KG-RAG เพื่อดึง "สัญชาตญาณ" จากความทรงจำและกราฟความรู้
        """
        contexts = []
        if self.rag_engine and hasattr(self.rag_engine, 'search_memory'):
            try:
                memory_results = self.rag_engine.search_memory(query, top_k=1)
                if memory_results:
                    contexts.append("\n".join([f"- ความทรงจำที่เกี่ยวข้อง: {mem.get('text', '')}" for mem in memory_results]))
            except Exception as e:
                print(f"  - Intuition (Memory RAG) Error: {e}")

        if self.graph_manager:
            try:
                graph_results = self.graph_manager.find_related_concepts(query, limit=2)
                if graph_results:
                    contexts.append("\n".join([f"- ความเชื่อมโยงที่เกี่ยวข้อง: '{rel.get('source')}' {rel.get('relationship')} '{rel.get('target')}'" for rel in graph_results]))
            except Exception as e:
                print(f"  - Intuition (Graph) Error: {e}")
        
        return "\n".join(contexts) if contexts else "ไม่มี"

    def handle(self, query: str, short_term_memory: List[Dict[str, Any]]) -> str:
        """
        เมธอดหลักที่ Dispatcher จะเรียกใช้
        """
        print(f"💬 [General Conversation Agent] Handling: '{query[:40]}...'")
        api_key = self.key_manager.get_key()
        if not api_key:
            return "ขออภัยครับ ตอนนี้ผมไม่สามารถสนทนาต่อได้ในขณะนี้"

        try:
            client = Groq(api_key=api_key)
            intuitive_context = self._get_intuitive_context(query)
            history_context = "\n".join([f"- {mem.get('role')}: {mem.get('content')}" for mem in short_term_memory])
            
            prompt = self.general_conversation_prompt.format(
                intuitive_context=intuitive_context,
                history_context=history_context,
                query=query
            )
            
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model_name,
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ GeneralConversationAgent LLM Error: {e}")
            return "ขออภัยครับ เกิดข้อผิดพลาดในการสนทนา"
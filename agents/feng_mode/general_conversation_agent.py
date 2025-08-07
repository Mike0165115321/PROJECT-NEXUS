# agents/feng_mode/general_conversation_agent.py
# (V2 - The Sage's Companion)

import json
from typing import Dict, List, Any
from groq import Groq

class GeneralConversationAgent:
    """
    Agent ที่รับผิดชอบการสนทนาทั่วไปทั้งหมด (GENERAL_CONVERSATION)
    (เวอร์ชันอัปเกรด: มีสัญชาตญาณที่เฉียบคมขึ้น)
    """
    def __init__(self, key_manager, model_name: str, rag_engine, graph_manager, persona_prompt: str):
        self.key_manager = key_manager
        self.model_name = model_name
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

    def _extract_keywords_for_intuition(self, query: str) -> List[str]:
        """ใช้ LLM (โมเดลเล็ก) เพื่อสกัด Keywords สำหรับการค้นหากราฟ"""
        print(f"  - 🧠 Extracting keywords from: '{query}' for intuition...")
        prompt = f"""
คุณคือ AI ผู้เชี่ยวชาญด้านการสกัด "คำสำคัญ" (Keywords) จากประโยค เพื่อใช้ในการค้นหาฐานข้อมูล Knowledge Graph

**กฎ:**
1.  อ่าน "ประโยค" ที่ให้มา และจับใจความถึง "แนวคิดหลัก"
2.  สกัดเฉพาะ "แนวคิดหลัก" หรือ "คำนาม" ที่สำคัญที่สุดออกมา 2-3 คำ
3.  ตอบกลับเป็น JSON Array ของ Strings เท่านั้น (เช่น ["คำที่ 1", "คำที่ 2"])

**ประโยคที่ต้องวิเคราะห์:** "{query}"
**Keywords (JSON Array):**
"""
        try:
            api_key = self.key_manager.get_key()
            client = Groq(api_key=api_key)
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192", # ใช้โมเดลเล็กและเร็วสำหรับงานนี้เสมอ
                response_format={"type": "json_object"}
            )
            keywords = json.loads(chat_completion.choices[0].message.content)
            if isinstance(keywords, list) and all(isinstance(k, str) for k in keywords):
                print(f"  -> Keywords extracted for intuition: {keywords}")
                return keywords
            return []
        except Exception:
            return [word for word in query.split() if len(word) > 3]

    # [UPGRADE] อัปเกรดฟังก์ชันนี้ให้ใช้ Keywords
    def _get_intuitive_context(self, query: str) -> str:
        """
        ใช้ Keywords ที่สกัดได้ เพื่อดึง "สัญชาตญาณ" จากความทรงจำและกราฟความรู้
        """
        # 1. สกัด Keywords ก่อน
        keywords = self._extract_keywords_for_intuition(query)
        if not keywords:
            return "ไม่มี"

        contexts = []

        # 2. ใช้ Keywords ค้นหาใน Graph
        print(f"  - 🕸️ Searching Graph with keywords: {keywords}")
        found_ids = set()
        for keyword in keywords:
            # สร้าง ID ที่คาดว่าจะเป็นไปได้
            possible_ids = [
                f"concept:{keyword.replace(' ', '-')}",
                f"book:{keyword.replace(' ', '-')}",
                f"technique:{keyword.replace(' ', '-')}"
            ]
            for entity_id in possible_ids:
                try:
                    graph_results = self.graph_manager.find_related_concepts(entity_id, limit=2)
                    for rel in graph_results:
                        target_id = rel.get('target_id')
                        if target_id and target_id not in found_ids:
                            contexts.append(f"- ความเชื่อมโยงที่เกี่ยวข้อง: '{rel.get('source')}' {rel.get('relationship')} '{rel.get('target')}'")
                            found_ids.add(target_id)
                except Exception as e:
                    print(f"  - Intuition (Graph) Error for '{entity_id}': {e}")
        
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
            # [UPGRADE] ตอนนี้ intuitive_context จะมีข้อมูลที่ถูกต้องแล้ว
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
            if api_key: self.key_manager.report_failure(api_key)
            return "ขออภัยครับ เกิดข้อผิดพลาดในการสนทนา"
# agents/counseling_mode/counselor_agent.py
# (V1 - Empathic Listening First)

from typing import Dict, List, Any
import google.generativeai as genai 

class CounselorAgent:
    """
    Agent ที่ทำหน้าที่เป็น "สหายผู้เข้าอกเข้าใจ" (Empathic Companion)
    สร้างพื้นที่ปลอดภัยและช่วยผู้ใช้ไตร่ตรองความรู้สึกของตนเอง
    """
    def __init__(self, key_manager, model_name: str, persona_prompt: str):
        self.key_manager = key_manager
        self.model_name = model_name
        self.counseling_prompt_template = persona_prompt + """
**ภารกิจ: สหายผู้เข้าอกเข้าใจ (The Empathic Companion)**

คุณคือ "เฟิง" ในบทบาทผู้รับฟังและให้คำปรึกษาที่เข้าอกเข้าใจ ภารกิจของคุณไม่ใช่การ "แก้ปัญหา" แต่คือการ "อยู่เคียงข้าง" และ "สะท้อน" ความรู้สึกของผู้ใช้ เพื่อช่วยให้เขาได้เข้าใจตัวเองและค้นพบทางออกด้วยตัวเอง

**ศิลปะแห่งการรับฟัง (The Art of Listening):**
1.  **Validate Feelings (ยอมรับความรู้สึก):** เริ่มต้นด้วยการยอมรับและแสดงความเข้าใจต่อความรู้สึกของผู้ใช้เสมอ (เช่น "ผมเข้าใจเลยว่าเรื่องนี้ทำให้คุณรู้สึกหนักใจ", "การรู้สึกเช่นนั้นเป็นเรื่องปกติมากครับ")
2.  **Reflective Listening (การฟังเชิงสะท้อน):** สรุปความและสะท้อนสิ่งที่คุณได้ยินกลับไป เพื่อให้ผู้ใช้รู้สึกว่ามีคนเข้าใจเขาจริงๆ
3.  **Ask Open-ended, Gentle Questions (ถามคำถามปลายเปิดอย่างอ่อนโยน):** ถามคำถามที่กระตุ้นให้ผู้ใช้ได้สำรวจความรู้สึกของตัวเองลึกขึ้น ไม่ใช่การซักไซ้ (เช่น "อะไรในสถานการณ์นั้นที่ทำให้คุณรู้สึกแย่ที่สุดครับ?", "คุณได้เรียนรู้อะไรเกี่ยวกับตัวเองจากเหตุการณ์นี้บ้างครับ?")

**กฎเหล็กที่สำคัญที่สุด:**
- **ห้ามให้คำแนะนำหรือทางแก้ไขโดยตรง (DO NOT GIVE SOLUTIONS):** จนกว่าผู้ใช้จะร้องขออย่างชัดเจน
- **ห้ามอ้างอิงหนังสือหรือข้อมูลภายนอก:** ในขั้นตอนนี้ ให้ตอบจากความเข้าอกเข้าใจเพียงอย่างเดียว
- **เป้าหมายคือการสร้าง "พื้นที่ปลอดภัย" (Safe Space):** ทำให้ผู้ใช้รู้สึกสบายใจที่จะเปิดใจ

**ประวัติการสนทนาล่าสุด:**
{history_context}

**Input ล่าสุดจากผู้ใช้:** "{query}"
**คำตอบของเฟิง (ในฐานะผู้รับฟัง):**
"""
        print("❤️  ทีมสนทนาและให้คำปรึกษา (CounselorAgent) รายงานตัวพร้อมปฏิบัติภารกิจ")

    def handle(self, query: str, short_term_memory: List[Dict[str, Any]]) -> str:
        """
        เมธอดหลักที่ Dispatcher จะเรียกใช้
        ทำหน้าที่สร้างคำตอบที่แสดงความเข้าอกเข้าใจ
        """
        print(f"❤️  [Counselor Agent] Handling sensitive query: '{query[:40]}...'")
        
        history_context = "\n".join([f"- {mem.get('role')}: {mem.get('content')}" for mem in short_term_memory])
        if not history_context:
            history_context = "(ยังไม่มีประวัติการสนทนา)"

        api_key = self.key_manager.get_key()
        if not api_key:
            return "ขออภัยครับ ตอนนี้ผมอาจจะยังไม่พร้อมที่จะรับฟังเรื่องราวที่ละเอียดอ่อนเช่นนี้"

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(self.model_name)
            
            prompt = self.counseling_prompt_template.format(
                history_context=history_context,
                query=query
            )
            
            response = model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"❌ CounselorAgent LLM Error: {e}")
            return "ผมต้องขออภัยด้วยครับ ดูเหมือนว่าตอนนี้ผมจะยังไม่สามารถไตร่ตรองในเรื่องนี้ได้อย่างเต็มที่"
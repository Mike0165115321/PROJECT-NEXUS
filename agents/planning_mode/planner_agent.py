# agents/planning_mode/planner_agent.py
# (V3.1 - Centralized Config & Cleaned Prompts)

import google.generativeai as genai
import json
import re
import traceback
from typing import List, Dict, Any

class PlannerAgent:
    def __init__(self, key_manager, model_name: str, rag_engine, persona_prompt: str):
        self.key_manager = key_manager
        self.rag_engine = rag_engine
        self.model_name = model_name # ⭐️ ใช้ model_name ที่ได้รับมา
        self.max_context_chunks = 5 
        self.planning_prompt_template = """
คุณคือ "สถาปนิกแห่งความรู้" (Knowledge Architect) ภารกิจของคุณคือการแปลง "คำถาม" ของผู้ใช้ให้กลายเป็น "พิมพ์เขียวสำหรับการค้นคว้า" ที่สมบูรณ์แบบ เพื่อให้ทีมงานสามารถรวบรวมข้อมูลมาสร้างเป็นภูมิปัญญาได้

**กระบวนการออกแบบพิมพ์เขียว (Blueprint Design Process):**
1.  วิเคราะห์แก่นแท้ (Analyze Core Intent): เจาะลึกไปให้ถึงเจตนาที่แท้จริงของผู้ใช้ เขาต้องการ 'นิยาม', 'ขั้นตอน', 'การเปรียบเทียบ', หรือ 'การวิเคราะห์เชิงลึก'?
2.  สร้างเสาหลัก (Identify Core Pillars): ดึง "แนวคิดหลัก" (Key Concepts) ที่เป็นเหมือนเสาหลักของคำตอบออกมา 2-4 อย่าง
3.  ออกแบบโครงสร้าง (Structure the Narrative): จินตนาการถึงบทวิเคราะห์ที่ดีที่สุด แล้วออกแบบ "โครงสร้างของเรื่องราว" ที่จะเล่า เช่น
    -   บทนำ: เริ่มด้วยการนิยามแนวคิดหลัก
    -   เนื้อหา: ขยายความด้วยตัวอย่าง, เปรียบเทียบข้อดี-ข้อเสีย, หรืออธิบายความเชื่อมโยง
    -   บทสรุป: สรุปเป็นหลักการที่นำไปปรับใช้ได้
4.  สร้างรายการวัสดุ (Generate Sub-queries): สร้าง "คำค้นหาย่อย" ที่จะทำหน้าที่หาข้อมูลมาเติมเต็มแต่ละส่วนของโครงสร้างเรื่องราวที่คุณออกแบบไว้
5.  ระบุแหล่งข้อมูล (Target Categories): จากแนวคิดหลักทั้งหมด ให้ระบุ "หมวดหมู่หนังสือ" ที่เกี่ยวข้องที่สุดจากรายการที่มีให้ เพื่อการค้นหาที่แม่นยำ

**ผลลัพธ์สุดท้าย (Final Output):**
จงสรุปผลการออกแบบทั้งหมดออกมาเป็น JSON object ที่สมบูรณ์เท่านั้น ห้ามมีข้อความอื่นนอก JSON

**โครงสร้าง JSON:**
{
    "thought": "สรุปแผนการสั้นๆ: เริ่มจากนิยาม, ตามด้วยตัวอย่าง, และจบด้วยการประยุกต์ใช้",
    "sub_queries": ["คำจำกัดความของ...", "ตัวอย่างการใช้...", "ข้อดีและข้อเสียของ..."],
    "search_in": ["book", "memory"],
    "categories": ["หมวดหมู่ที่แม่นยำที่สุด 1", "หมวดหมู่ที่แม่นยำที่สุด 2"]
}

**ข้อมูลประกอบ:**
- **หมวดหมู่หนังสือทั้งหมดที่มี:** {available_categories}

**คำถามของผู้ใช้:** "{query}"
**ผลลัพธ์ JSON:**
"""
        self.master_prompt_template = persona_prompt + """
**ภารกิจ: การสังเคราะห์ภูมิปัญญา (Wisdom Synthesis)**

คุณคือ "เฟิง" ในบทบาท "ปราชญ์ผู้สังเคราะห์" (The Synthesizing Sage) ภารกิจของคุณไม่ใช่การรายงานข้อมูล แต่คือการ **"ตกผลึก"** ข้อมูลดิบที่หลากหลายให้กลายเป็น **"ภูมิปัญญา"** ที่สอดคล้อง, ลึกซึ้ง, และนำไปปรับใช้ได้จริง

**กระบวนการตกผลึกทางปัญญา (The Crystallization Process):**
1.  มองหาความเชื่อมโยง (Identify Connections): อ่าน "บริบทข้อมูล" ทั้งหมด แล้วมองหา "เส้นด้ายสีทอง" (The Golden Thread) ที่ร้อยเรียงแนวคิดต่างๆ ที่ดูเหมือนไม่เกี่ยวข้องกัน ให้กลายเป็นเรื่องราวเดียวกัน
2.  สกัดแก่นแท้ (Extract the Essence): กลั่นกรองข้อมูลทั้งหมดให้เหลือเพียง "หลักการ" (Principles) หรือ "แก่นความคิด" (Core Ideas) ที่สำคัญที่สุด
3.  สร้างมุมมองใหม่ (Create a New Perspective): นำหลักการที่สกัดได้มาผสมผสานกันเพื่อสร้างเป็น "มุมมองใหม่" หรือ "บทเรียน" ที่ผู้ใช้ไม่เคยเห็นมาก่อน นี่คือการสร้างคุณค่าที่แท้จริง
4.  เชื่อมโยงกับผู้ใช้ (Connect to the User): นำภูมิปัญญาที่ตกผลึกได้ มาเชื่อมโยงกับ "ประวัติการสนทนาล่าสุด" เพื่อทำให้คำตอบรู้สึกเหมือนเป็นคำแนะนำที่สร้างขึ้นเพื่อเขาโดยเฉพาะ

**ข้อมูลประกอบ:**
- **ประวัติการสนทนาล่าสุด:** 
{history_context}
- **บริบทข้อมูลที่ค้นหามาได้ (ข้อมูลดิบ):**
---
{rag_context}
---

**กฎเหล็กในการสร้างบทวิเคราะห์:**
1.  ห้ามตอบสั้นเด็ดขาด (CRUCIAL: DO NOT BE CONCISE): ผลงานของคุณต้องสะท้อนความลึกซึ้งทางความคิด มีความยาว, ละเอียด, และเต็มไปด้วยภูมิปัญญา
2.  เล่าเรื่อง ไม่ใช่รายงาน: เขียนในรูปแบบเรียงความที่ลื่นไหล มีการเกริ่นนำ, ขยายความ, และสรุปผลอย่างเป็นธรรมชาติ
3.  เป็นเจ้าของภูมิปัญญา: หลอมรวมทุกอย่างให้กลายเป็นความคิดและคำแนะนำของ "เฟิง" แต่เพียงผู้เดียว

**คำสั่ง:**
จง "ตกผลึก" ข้อมูลทั้งหมดให้กลายเป็น "บทวิเคราะห์ฉบับร่าง" ที่ดีที่สุด

**บทวิเคราะห์ฉบับร่าง (จากปราชญ์เฟิง):**
"""

    def _extract_json(self, text: str) -> str:
        # ... (โค้ดส่วนนี้ดีอยู่แล้ว ไม่ต้องแก้ไข) ...
        match = re.search(r'```(json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            return match.group(2)
        if text.strip().startswith('{') and text.strip().endswith('}'):
            return text
        raise json.JSONDecodeError("Could not find JSON object in the response.", text, 0)

    def _call_llm(self, prompt: str) -> str:
        # ... (โค้ดส่วนนี้ดีอยู่แล้ว ไม่ต้องแก้ไข) ...
        api_key = self.key_manager.get_key()
        if not api_key: raise Exception("No available API keys.")
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if "429" in str(e):
                self.key_manager.report_failure(api_key)
                return self._call_llm(prompt)
            raise e

    def handle(self, query: str, short_term_memory: List[Dict], available_categories: List[str]) -> Dict[str, Any]:
        search_logs = []
        try:
            print("🧠 Planner Agent: Step 1 - Creating search plan...")
            # ⭐️ 4. ใช้ .format() กับ Template ที่ถูกต้อง ⭐️
            plan_prompt = self.planning_prompt_template.format(
                query=query, 
                available_categories=json.dumps(available_categories, ensure_ascii=False)
            )
            plan_response_text = self._call_llm(plan_prompt)

            # ... (ส่วนของการประมวลผล Plan และ Retrieval ดีอยู่แล้ว ไม่ต้องแก้ไข) ...
            try:
                json_string = self._extract_json(plan_response_text)
                plan = json.loads(json_string)
            except json.JSONDecodeError:
                print(f"⚠️ Warning: Failed to decode JSON from plan response. Using fallback plan.")
                plan = {"sub_queries": [query], "search_in": ["book", "memory"], "categories": []}

            search_in = plan.get("search_in", ["book", "memory"])
            target_categories = plan.get("categories", [])
            sub_queries = plan.get("sub_queries", [query])
            sub_queries = list(dict.fromkeys(sub_queries))
            
            print(f"  -> Step 2 - Executing search plan...")
            all_chunks = []
            # ... (ส่วนของการค้นหา book และ memory ดีอยู่แล้ว) ...
            if "book" in search_in and self.rag_engine:
                num_cats_to_search = len(target_categories) if target_categories else len(available_categories)
                for q in sub_queries:
                    log_msg = f"🔍 Searching BOOKS in {num_cats_to_search} categories for '{q}'..."
                    print(f"  {log_msg}")
                    search_logs.append(log_msg)
                    result = self.rag_engine.search_books(q, 20, True, target_categories)
                    for chunk in result.get("raw_chunks", []):
                        chunk['source'] = 'book'
                        all_chunks.append(chunk)

            if "memory" in search_in and self.rag_engine and self.rag_engine.memory_index:
                for q in sub_queries:
                    log_msg = f"🧠 Searching MEMORY for connections to '{q}'..."
                    print(f"  {log_msg}")
                    search_logs.append(log_msg)
                    memory_chunks = self.rag_engine.search_memory(q, top_k=3)
                    for chunk in memory_chunks:
                        chunk['source'] = 'memory'
                        all_chunks.append(chunk)

            if not all_chunks:
                thought_process = {"plan": plan, "search_logs": search_logs, "retrieved_chunks_count": 0, "final_context_chunks": []}
                return {"answer": "ขออภัยครับ ผมไม่พบข้อมูลที่เกี่ยวข้องเลย", "thought_process": thought_process}

            unique_chunks = list({item.get('embedding_text', item.get('text')): item for item in all_chunks}.values())
            final_selection = unique_chunks[:self.max_context_chunks]
            rag_context = "\n\n---\n\n".join([item.get("embedding_text", item.get("text", "")) for item in final_selection])

            print("  -> Step 3 - Synthesizing final draft...")
            history_context = "\n".join([f"- {mem['role']}: {mem['content']}" for mem in short_term_memory])
            # ⭐️ 4. ใช้ .format() กับ Template ที่ถูกต้อง ⭐️
            synthesis_prompt = self.master_prompt_template.format(history_context=history_context, rag_context=rag_context)
            final_draft = self._call_llm(synthesis_prompt)

            thought_process = {
                "plan": plan,
                "search_logs": search_logs,
                "retrieved_chunks_count": len(unique_chunks),
                "final_context_chunks": final_selection
            }
            return {"answer": final_draft, "thought_process": thought_process}

        except Exception as e:
            print(f"❌ An unexpected error in Planner Agent: {e}")
            traceback.print_exc()
            return {"answer": "ขออภัยครับ เกิดข้อผิดพลาดในการวางแผนและวิเคราะห์ข้อมูล", "thought_process": {"error": str(e), "search_logs": search_logs}}
# agents/planning_mode/planner_agent.py
# (V9.0 - Asynchronous & Concurrent)

import google.generativeai as genai
import json
import re
import traceback
from typing import List, Dict, Any
import asyncio 

class PlannerAgent:
    def __init__(self, key_manager, model_name: str, rag_engine, persona_prompt: str):
        self.key_manager = key_manager
        self.rag_engine = rag_engine
        self.model_name = model_name
        self.max_context_chunks = 5 
        self.planning_prompt_template = """คุณคือ "สถาปนิกแห่งความรู้" (Knowledge Architect) ภารกิจของคุณคือการแปลง "คำถาม" ของผู้ใช้ให้กลายเป็น "พิมพ์เขียวสำหรับการค้นคว้า" ที่สมบูรณ์แบบ เพื่อให้ทีมงานสามารถรวบรวมข้อมูลมาสร้างเป็นภูมิปัญญาได้
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
{{
    "thought": "สรุปแผนการสั้นๆ: เริ่มจากนิยาม, ตามด้วยตัวอย่าง, และจบด้วยการประยุกต์ใช้",
    "sub_queries": ["คำจำกัดความของ...", "ตัวอย่างการใช้...", "ข้อดีและข้อเสียของ..."],
    "search_in": ["book", "memory"],
    "categories": ["หมวดหมู่ที่แม่นยำที่สุด 1", "หมวดหมู่ที่แม่นยำที่สุด 2"]
}}
**ข้อมูลประกอบ:**
- **หมวดหมู่หนังสือทั้งหมดที่มี:** {available_categories}
**คำถามของผู้ใช้:** "{query}"
**ผลลัพธ์ JSON:**
"""
        self.master_prompt_template = persona_prompt + """
**ภารกิจ: การถักทอภูมิปัญญา (The Weaving of Wisdom)**
คุณคือ "ฟางซิน" ในบทบาท "ปราชญ์ผู้สังเคราะห์" (The Synthesizing Sage) ภารกิจของคุณไม่ใช่แค่การรายงานข้อมูล แต่คือการ **"ถักทอ"** ข้อมูลดิบที่หลากหลายจากคลังความรู้ ให้กลายเป็น **"ผืนผ้าแห่งภูมิปัญญา"** ที่สอดคล้อง, ลึกซึ้ง, และนำไปปรับใช้ได้จริง
**กระบวนการถักทอภูมิปัญญา (The Wisdom Weaving Process):**
1.  **ค้นหาเส้นด้ายสีทอง (Identify the Golden Thread):** อ่าน "บริบทข้อมูล" ทั้งหมด แล้วตอบคำถามนี้ในใจ: "อะไรคือแก่นความคิดหลัก หรือความตึงเครียด (Tension) ที่ซ่อนอยู่ที่ร้อยเรียงข้อมูลทั้งหมดนี้เข้าด้วยกัน?"
2.  **สังเคราะห์หลักการข้ามศาสตร์ (Synthesize Cross-Disciplinary Principles):** กลั่นกรองข้อมูลทั้งหมดให้เหลือเพียง "หลักการ" (Principles) ที่สำคัญที่สุด **เมื่ออ้างอิงแนวคิดใด ให้กล่าวถึงชื่อหนังสือที่เป็นแหล่งที่มาอย่างเป็นธรรมชาติ** (เช่น "จากหนังสือ 'The Art of War' เราเรียนรู้ว่า...") เพื่อแสดงให้เห็นถึงการเชื่อมโยงความรู้
3.  **สร้างมุมมองใหม่ที่นำไปใช้ได้ (Create an Actionable Perspective):** นำหลักการที่สกัดได้มาผสมผสานกันเพื่อสร้างเป็น "มุมมองใหม่" หรือ "กรอบความคิด (Framework)" ที่ผู้ใช้สามารถนำไปปรับใช้เพื่อมองปัญหาของตนเองได้ชัดเจนขึ้น
4.  **เชื่อมโยงกับผู้ใช้ (Connect to the User):** นำภูมิปัญญาที่ตกผลึกได้ มาเชื่อมโยงกับ "ประวัติการสนทนาล่าสุด" เพื่อทำให้คำตอบรู้สึกเหมือนเป็นคำแนะนำที่สร้างขึ้นเพื่อเขาโดยเฉพาะ
**ข้อมูลประกอบ:**
- **ประวัติการสนทนาล่าสุด:**
{history_context}
- **บริบทข้อมูลที่ค้นหามาได้ (ข้อมูลดิบ):**
---
{rag_context}
---
**กฎเหล็กในการสร้างบทวิเคราะห์:**
1.  **โครงสร้างต้องชัดเจน:** ใช้ Markdown (เช่น `# หัวข้อหลัก`, `## หัวข้อย่อย`, `* รายการ`) เพื่อจัดระเบียบความคิด ทำให้อ่านง่ายและน่าติดตาม
2.  **ต้องลึกซึ้งและละเอียด:** ผลงานของคุณต้องสะท้อนความลึกซึ้งทางความคิด มีความยาว, ละเอียด, และเต็มไปด้วยภูมิปัญญา ห้ามตอบสั้นเด็ดขาด
3.  **เล่าเรื่อง ไม่ใช่รายงาน:** เขียนในรูปแบบเรียงความที่ลื่นไหล มีการเกริ่นนำที่น่าสนใจ, ขยายความอย่างมีตรรกะ, และสรุปผลอย่างทรงพลัง
4.  **เป็นเจ้าของภูมิปัญญา:** หลอมรวมทุกอย่างให้กลายเป็นความคิดและคำแนะนำของ "เฟิง" แต่เพียงผู้เดียว
**คำสั่ง:**
จง "ถักทอ" ข้อมูลทั้งหมดให้กลายเป็น "บทวิเคราะห์ฉบับร่าง" ที่ดีที่สุดตามโครงสร้างและกฎเหล็กข้างต้น
**บทวิเคราะห์ฉบับร่าง (จากปราชญ์ฟางซิน):**

"""
        
        self.model = genai.GenerativeModel(self.model_name)

    def _extract_json(self, text: str) -> str:
        match = re.search(r'```(json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            return match.group(2)
        if text.strip().startswith('{') and text.strip().endswith('}'):
            return text
        raise json.JSONDecodeError("Could not find JSON object in the response.", text, 0)

    async def _call_llm_async(self, prompt: str) -> str:
        api_key = await self.key_manager.get_key()
        if not api_key: raise Exception("No available API keys.")
        try:
            genai.configure(api_key=api_key)
            
            response = await self.model.generate_content_async(prompt)
            return response.text
        
        except Exception as e:
            if "429" in str(e) or "resource_exhausted" in str(e).lower():
                print(f"⚠️ 429 Error. Key {api_key[:5]}... failed. Retrying...")
                self.key_manager.report_failure(api_key)
                await asyncio.sleep(1) 
                return await self._call_llm_async(prompt) 
            raise e
    
    async def handle(self, query: str, short_term_memory: List[Dict], available_categories: List[str]) -> Dict[str, Any]:
        search_logs = []
        plan_thought = "Plan generation failed before it began."
        plan = {}
        
        try:
            print("🧠 Planner Agent: Step 1 - Creating search plan...")
            plan_prompt = self.planning_prompt_template.format(
                query=query, 
                available_categories=json.dumps(available_categories, ensure_ascii=False)
            )
            plan_response_text = await self._call_llm_async(plan_prompt)

            try:
                json_string = self._extract_json(plan_response_text)
                plan = json.loads(json_string)
                plan_thought = plan.get("thought", "AI did not provide a thought in the plan.")
                print(f" 	-> Planner Thought: {plan_thought}")
            except json.JSONDecodeError:
                print(f"⚠️ Warning: Failed to decode JSON from plan response. Using fallback plan.")
                plan = {"sub_queries": [query], "search_in": ["book", "memory"], "categories": []}
                plan_thought = "Fallback plan initiated due to JSON decode error."

            search_in = plan.get("search_in", ["book", "memory"])
            target_categories = plan.get("categories", [])
            sub_queries = plan.get("sub_queries", [query])
            sub_queries = list(dict.fromkeys(sub_queries)) 
            
            print(f" 	-> Step 2 - Executing search plan... (CONCURRENTLY)")
            all_chunks = []
            
            search_tasks = []
            
            if "book" in search_in and self.rag_engine:
                num_cats_to_search = len(target_categories) if target_categories else len(available_categories)
                for q in sub_queries:
                    log_msg = f"🔍 Scheduling BOOK search in {num_cats_to_search} categories for '{q}'..."
                    print(f" 	{log_msg}")
                    search_logs.append(log_msg)
                    
                    search_tasks.append(
                        self.rag_engine.search_books(
                            q, 
                            self.max_context_chunks,  
                            True, 
                            target_categories
                        )
                    )

            if "memory" in search_in and self.rag_engine and self.rag_engine.memory_index:
                for q in sub_queries:
                    log_msg = f"🧠 Scheduling MEMORY search for connections to '{q}'..."
                    print(f" 	{log_msg}")
                    search_logs.append(log_msg)
                    
                    search_tasks.append(self.rag_engine.search_memory(q, top_k=3))

            if search_tasks:
                print(f" 	-> 🚀 Executing {len(search_tasks)} tasks concurrently via asyncio.gather...")
                results = await asyncio.gather(*search_tasks)
                
                for result in results:
                    if isinstance(result, dict) and 'raw_chunks' in result:
                        for chunk in result.get("raw_chunks", []):
                            chunk['source'] = 'book'
                            all_chunks.append(chunk)
                    elif isinstance(result, list):
                        for chunk in result:
                            chunk['source'] = 'memory'
                            all_chunks.append(chunk)


            if not all_chunks:
                thought_process = {"plan_thought": plan_thought, "plan": plan, "search_logs": search_logs, "retrieved_chunks_count": 0, "final_context_chunks": []}
                return {"answer": "ขออภัยครับ ผมไม่พบข้อมูลที่เกี่ยวข้องเลย", "thought_process": thought_process}

            sorted_chunks = sorted(all_chunks, key=lambda x: x.get('rerank_score', 0.0), reverse=True)
            unique_chunks_map = {item.get('embedding_text', item.get('text')): item for item in sorted_chunks}
            final_selection = list(unique_chunks_map.values())[:self.max_context_chunks]
            
            rag_context = "\n\n---\n\n".join([item.get("embedding_text", item.get("text", "")) for item in final_selection])

            print(" 	-> Step 3 - Synthesizing final draft...")
            history_context = "\n".join([f"- {mem['role']}: {mem['content']}" for mem in short_term_memory])
            synthesis_prompt = self.master_prompt_template.format(history_context=history_context, rag_context=rag_context)
            
            final_draft = await self._call_llm_async(synthesis_prompt)

            thought_process = {
                "plan_thought": plan_thought,
                "plan": plan,
                "search_logs": search_logs,
                "retrieved_chunks_count": len(unique_chunks_map),
                "final_context_chunks": [chunk['embedding_text'] for chunk in final_selection] 
            }
            return {"answer": final_draft, "thought_process": thought_process}

        except Exception as e:
            print(f"❌ An unexpected error in Planner Agent: {e}")
            traceback.print_exc()
            return {"answer": "ขออภัยครับ เกิดข้อผิดพลาดในการวางแผนและวิเคราะห์ข้อมูล", "thought_process": {"error": str(e), "plan_thought": plan_thought, "search_logs": search_logs}}
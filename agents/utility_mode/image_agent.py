# agents/utility_mode/image_agent.py
# (V36.0 - Async & CORRECTED Groq Fix)

import httpx  
import json
import random
from typing import Optional, Dict
from groq import AsyncGroq  
import asyncio  

class ImageAgent:
    def __init__(self, unsplash_key: str, key_manager, model_name: str):
        """
        [V36] เริ่มต้นการทำงาน (แบบ Async ที่ถูกต้อง)
        """
        self.unsplash_key = unsplash_key
        self.groq_key_manager = key_manager
        self.model_name = model_name
        self.api_url = "https://api.unsplash.com/search/photos"
        
        self.http_client = httpx.AsyncClient(timeout=10.0) 
        
        print("🖼️  Image Agent (V36.0 - Async Curator) is ready.")

    async def _call_llm_async(self, prompt: str) -> Optional[Dict]:
        
        api_key = await self.groq_key_manager.get_key()
        if not api_key: raise Exception("No available Groq API keys.")
        
        try:
            client = AsyncGroq(api_key=api_key)
            
            chat_completion = await client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model_name,
                temperature=0.1
            )
            llm_response = chat_completion.choices[0].message.content
            cleaned_response = llm_response.strip().replace("```json", "").replace("```", "")
            params = json.loads(cleaned_response)
            return params
        
        except Exception as e:
            print(f"❌ ImageAgent LLM Error: {e}")
            if api_key: self.groq_key_manager.report_failure(api_key)
            
            if api_key and ("429" in str(e).lower() or "service_unavailable" in str(e).lower()):
                print(" 	 -> Retrying _call_llm_async...")
                await asyncio.sleep(1)
                return await self._call_llm_async(prompt) 
            
            return None 
            
    async def _extract_search_parameters(self, query: str) -> Optional[Dict]:
        print(f" 	- 🧠 [Image Agent V36] Performing deep analysis on: '{query}' (Async)")
        prompt = f"""
คุณคือ AI ที่มีหน้าที่แปลงคำขอรูปภาพให้เป็น JSON object เท่านั้น

**คำสั่ง:**
วิเคราะห์ "คำขอ" ด้านล่าง และสร้าง JSON object ที่มี keys: `search_term`, `color`, `style`

**กฎที่ต้องปฏิบัติตามอย่างเคร่งครัด:**
1.  `search_term` (string): แปลคำสำคัญหลักเป็นภาษาอังกฤษ
2.  `color` (string or null): ถ้ามี "โทนสี" ให้ใส่ชื่อสีเป็นภาษาอังกฤษ, ถ้าไม่มีให้เป็น `null`
3.  `style` (string or null): ถ้ามี "อารมณ์" หรือ "สไตล์" ให้ใส่เป็นคำคุณศัพท์ภาษาอังกฤษ, ถ้าไม่มีให้เป็น `null`
4.  **ห้ามมีข้อความอธิบายใดๆ ทั้งสิ้น**
5.  **คำตอบของคุณทั้งหมดต้องเป็น JSON object ที่ถูกต้อง เริ่มต้นด้วย `{{` และจบด้วย `}}` เท่านั้น**

**ตัวอย่าง:**
- คำขอ: "หารูปท้องฟ้าสวยๆ ตอนเย็นๆ โทนสีส้ม"
- ผลลัพธ์: {{"search_term": "beautiful evening sky", "color": "orange", "style": null}}

- คำขอ: "ขอดูภาพทะเลที่ดูเหงาๆ หน่อย"
- ผลลัพธ์: {{"search_term": "sea ocean", "color": null, "style": "lonely"}}

**คำขอ:** "{query}"
**ผลลัพธ์:**
"""
        try:
            params = await self._call_llm_async(prompt) 
            
            if params:
                print(f" 	- ✅ Extracted search parameters: {params}")
                return params
            else:
                raise ValueError("LLM returned no valid JSON params.")
                
        except Exception as e:
            print(f" 	- ⚠️ Parameter extraction failed: {e}")
            return None

    async def _search(self, search_params: Dict) -> Optional[Dict]:
        """
        [V23] ฟังก์ชันค้นหาที่ใช้ 'httpx' (Async)
        """
        if not self.unsplash_key:
            print("❌ [Image Agent] Error: UNSPLASH_ACCESS_KEY is not configured.")
            return None

        term = search_params.get('search_term', '')
        if search_params.get('style'):
            term = f"{search_params['style']} {term}"

        params = {
            'query': term, 'per_page': 20,
            'orientation': 'landscape', 'lang': 'en'
        }
        if search_params.get('color'):
            params['color'] = search_params['color']
        
        headers = {'Authorization': f'Client-ID {self.unsplash_key}'}

        try:
            print(f"🖼️  [Image Agent V36] Searching Unsplash (Async) for: '{term}'...")
            
            response = await self.http_client.get(self.api_url, headers=headers, params=params)
            
            response.raise_for_status()
            data = response.json()

            if results := data.get('results'):
                image_to_show = random.choice(results)
                
                image_info = {
                    "url": image_to_show['urls']['regular'],
                    "description": image_to_show.get('alt_description', 'No description available.'),
                    "photographer": image_to_show['user']['name'],
                    "profile_url": image_to_show['user']['links']['html']
                }
                print(f"✅ [Image Agent] Randomly selected image by {image_info['photographer']}")
                return image_info
            else:
                print(f"🟡 [Image Agent] No results found for '{term}'.")
                return None

        except Exception as e:
            print(f"❌ [Image Agent] An unexpected error occurred during search: {e}")
            return None

    async def handle(self, query: str) -> Optional[Dict]:
        search_params = await self._extract_search_parameters(query) 
        
        if search_params and search_params.get('search_term'):
            return await self._search(search_params) 
        
        print(" 	- 🟡 Fallback: Could not extract structured parameters. Using simple keyword extraction.")
        simple_term = query.replace("หารูปภาพ", "").replace("หารูป", "").replace("รูปภาพของ", "").strip()
        
        return await self._search({"search_term": simple_term}) 
# agents/utility_mode/image_agent.py
# (V3 - LLM-Powered & Intelligent)

import requests
import re
import json
from typing import Optional, Dict
from groq import Groq

class ImageAgent:
    """
    Agent ที่เชี่ยวชาญด้านการค้นหารูปภาพ (เวอร์ชันอัปเกรด: ใช้ LLM สกัด Keyword)
    """
    def __init__(self, unsplash_key: str, key_manager, model_name: str):
        """
        เริ่มต้นการทำงานโดยรับทรัพยากรที่จำเป็นทั้งหมดเข้ามา
        """
        self.unsplash_key = unsplash_key
        self.groq_key_manager = key_manager
        self.model_name = model_name
        self.api_url = "https://api.unsplash.com/search/photos"
        print("🖼️  Image Agent (V3 - LLM-Powered) is ready.")

    def _extract_and_translate_search_term(self, query: str) -> Optional[str]:
        """
        ใช้ LLM (Groq 8B) เพื่อสกัดและแปลคำค้นหาจากภาษาไทยเป็นภาษาอังกฤษ
        """
        print(f"  - 🧠 [Image Agent] Extracting keywords from: '{query}'")
        prompt = f"""
คุณคือ AI ผู้เชี่ยวชาญด้านการแปลง "คำขอรูปภาพภาษาไทย" ให้กลายเป็น "คำค้นหาภาษาอังกฤษ" ที่สั้นและกระชับที่สุดสำหรับ Image Search API (เช่น Unsplash)

**กฎ:**
1.  อ่าน "คำขอ" และจับใจความถึง "วัตถุหลัก" และ "ลักษณะเด่น"
2.  สกัดเฉพาะคำสำคัญเหล่านั้นออกมา
3.  แปลคำสำคัญเป็นภาษาอังกฤษ
4.  รวมคำภาษาอังกฤษทั้งหมดเข้าด้วยกันด้วยการเว้นวรรค
5.  ตอบกลับเป็น String เท่านั้น

**ตัวอย่าง:**
- คำขอ: "หารูปภูเขาสวยๆ ตอนพระอาทิตย์ขึ้น"
- ผลลัพธ์: "beautiful mountain sunrise"

- คำขอ: "ขอดูภาพแมวน่ารักๆ กำลังนอนหลับ"
- ผลลัพธ์: "cute cat sleeping"

**คำขอ:** "{query}"
**ผลลัพธ์:**
"""
        try:
            api_key = self.groq_key_manager.get_key()
            if not api_key:
                raise Exception("No available Groq API keys.")

            client = Groq(api_key=api_key)
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model_name,
                temperature=0.1
            )
            search_term = chat_completion.choices[0].message.content.strip().replace('"', '')
            
            if not search_term:
                print("  - ⚠️ LLM returned an empty search term.")
                return None

            print(f"  - ✅ Translated search term: '{search_term}'")
            return search_term
        except Exception as e:
            print(f"  - ⚠️ Keyword extraction for image search failed: {e}")
            return None

    def _search(self, term: str) -> Optional[Dict]:
        """
        ฟังก์ชันย่อยสำหรับค้นหารูปภาพและจัดรูปแบบผลลัพธ์
        """
        if not self.unsplash_key:
            print("❌ [Image Agent] Error: UNSPLASH_ACCESS_KEY is not configured.")
            return None

        params = {
            'query': term,
            'per_page': 1,
            'orientation': 'landscape',
            'lang': 'en'
        }
        headers = {'Authorization': f'Client-ID {self.unsplash_key}'}

        try:
            print(f"🖼️  [Image Agent] Searching for '{term}' on Unsplash...")
            response = requests.get(self.api_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            if results := data.get('results'):
                first_image = results[0]
                image_info = {
                    "url": first_image['urls']['regular'],
                    "description": first_image.get('alt_description', 'No description available.'),
                    "photographer": first_image['user']['name'],
                    "profile_url": first_image['user']['links']['html']
                }
                print(f"✅ [Image Agent] Found image by {image_info['photographer']}")
                return image_info
            else:
                print(f"🟡 [Image Agent] No results found for '{term}'.")
                return None

        except requests.exceptions.RequestException as e:
            print(f"❌ [Image Agent] Error connecting to Unsplash API: {e}")
            return None
        except Exception as e:
            print(f"❌ [Image Agent] An unexpected error occurred: {e}")
            return None

    def handle(self, query: str) -> Optional[Dict]:
        """
        เมธอดหลักที่ Dispatcher จะเรียกใช้
        """
        image_keywords = ["หารูป", "ขอดูรูป", "หาภาพ", "รูปภาพของ", "ภาพของ"]
        if not any(keyword in query.lower() for keyword in image_keywords):
            return None
        search_term = self._extract_and_translate_search_term(query)
        
        if search_term:
            return self._search(search_term)
        
        return None
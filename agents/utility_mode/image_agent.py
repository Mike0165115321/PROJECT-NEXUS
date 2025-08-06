# agents/utility_mode/image_agent.py
# (V2 - Standardized & Production-Ready)

import requests
import re
from typing import Optional, Dict

class ImageAgent:
    """
    Agent ที่เชี่ยวชาญด้านการค้นหารูปภาพจาก Unsplash
    ทำงานแบบ Rule-based โดยเรียกใช้ API ภายนอก
    """
    def __init__(self, unsplash_key: str):
        """
        เริ่มต้นการทำงานโดยรับ Unsplash Access Key เข้ามา
        """
        self.api_key = unsplash_key
        self.api_url = "https://api.unsplash.com/search/photos"
        print("🖼️  Image Agent (V2 - API-Driven) is ready.")

    def _search(self, term: str) -> Optional[Dict]:
        """
        ฟังก์ชันย่อยสำหรับค้นหารูปภาพและจัดรูปแบบผลลัพธ์
        """
        if not self.api_key:
            print("❌ [Image Agent] Error: UNSPLASH_ACCESS_KEY is not configured.")
            return None

        params = {
            'query': term,
            'per_page': 1,
            'orientation': 'landscape',
            'lang': 'en' # ค้นหาด้วยภาษาอังกฤษเพื่อผลลัพธ์ที่ดีที่สุด
        }
        headers = {'Authorization': f'Client-ID {self.api_key}'}

        try:
            print(f"🖼️  [Image Agent] Searching for '{term}' on Unsplash...")
            response = requests.get(self.api_url, headers=headers, params=params, timeout=10)
            response.raise_for_status() # ตรวจสอบ HTTP Error (4xx or 5xx)

            data = response.json()
            if results := data.get('results'): # ใช้ Walrus operator (:=) เพื่อความกระชับ
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
        ตรวจสอบว่าผู้ใช้ต้องการค้นหารูปภาพหรือไม่
        """
        # ⭐️ ใช้ List ของ Keywords เพื่อความยืดหยุ่น ⭐️
        image_keywords = ["หารูป", "ขอดูรูป", "หาภาพ", "รูปภาพของ", "ภาพของ"]
        
        # ใช้ loop เพื่อหา keyword ที่ตรงและดึง search term ออกมา
        for keyword in image_keywords:
            # ใช้ re.IGNORECASE เพื่อให้ไม่สนตัวพิมพ์เล็ก/ใหญ่
            match = re.search(rf"{keyword}\s+(.+)", query, re.IGNORECASE)
            if match:
                search_term = match.group(1).strip()
                return self._search(search_term)
        
        # ถ้าไม่ใช่คำสั่งหารูป ให้คืนค่า None
        return None
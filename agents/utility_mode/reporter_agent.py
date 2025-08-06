# agents/utility_mode/reporter_agent.py
# (V2 - Enhanced Keyword Matching)

import datetime
from typing import Optional

class ReporterAgent:
    """
    Agent ที่เชี่ยวชาญด้านการบอกข้อมูลวันและเวลาปัจจุบัน
    ทำงานแบบ Rule-based เพื่อความเร็วสูงสุด
    """
    def __init__(self):
        self.thai_months = [
            "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", 
            "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
        ]
        self.day_of_week_thai = [
            "วันจันทร์", "วันอังคาร", "วันพุธ", "วันพฤหัสบดี", "วันศุกร์", "วันเสาร์", "วันอาทิตย์"
        ]
        print("📊 Reporter Agent (V2 - Rule-Based) is on duty.")

    def _get_daily_context(self) -> dict:
        now = datetime.datetime.now()
        return {
            "full_date_str": f"วันที่ {now.day} {self.thai_months[now.month - 1]} พ.ศ. {now.year + 543}",
            "current_time": now.strftime("%H:%M"),
            "day_of_week_thai": self.day_of_week_thai[now.weekday()],
        }

    def handle(self, query: str) -> Optional[str]:
        """
        เมธอดหลักที่จะตรวจสอบ query และตอบกลับเกี่ยวกับวัน/เวลา
        """
        daily_context = self._get_daily_context()
        q_lower = query.lower().strip()

        # ⭐️ ใช้ List ของ Keywords เพื่อการจับคู่ที่ครอบคลุมขึ้น ⭐️
        time_keywords = ["กี่โมง", "เวลาอะไร", "เวลาเท่าไหร่", "ตอนนี้เวลากี่โมง"]
        if any(keyword in q_lower for keyword in time_keywords):
            return f"ตอนนี้เวลา {daily_context['current_time']} น. ครับ"

        # ⭐️ ใช้ List ของ Keywords เพื่อการจับคู่ที่ครอบคลุมขึ้น ⭐️
        date_keywords = ["วันนี้วันอะไร", "วันที่เท่าไหร่", "วันนี้วันที่"]
        if any(keyword in q_lower for keyword in date_keywords):
            day_of_week = daily_context['day_of_week_thai']
            full_date_str = daily_context['full_date_str']
            
            return f"วันนี้คือ{day_of_week} ตรงกับ{full_date_str}ครับ"
        
        # ถ้าไม่เข้าเงื่อนไขใดๆ เลย ให้คืนค่า None
        return None
    

    
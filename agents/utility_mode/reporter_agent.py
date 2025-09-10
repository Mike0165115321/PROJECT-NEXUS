# agents/utility_mode/reporter_agent.py
# (V3 - The Context-Aware Chronicler)

import datetime
from typing import Optional

class ReporterAgent:
    """
    Agent ที่เชี่ยวชาญด้านการบอกข้อมูลวันและเวลาปัจจุบัน
    (V3: เพิ่มความสามารถในการรับรู้วันสำคัญ)
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
        
        # <<< [UPGRADE] พจนานุกรมเก็บวันสำคัญ (Key: (เดือน, วัน))
        self.IMPORTANT_DAYS = {
            (1, 1): "วันขึ้นปีใหม่",
            (4, 6): "วันจักรี",
            (4, 13): "วันสงกรานต์",
            (4, 14): "วันสงกรานต์",
            (4, 15): "วันสงกรานต์",
            (5, 4): "วันฉัตรมงคล",
            (6, 3): "วันเฉลิมพระชนมพรรษา สมเด็จพระนางเจ้าสุทิดาฯ",
            (7, 28): "วันเฉลิมพระชนมพรรษา พระบาทสมเด็จพระวชิรเกล้าเจ้าอยู่หัว",
            (8, 12): "วันแม่แห่งชาติ",
            (10, 13): "วันคล้ายวันสวรรคต พระบาทสมเด็จพระบรมชนกาธิเบศร มหาภูมิพลอดุลยเดชมหาราช บรมนาถบพิตร (วันนวมินทรมหาราช)",
            (10, 23): "วันปิยมหาราช",
            (12, 5): "วันพ่อแห่งชาติ",
            (12, 10): "วันรัฐธรรมนูญ",
            (12, 31): "วันสิ้นปี"
        }
        print("📊 Reporter Agent (V3 - Context-Aware) is on duty.")

    def _get_daily_context(self) -> dict:
        now = datetime.datetime.now()
        
        today_key = (now.month, now.day)
        important_day_info = self.IMPORTANT_DAYS.get(today_key)

        return {
            "full_date_str": f"วันที่ {now.day} {self.thai_months[now.month - 1]} พ.ศ. {now.year + 543}",
            "current_time": now.strftime("%H:%M"),
            "day_of_week_thai": self.day_of_week_thai[now.weekday()],
            "important_day_info": important_day_info 
        }

    def handle(self, query: str) -> Optional[str]:
        """
        เมธอดหลักที่จะตรวจสอบ query และตอบกลับเกี่ยวกับวัน/เวลา
        """
        daily_context = self._get_daily_context()
        q_lower = query.lower().strip()

        time_keywords = ["กี่โมง", "เวลาอะไร", "เวลาเท่าไหร่", "ตอนนี้เวลากี่โมง"]
        if any(keyword in q_lower for keyword in time_keywords):
            return f"ตอนนี้เวลา {daily_context['current_time']} น. ครับ"

        date_keywords = ["วันนี้วันอะไร", "วันที่เท่าไหร่", "วันนี้วันที่"]
        if any(keyword in q_lower for keyword in date_keywords):
            day_of_week = daily_context['day_of_week_thai']
            full_date_str = daily_context['full_date_str']
            important_day = daily_context.get('important_day_info')

            if important_day:
                return f"วันนี้คือ{day_of_week} ตรงกับ{full_date_str} และยังเป็นวัน{important_day}ที่สำคัญอีกด้วยครับ"
            else:
                return f"วันนี้คือ{day_of_week} ตรงกับ{full_date_str}ครับ"
        
        return None
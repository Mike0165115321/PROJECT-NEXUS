# agents/utility_mode/system_agent.py
# (V3 - Linux Specialist)

import pyperclip
import os
import subprocess
import platform
import webbrowser
import re
from typing import Optional

class SystemAgent:
    """
    Agent ที่จัดการการทำงานกับระบบปฏิบัติการ (ปรับจูนสำหรับ Linux/WSL)
    """
    def __init__(self):
        self.current_os = platform.system().lower()
        print(f"⚙️  System Agent (V3 - Linux Specialist) is operational on {self.current_os}.")

    def _read_clipboard(self) -> str:
        try:
            content = pyperclip.paste()
            return f"ข้อความในคลิปบอร์ดคือ:\n---\n{content}\n---" if content else "ในคลิปบอร์ดไม่มีข้อความอยู่ครับ"
        except Exception as e:
            return f"ขออภัยครับ เกิดข้อผิดพลาดในการอ่านคลิปบอร์ด: {e}"

    def _write_to_clipboard(self, text: str) -> str:
        try:
            pyperclip.copy(text)
            return "เรียบร้อยครับ! ข้อความถูกคัดลอกไปยังคลิปบอร์ดแล้ว"
        except Exception as e:
            return f"ขออภัยครับ เกิดข้อผิดพลาดในการเขียนลงคลิปบอร์ด: {e}"
    
    def _open_application(self, app_name: str) -> str:
        app_name_lower = app_name.lower().strip()
        
        thai_to_eng_app = {
            'เครื่องคิดเลข': 'calculator', 
            'เท็กซ์เอดิเตอร์': 'text_editor',
            'โน้ตแพด': 'text_editor',
            'โครม': 'chrome',
            'เบราว์เซอร์': 'browser',
            'วีเอสโค้ด': 'vscode',
            'สปอติฟาย': 'spotify',
            'เทอร์มินัล': 'terminal',
            'ไฟล์': 'file_manager'
        }
        
        app_map = {
            'text_editor': 'gedit',
            'calculator': 'gnome-calculator',
            'browser': 'google-chrome-stable',
            'chrome': 'google-chrome-stable',
            'vscode': 'code',
            'spotify': 'spotify',
            'terminal': 'gnome-terminal',
            'file_manager': 'nautilus'
        }
        
        app_key = thai_to_eng_app.get(app_name_lower, app_name_lower)
        command = app_map.get(app_key)
        is_wsl = 'microsoft' in platform.uname().release.lower()
        
        if app_key == 'file_manager' and is_wsl:
            command = 'explorer.exe .'
            print("  - [System Agent] WSL detected. Using 'explorer.exe .' for file manager.")
        
        if not command: 
            return f"ขออภัยครับ ผมไม่รู้จักวิธีเปิด '{app_name}' บน Linux"
        try:
            subprocess.Popen(command, shell=True)
            return f"กำลังเปิด {app_name} ให้ครับ..."
        except FileNotFoundError:
            return f"ขออภัยครับ ดูเหมือนว่าโปรแกรม '{command}' จะยังไม่ได้ติดตั้งบนระบบของคุณ"
        except Exception as e:
            return f"ขออภัยครับ เกิดข้อผิดพลาดขณะพยายามเปิด {app_name}: {e}"

    def _open_website(self, site_name: str) -> str:
        site_map = {
            'youtube': 'https://www.youtube.com', 'facebook': 'https://www.facebook.com',
            'google': 'https://www.google.com', 'gmail': 'https://mail.google.com',
            'github': 'https://www.github.com'
        }
        url = site_map.get(site_name.lower().strip())
        if not url: return f"ขออภัยครับ ผมไม่รู้จักเว็บไซต์ '{site_name}'"
        try:
            webbrowser.open_new_tab(url)
            return f"กำลังเปิด {site_name.capitalize()} ให้ในเบราว์เซอร์ครับ"
        except Exception as e:
            return f"ขออภัยครับ เกิดข้อผิดพลาดขณะพยายามเปิด {site_name}: {e}"

    def _set_system_volume(self, level: int) -> str:
        if not 0 <= level <= 100: return "โปรดระบุระดับเสียงระหว่าง 0 ถึง 100 ครับ"
        try:
            subprocess.run(['amixer', '-D', 'pulse', 'sset', 'Master', f'{level}%'], check=True)
            return f"ปรับระดับเสียงเป็น {level}% แล้วครับ"
        except subprocess.CalledProcessError:
            return "ขออภัยครับ ไม่สามารถปรับระดับเสียงได้ อาจจะไม่มี PulseAudio ติดตั้งอยู่"
        except Exception as e:
            return f"ขออภัยครับ เกิดข้อผิดพลาดขณะพยายามปรับระดับเสียง: {e}"

    def _get_current_volume(self) -> Optional[int]:
        try:
            result = subprocess.run(['amixer', '-D', 'pulse', 'sget', 'Master'], capture_output=True, text=True, check=True)
            match = re.search(r"\[(\d{1,3})%\]", result.stdout)
            if match: return int(match.group(1))
            return None
        except Exception: 
            return None

    def _change_volume(self, direction: str, amount: int = 10) -> str:
        current_level = self._get_current_volume()
        if current_level is None: return "ขออภัยครับ ผมไม่สามารถตรวจสอบระดับเสียงปัจจุบันได้"
        
        new_level = min(current_level + amount, 100) if direction == "increase" else max(current_level - amount, 0)
        return self._set_system_volume(new_level)

    def handle(self, query: str) -> Optional[str]:
        """
        ตรวจสอบ query กับชุดกฎ (Rules) ที่กำหนดไว้
        ถ้าตรงเงื่อนไข จะเรียกใช้ฟังก์ชันที่เกี่ยวข้องและคืนค่าผลลัพธ์
        """
        q_lower = query.lower().strip()

        set_volume_match = re.search(r"(ปรับ|ตั้งค่า)\s*เสียง\s*(?:เป็น|ไปที่)?\s*(\d{1,3})", q_lower)
        if set_volume_match:
            return self._set_system_volume(int(set_volume_match.group(2)))
        if any(keyword in q_lower for keyword in ["เพิ่มเสียง", "ดังขึ้น"]):
            return self._change_volume("increase")
        if any(keyword in q_lower for keyword in ["ลดเสียง", "เบาลง"]):
            return self._change_volume("decrease")

        open_app_match = re.search(r"เปิด(?:โปรแกรม|แอป)?\s*(.+)", q_lower)
        if open_app_match:
            entity_name = open_app_match.group(1).replace("ให้หน่อย", "").replace("หน่อย", "").strip()
            
            if entity_name in ['youtube', 'facebook', 'google', 'gmail', 'github']:
                return self._open_website(entity_name)
            else:
                return self._open_application(entity_name)
    
        open_site_match = re.search(r"เปิดเว็บ\s+(.+)", q_lower)
        if open_site_match:
            return self._open_website(open_site_match.group(1))

        write_clip_match = re.search(r"(คัดลอก|copy)\s*(?:ข้อความ)?\s*['\"](.+)['\"]", query, re.IGNORECASE)
        if write_clip_match:
            return self._write_to_clipboard(write_clip_match.group(2))
        if any(keyword in q_lower for keyword in ["อ่านคลิปบอร์ด", "ในคลิปบอร์ดมีอะไร"]):
            return self._read_clipboard()

        return None
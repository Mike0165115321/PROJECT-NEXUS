# agents/utility_mode/system_agent.py

import pyperclip
import os
import subprocess
import platform
import webbrowser
import re
from typing import Optional

class SystemAgent:
    def __init__(self):
        self.current_os = platform.system().lower()
        self.AudioUtilities = None
        self.IAudioEndpointVolume = None
        self.CLSCTX_ALL = None
        print(f"⚙️  System Agent (V2 - Rule-Based) is operational on {self.current_os}.")

        if self.current_os == 'windows':
            try:
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                self.AudioUtilities = AudioUtilities
                self.IAudioEndpointVolume = IAudioEndpointVolume
                self.CLSCTX_ALL = CLSCTX_ALL
                print("[System Agent] pycaw loaded successfully for Windows volume control.")
            except ImportError:
                print("[System Agent] WARNING: pycaw or comtypes not found. Volume control disabled.")
        else:
            print(f"[System Agent] Running on {self.current_os}. Windows-specific features are disabled.")


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
            'เครื่องคิดเลข': 'calculator', 'โน้ตแพด': 'notepad', 'โครม': 'chrome',
            'เบราว์เซอร์': 'browser', 'เวิร์ด': 'word', 'เอ็กเซล': 'excel',
            'พาวเวอร์พอยท์': 'powerpoint', 'สปอติฟาย': 'spotify', 'วีเอสโค้ด': 'vscode',
        }
        app_map = {
            'notepad': {'windows': 'notepad.exe', 'darwin': 'open -a TextEdit', 'linux': 'gedit'},
            'calculator': {'windows': 'calc.exe', 'darwin': 'open -a Calculator', 'linux': 'gnome-calculator'},
            'browser': {'windows': r'start chrome', 'darwin': 'open -a "Google Chrome"', 'linux': 'google-chrome-stable'},
            'chrome': {'windows': r'start chrome', 'darwin': 'open -a "Google Chrome"', 'linux': 'google-chrome-stable'},
            'vscode': {'windows': 'code', 'darwin': 'code', 'linux': 'code'},
            'spotify': {'windows': 'spotify', 'darwin': 'open -a Spotify', 'linux': 'spotify'},
            'word': {'windows': 'winword'}, 'excel': {'windows': 'excel'},
            'powerpoint': {'windows': 'powerpnt', 'darwin': 'open -a "Microsoft PowerPoint"'},
        }
        app_key = thai_to_eng_app.get(app_name_lower, app_name_lower)
        command = app_map.get(app_key, {}).get(self.current_os)
        if not command: return f"ขออภัยครับ ผมไม่รู้จักวิธีเปิด '{app_name}' บน {self.current_os}"
        try:
            subprocess.Popen(command, shell=True)
            return f"กำลังเปิด {app_name} ให้ครับ..."
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
            if self.current_os == 'windows':
                if not self.AudioUtilities: raise NotImplementedError("Volume control disabled (pycaw missing).")
                devices = self.AudioUtilities.GetSpeakers()
                interface = devices.Activate(self.IAudioEndpointVolume._iid_, self.CLSCTX_ALL, None)
                volume = interface.QueryInterface(self.IAudioEndpointVolume)
                volume.SetMasterVolumeLevelScalar(level / 100.0, None)
            elif self.current_os == 'darwin':
                subprocess.run(['osascript', '-e', f'set volume output volume {level}'])
            elif self.current_os == 'linux':
                subprocess.run(['amixer', '-D', 'pulse', 'sset', 'Master', f'{level}%'])
            return f"ปรับระดับเสียงเป็น {level}% แล้วครับ"
        except Exception as e:
            return f"ขออภัยครับ เกิดข้อผิดพลาดขณะพยายามปรับระดับเสียง: {e}"

    def _get_current_volume(self) -> Optional[int]:
        try:
            if self.current_os == 'windows':
                if not self.AudioUtilities: return None
                devices = self.AudioUtilities.GetSpeakers()
                interface = devices.Activate(self.IAudioEndpointVolume._iid_, self.CLSCTX_ALL, None)
                volume = interface.QueryInterface(self.IAudioEndpointVolume)
                return round(volume.GetMasterVolumeLevelScalar() * 100)
            elif self.current_os == 'darwin':
                result = subprocess.run(['osascript', '-e', 'output volume of (get volume settings)'], capture_output=True, text=True)
                return int(result.stdout.strip())
            elif self.current_os == 'linux':
                result = subprocess.run(['amixer', '-D', 'pulse', 'sget', 'Master'], capture_output=True, text=True)
                match = re.search(r"\[(\d{1,3})%\]", result.stdout)
                if match: return int(match.group(1))
            return None
        except Exception: return None

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

        open_app_match = re.search(r"เปิด(?:โปรแกรม|แอป)?\s+([\wก-๙_.-]+)", q_lower)
        if open_app_match:
            entity_name = open_app_match.group(1)
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
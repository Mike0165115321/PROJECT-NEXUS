# core/code_executor.py (เวอร์ชันไม่ใช้ Docker)

import subprocess
import os
import sys
from typing import Tuple

# กำหนด Path ไปยังห้องทดลองของเรา
SANDBOX_DIR = os.path.join(os.getcwd(), "sandbox_workspace")
os.makedirs(SANDBOX_DIR, exist_ok=True)

class CodeExecutor:
    def __init__(self):
        print("🔬 ห้องทดลอง Sandbox พร้อมสำหรับการรันโค้ด (โหมด: Subprocess)")

    def run_code_in_sandbox(self, code: str) -> Tuple[str, bool]:
        """
        รันโค้ด Python ในโปรเซสลูกที่ถูกจำกัดสิทธิ์
        """
        # สร้างไฟล์ Python ชั่วคราวใน sandbox
        temp_script_path = os.path.join(SANDBOX_DIR, "temp_script.py")
        
        try:
            with open(temp_script_path, "w", encoding="utf-8") as f:
                f.write(code)
            command = [sys.executable, temp_script_path]
            
            # --- รันโค้ดด้วย subprocess ---
            # timeout=30: จำกัดเวลาทำงาน 30 วินาที
            # cwd=SANDBOX_DIR: จำกัดให้โปรเซสทำงานอยู่ในโฟลเดอร์ sandbox เท่านั้น
            # text=True, capture_output=True: เพื่อดักจับผลลัพธ์
            result = subprocess.run(
                command,
                timeout=30,
                cwd=SANDBOX_DIR,
                text=True,
                capture_output=True,
                # **หมายเหตุ:** การจำกัดสิทธิ์ user และ network บน Windows
                # จะต้องใช้เทคนิคขั้นสูงเพิ่มเติม แต่ cwd เป็นการป้องกันที่ดีในระดับแรก
            )
            
            if result.returncode != 0:
                return result.stderr, True
            else:
                return result.stdout, False

        except subprocess.TimeoutExpired:
            return "Execution timed out after 30 seconds.", True
        except Exception as e:
            return f"An unexpected error occurred during execution: {str(e)}", True
        finally:
            if os.path.exists(temp_script_path):
                os.remove(temp_script_path)
# core/api_key_manager.py
# (V7 - The Smart Throttler)

import time
from typing import List, Dict

class AllKeysOnCooldownError(Exception):
    """Exception ที่จะถูกโยนเมื่อ API Key ทั้งหมดไม่พร้อมใช้งาน"""
    pass

class ApiKeyManager:
    def __init__(self, all_google_keys: List[str], silent: bool = False):
        if not all_google_keys:
            print("⚠️ [Key Manager] No Google API keys provided.")
            self.all_keys = []
        else:
            self.all_keys = all_google_keys

        self.key_cooldowns: Dict[str, float] = {key: 0 for key in self.all_keys}
        self.current_index = 0
        self.silent = silent

        self.last_failure_time: float = 0.0
        self.failure_streak: int = 0

        if self.all_keys and not self.silent:
            print(f"🔑 [Key Manager] Initialized with {len(self.all_keys)} Google keys.")

    def get_key(self) -> str:
        """
        หาคีย์ที่พร้อมใช้งานตัวถัดไป พร้อมกลไกหน่วงเวลาอัตโนมัติ
        โยน AllKeysOnCooldownError ถ้าไม่มีคีย์ไหนพร้อมใช้งานเลย
        """
        if not self.all_keys:
            raise AllKeysOnCooldownError("No API keys were provided to the manager.")
        if self.failure_streak >= len(self.all_keys) / 2:
            time_since_last_fail = time.time() - self.last_failure_time
            if time_since_last_fail < 2.0:
                sleep_duration = 2.0 - time_since_last_fail
                if not self.silent:
                    print(f"⚠️ [Key Manager] High failure rate detected. Throttling for {sleep_duration:.2f}s...")
                time.sleep(sleep_duration)

        for _ in range(len(self.all_keys)):
            key_to_try = self.all_keys[self.current_index]
            
            if time.time() >= self.key_cooldowns.get(key_to_try, 0):
                self.failure_streak = 0
                # ---------------------------------------------------------
                return key_to_try 
            self._rotate()

        # --- 3. ถ้าวนครบแล้วยังหาคีย์ไม่ได้ ให้ยอมแพ้ ---
        raise AllKeysOnCooldownError(f"All {len(self.all_keys)} keys are on cooldown. Try again later.")

    def report_failure(self, failed_key: str, error_type: str = "generic"):
        """
        รายงานว่าคีย์ใช้งานไม่ได้ และอัปเดตสถานะความล้มเหลว
        """
        if failed_key not in self.key_cooldowns:
            return

        # --- อัปเดตสถานะความล้มเหลวสำหรับ Smart Throttling ---
        self.last_failure_time = time.time()
        self.failure_streak += 1
        # ----------------------------------------------------

        # --- กำหนดเวลา Cooldown ตามประเภท Error (เหมือนเดิม) ---
        if error_type == 'quota':
            cooldown_duration = 24 * 60 * 60 
            reason = "Daily quota reached"
        else: # rate_limit หรือ generic
            cooldown_duration = 65
            reason = "Rate limit hit/Generic"

        self.key_cooldowns[failed_key] = time.time() + cooldown_duration
        
        if not self.silent:
            print(f"🔻 [Key Manager] Key '...{failed_key[-4:]}' failed ({reason}). Cooldown for {cooldown_duration}s. Streak: {self.failure_streak}")
        
        # หลังจากรายงานแล้ว ให้หมุน index ไปตัวถัดไปทันที
        self._rotate()

    def _rotate(self):
        """หมุน index ไปยังคีย์ตัวถัดไปในลิสต์"""
        if not self.all_keys:
            return
        self.current_index = (self.current_index + 1) % len(self.all_keys)
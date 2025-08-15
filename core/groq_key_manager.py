# core/groq_key_manager.py
# (V4 - The Smart Throttler)

import time
from typing import List, Dict

class AllGroqKeysOnCooldownError(Exception):
    """Exception ที่จะถูกโยนเมื่อ Groq API Key ทั้งหมดไม่พร้อมใช้งาน"""
    pass

class GroqApiKeyManager:
    def __init__(self, all_groq_keys: List[str], silent: bool = False):
        if not all_groq_keys:
            print("⚠️ [Groq Key Manager] No Groq API keys provided.")
            self.all_keys = []
        else:
            self.all_keys = all_groq_keys

        self.key_cooldowns: Dict[str, float] = {key: 0 for key in self.all_keys}
        self.current_index = 0
        self.silent = silent

        self.last_failure_time: float = 0.0
        self.failure_streak: int = 0
        # -----------------------------------------

        if self.all_keys and not self.silent:
            print(f"🔑 [Groq Key Manager] Initialized with {len(self.all_keys)} Groq keys.")

    def get_key(self) -> str:
        """
        หาคีย์ที่พร้อมใช้งานตัวถัดไป พร้อมกลไกหน่วงเวลาอัตโนมัติ
        โยน AllGroqKeysOnCooldownError ถ้าไม่มีคีย์ไหนพร้อมใช้งานเลย
        """
        if not self.all_keys:
            raise AllGroqKeysOnCooldownError("No Groq API keys were provided to the manager.")

        if self.failure_streak >= len(self.all_keys) / 2:
            time_since_last_fail = time.time() - self.last_failure_time
            if time_since_last_fail < 1.5:
                sleep_duration = 1.5 - time_since_last_fail
                if not self.silent:
                    print(f"⚠️ [Groq Key Manager] High failure rate detected. Throttling for {sleep_duration:.2f}s...")
                time.sleep(sleep_duration)
        # ----------------------------------------------------

        for _ in range(len(self.all_keys)):
            key_to_try = self.all_keys[self.current_index]
            
            if time.time() >= self.key_cooldowns.get(key_to_try, 0):
                self.failure_streak = 0
                return key_to_try
            
            self._rotate()

        raise AllGroqKeysOnCooldownError(f"All {len(self.all_keys)} Groq keys are on cooldown. Try again later.")

    def report_failure(self, failed_key: str, error_type: str = "rate_limit"):
        """
        รายงานว่าคีย์ใช้งานไม่ได้ และอัปเดตสถานะความล้มเหลว
        """
        if failed_key not in self.key_cooldowns:
            return


        self.last_failure_time = time.time()
        self.failure_streak += 1

        if error_type == 'invalid_key':
            cooldown_duration = 365 * 24 * 60 * 60
            reason = "Invalid API Key"
        elif error_type == 'server_error':
            cooldown_duration = 120
            reason = "Server error"
        else:
            cooldown_duration = 65
            reason = "Rate limit hit"

        self.key_cooldowns[failed_key] = time.time() + cooldown_duration
        
        if not self.silent:
            print(f"🔻 [Groq Key Manager] Key '...{failed_key[-4:]}' failed ({reason}). Cooldown for {cooldown_duration}s. Streak: {self.failure_streak}")
        
        self._rotate()

    def _rotate(self):
        """หมุน index ไปยังคีย์ตัวถัดไปในลิสต์"""
        if not self.all_keys:
            return
        self.current_index = (self.current_index + 1) % len(self.all_keys)

    def get_active_key_count(self) -> int:
        """คืนค่าจำนวนคีย์ที่พร้อมใช้งานในขณะนี้"""
        now = time.time()
        return sum(1 for key in self.all_keys if now >= self.key_cooldowns.get(key, 0))
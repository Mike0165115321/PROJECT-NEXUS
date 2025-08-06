# core/api_key_manager.py
# (V4 - Circuit Breaker Edition)

import time
from typing import List, Dict, Optional

class AllKeysOnCooldownError(Exception):
    """Exception ที่จะถูกโยนเมื่อ API Key ทั้งหมดไม่พร้อมใช้งานหลังจากพยายามหลายครั้ง"""
    pass

class ApiKeyManager:
    def __init__(self, all_google_keys: List[str], silent: bool = False):
        self.all_keys = all_google_keys
        self.key_cooldowns: Dict[str, float] = {key: 0 for key in all_google_keys}
        self.current_index = 0
        self.silent = silent

        if not self.all_keys:
            print("⚠️ [Key Manager] No Google API keys provided.")
        elif not self.silent:
            print(f"🔑 [Key Manager] Initialized with {len(self.all_keys)} Google keys.")

    def get_key(self, max_retries: int = 3) -> str:
        """
        ค้นหากุญแจที่พร้อมใช้งาน ถ้าไม่มี จะรอและลองใหม่ตามจำนวน max_retries
        ถ้าลองจนครบแล้วยังไม่มี จะโยน AllKeysOnCooldownError
        """
        if not self.all_keys:
            raise AllKeysOnCooldownError("No API keys were provided to the manager.")
        
        retries = 0
        while retries < max_retries:
            # ตรวจสอบคีย์ทั้งหมดในหนึ่งรอบ
            for _ in range(len(self.all_keys)):
                key_to_try = self.all_keys[self.current_index]
                cooldown_until = self.key_cooldowns.get(key_to_try, 0)
                
                if time.time() >= cooldown_until:
                    return key_to_try
                
                self._rotate()

            retries += 1
            if not self.silent:
                print(f"🔄 [Key Manager] All keys on cooldown. Retry attempt {retries}/{max_retries}.")

            try:
                soonest_available_time = min(t for t in self.key_cooldowns.values() if t > 0)
                wait_time = max(0, soonest_available_time - time.time()) + 1
            except ValueError:
                wait_time = 60

            if not self.silent:
                print(f"⏳ [Key Manager] Waiting for {wait_time:.1f} seconds...")
            
            time.sleep(wait_time)

        raise AllKeysOnCooldownError(f"All keys are still on cooldown after {max_retries} retries.")

    def report_failure(self, failed_key: str):
        if failed_key not in self.all_keys:
            return
        
        cooldown_duration = 61
        self.key_cooldowns[failed_key] = time.time() + cooldown_duration
        
        if not self.silent:
            print(f"🔻 [Key Manager] Key '...{failed_key[-4:]}' hit rate limit. Cooldown for {cooldown_duration}s.")
        
        self._rotate()

    def _rotate(self):
        if not self.all_keys:
            return
        self.current_index = (self.current_index + 1) % len(self.all_keys)
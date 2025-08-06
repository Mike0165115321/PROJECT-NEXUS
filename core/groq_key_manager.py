# core/groq_key_manager.py
# (V1 - Based on the battle-tested V4 Manager)

import time
from typing import List, Dict

class AllGroqKeysOnCooldownError(Exception):
    """Exception ที่จะถูกโยนเมื่อ Groq API Key ทั้งหมดไม่พร้อมใช้งาน"""
    pass

class GroqApiKeyManager:
    def __init__(self, all_groq_keys: List[str], silent: bool = False):
        self.all_keys = all_groq_keys
        self.key_cooldowns: Dict[str, float] = {key: 0 for key in all_groq_keys}
        self.current_index = 0
        self.silent = silent

        if not self.all_keys:
            print("⚠️ [Groq Key Manager] No Groq API keys provided.")
        elif not self.silent:
            print(f"🔑 [Groq Key Manager] Initialized with {len(self.all_keys)} Groq keys.")

    def get_key(self, max_retries: int = 3) -> str:
        if not self.all_keys:
            raise AllGroqKeysOnCooldownError("No Groq API keys were provided.")
        
        retries = 0
        while retries < max_retries:
            for _ in range(len(self.all_keys)):
                key_to_try = self.all_keys[self.current_index]
                cooldown_until = self.key_cooldowns.get(key_to_try, 0)
                
                if time.time() >= cooldown_until:
                    return key_to_try
                
                self._rotate()

            retries += 1
            if not self.silent:
                print(f"🔄 [Groq Key Manager] All keys on cooldown. Retry attempt {retries}/{max_retries}.")

            try:
                soonest_available_time = min(t for t in self.key_cooldowns.values() if t > 0)
                wait_time = max(0, soonest_available_time - time.time()) + 1
            except ValueError:
                wait_time = 60

            if not self.silent:
                print(f"⏳ [Groq Key Manager] Waiting for {wait_time:.1f} seconds...")
            
            time.sleep(wait_time)

        raise AllGroqKeysOnCooldownError(f"All Groq keys are still on cooldown after {max_retries} retries.")

    def report_failure(self, failed_key: str):
        if failed_key not in self.all_keys:
            return
        
        # Groq Rate Limit รีเซ็ตทุกนาที การพัก 61 วินาทีจึงปลอดภัย
        cooldown_duration = 61
        self.key_cooldowns[failed_key] = time.time() + cooldown_duration
        
        if not self.silent:
            print(f"🔻 [Groq Key Manager] Key '...{failed_key[-4:]}' hit rate limit. Cooldown for {cooldown_duration}s.")
        
        self._rotate()

    def _rotate(self):
        if not self.all_keys:
            return
        self.current_index = (self.current_index + 1) % len(self.all_keys)
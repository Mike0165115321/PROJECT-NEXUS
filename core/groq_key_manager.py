# core/groq_key_manager.py

import time
import asyncio  
from typing import List, Dict

class AllGroqKeysOnCooldownError(Exception):
    pass

class GroqApiKeyManager:
    def __init__(self, all_groq_keys: List[str], silent: bool = False):
        if not all_groq_keys:
            print("⚠️ [Groq Manager] No Groq API keys provided.")
            self.all_keys = []
        else:
            self.all_keys = all_groq_keys

        self.key_cooldowns: Dict[str, float] = {key: 0 for key in self.all_keys}
        self.current_index = 0
        self.silent = silent
        self.last_failure_time: float = 0.0
        self.failure_streak: int = 0
        if self.all_keys and not self.silent:
            print(f"🔑 [Groq Manager] Initialized with {len(self.all_keys)} Groq keys (Async Ready).")

    async def get_key(self) -> str:
        if not self.all_keys:
            raise AllGroqKeysOnCooldownError("No Groq API keys were provided.")
        
        if self.failure_streak >= len(self.all_keys) / 2:
            time_since_last_fail = time.time() - self.last_failure_time
            if time_since_last_fail < 2.0:
                sleep_duration = 2.0 - time_since_last_fail
                if not self.silent:
                    print(f"⚠️ [Groq Manager] High failure rate detected. Throttling for {sleep_duration:.2f}s (Async)...")
                
                await asyncio.sleep(sleep_duration)

        for _ in range(len(self.all_keys)):
            key_to_try = self.all_keys[self.current_index]
            if time.time() >= self.key_cooldowns.get(key_to_try, 0):
                self.failure_streak = 0
                return key_to_try 
            self._rotate()
        
        raise AllGroqKeysOnCooldownError(f"All {len(self.all_keys)} Groq keys are on cooldown.")

    def report_failure(self, failed_key: str, error_type: str = "generic"):
        if failed_key not in self.key_cooldowns:
            return
        
        self.last_failure_time = time.time()
        self.failure_streak += 1
        
        cooldown_duration = 35 
        reason = "Rate limit hit/Generic"

        self.key_cooldowns[failed_key] = time.time() + cooldown_duration
        
        if not self.silent:
            print(f"🔻 [Groq Manager] Key '...{failed_key[-4:]}' failed ({reason}). Cooldown for {cooldown_duration}s. Streak: {self.failure_streak}")
        
        self._rotate()

    def _rotate(self):
        if not self.all_keys:
            return
        self.current_index = (self.current_index + 1) % len(self.all_keys)
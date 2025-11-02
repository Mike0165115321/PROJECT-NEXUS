# core/tts_engine.py
# (V49.0 - Robust & Non-Blocking gTTS)

import os
import re
from typing import Optional
from gtts import gTTS
import asyncio 
import time   

class TextToSpeechEngine:
    """
    [V49] ผู้เชี่ยวชาญด้านการสังเคราะห์เสียง (แบบ Async & Robust)
    """
    def __init__(self):
        print("🗣️  Initializing Text-to-Speech Engine (gTTS V49 - Robust)...") 
        self.is_ready = True
        print("✅ Text-to-Speech Engine (gTTS) is ready.")

    def _cleanup_text(self, text: str) -> str:
        text = re.sub(r'[\*#`]', '', text)
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    async def synthesize(self, text: str, output_path: str = "temp_voice.mp3") -> Optional[str]:
        """
        [V33] สังเคราะห์เสียงพูด (แบบ Async) โดยรัน gTTS ในเธรดแยก
        """
        if not self.is_ready or not text:
            return None

        cleaned_text = self._cleanup_text(text)
        if not cleaned_text:
            return None

        print(f"🗣️  [gTTS Engine V49] Synthesizing: '{cleaned_text[:50]}...' (Async)")

        def _blocking_gtts_save():
            """[V49] ฟังก์ชันนี้จะถูกรันในเธรดแยก (พร้อม "ตรวจสอบ" ไฟล์)"""
            try:
                tts = gTTS(text=cleaned_text, lang='th')
                tts.save(output_path)
                
                time.sleep(0.1) 
                
                if os.path.exists(output_path) and os.path.getsize(output_path) > 1024: 
                    print(f" 	- ✅ Audio file created successfully at: {output_path} (Size: {os.path.getsize(output_path)} bytes)")
                    return output_path
                else:
                    print(f" 	- ❌ gTTS Silently Failed. File is 0 bytes or missing.")
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    return None

            except Exception as e:
                print(f" 	- ❌ gTTS Synthesis failed (Exception): {e}")
                return None
        
        return await asyncio.to_thread(_blocking_gtts_save)
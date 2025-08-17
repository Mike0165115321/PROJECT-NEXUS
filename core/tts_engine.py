# core/tts_engine.py
# (V_Final - Switched to the simple and reliable gTTS)

import os
import re
from typing import Optional
from gtts import gTTS

class TextToSpeechEngine:
    """
    ผู้เชี่ยวชาญด้านการสังเคราะห์เสียงโดยใช้ gTTS (Google Text-to-Speech)
    - เรียบง่าย, เสถียร, และไม่ต้องใช้ Dependency ที่ซับซ้อน
    """
    def __init__(self):
        print("🗣️  Initializing Text-to-Speech Engine (gTTS)...")
        # gTTS ไม่ต้องมีการโหลดโมเดลใดๆ พร้อมใช้งานเสมอ
        self.is_ready = True
        print("✅ Text-to-Speech Engine (gTTS) is ready.")

    def _cleanup_text(self, text: str) -> str:
        """
        ทำความสะอาดข้อความก่อนส่งให้ TTS (ยังคงมีประโยชน์)
        """
        text = re.sub(r'[\*#`]', '', text)
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        # ลบ URL ออกไปก่อนส่งให้ gTTS
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def synthesize(self, text: str, output_path: str = "temp_voice.mp3") -> Optional[str]:
        """
        สังเคราะห์เสียงพูดเป็นไฟล์ .mp3 โดยใช้ gTTS
        """
        if not self.is_ready or not text:
            return None

        cleaned_text = self._cleanup_text(text)
        if not cleaned_text:
            return None

        print(f"🗣️  [gTTS Engine] Synthesizing: '{cleaned_text[:50]}...'")

        try:
            # 1. สร้าง Object gTTS โดยระบุข้อความและภาษา (th = ภาษาไทย)
            tts = gTTS(text=cleaned_text, lang='th')
            
            # 2. บันทึกไฟล์เสียงเป็น .mp3
            tts.save(output_path)
            
            print(f"  - ✅ Audio file created successfully at: {output_path}")
            return output_path

        except Exception as e:
            print(f"  - ❌ gTTS Synthesis failed: {e}")
            return None
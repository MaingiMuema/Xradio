import edge_tts
import asyncio
import logging
import io
import random

logger = logging.getLogger(__name__)

class ElevenLabsService:
    def __init__(self):
        self.voices = {
            'main_host': "en-US-ChristopherNeural",
            'news_anchor': "en-GB-SoniaNeural",
            'tech_expert': "en-US-GuyNeural",
            'culture_host': "en-US-JennyNeural"
        }
        self.voice_styles = {
            'main_host': "cheerful",
            'news_anchor': "professional",
            'tech_expert': "enthusiastic",
            'culture_host': "friendly"
        }
        logger.info(f"Edge TTS service initialized with voices: {self.voices}")

    async def generate_speech(self, text, host_type='main_host'):
        try:
            voice = self.voices.get(host_type, self.voices['main_host'])
            style = self.voice_styles.get(host_type, "default")
            
            communicate = edge_tts.Communicate(text, voice)
            if style != "default":
                communicate.rate = "+10%" if style == "enthusiastic" else "+0%"
                communicate.volume = "+20%" if style in ["cheerful", "enthusiastic"] else "+0%"
            
            audio_buffer = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_buffer.write(chunk["data"])
            
            audio_data = audio_buffer.getvalue()
            audio_buffer.close()
            
            return audio_data

        except Exception as e:
            logger.error(f"Error generating speech: {str(e)}")
            return None

    async def list_voices(self):
        voices = await edge_tts.list_voices()
        return [voice for voice in voices if voice["Locale"].startswith("en")]

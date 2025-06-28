import os
import subprocess
import tempfile
import whisper
from typing import Optional
from langchain.chat_models import ChatOpenAI

class SpeechProcessor:
    def __init__(self):
        self.model = whisper.load_model("base")
        self.llm = ChatOpenAI(
            model_name="o3-mini",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
    def record_audio(self, duration: int = 5, output_file: Optional[str] = None) -> str:
        """
        Record audio using ffmpeg
        
        Args:
            duration: Recording duration in seconds
            output_file: Path to save the audio file. If None, creates a temporary file
            
        Returns:
            Path to the recorded audio file
        """
        if output_file is None:
            # Create a temporary file
            temp_dir = tempfile.gettempdir()
            output_file = os.path.join(temp_dir, "recording.wav")
            
        # Use ffmpeg to record audio from default microphone
        command = [
            "ffmpeg",
            "-f", "dshow",  # DirectShow for Windows
            "-i", "audio=virtual-audio-capturer",  # Use virtual audio capturer
            "-t", str(duration),
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            output_file
        ]
        
        try:
            subprocess.run(command, check=True, capture_output=True)
            return output_file
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to record audio: {e.stderr.decode()}")
            
    def transcribe_audio(self, audio_file: str) -> str:
        """
        Transcribe audio file to text using Whisper
        
        Args:
            audio_file: Path to the audio file
            
        Returns:
            Transcribed text
        """
        try:
            result = self.model.transcribe(audio_file)
            return result["text"].strip()
        except Exception as e:
            raise Exception(f"Failed to transcribe audio: {str(e)}")
            
    def process_voice_query(self, duration: int = 5) -> str:
        """
        Record and transcribe voice query
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            Transcribed text
        """
        try:
            # Record audio
            audio_file = self.record_audio(duration)
            
            # Transcribe audio
            text = self.transcribe_audio(audio_file)
            
            # Clean up temporary file
            if os.path.exists(audio_file):
                os.remove(audio_file)
                
            return text
        except Exception as e:
            raise Exception(f"Failed to process voice query: {str(e)}") 
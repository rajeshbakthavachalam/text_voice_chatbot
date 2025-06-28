import speech_recognition as sr
import os
from typing import Optional

class AudioProcessor:
    def __init__(self):
        """Initialize the audio processor"""
        self.recognizer = sr.Recognizer()
        
    def transcribe_audio_file(self, audio_file_path: str) -> str:
        """Transcribe audio from a file"""
        try:
            with sr.AudioFile(audio_file_path) as source:
                audio_data = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio_data)
                return text
        except sr.UnknownValueError:
            raise Exception("Could not understand audio")
        except sr.RequestError as e:
            raise Exception(f"Could not request results; {str(e)}")
        except Exception as e:
            raise Exception(f"Error transcribing audio: {str(e)}")
            
    def transcribe_from_microphone(self) -> Optional[str]:
        """Transcribe audio from microphone"""
        try:
            with sr.Microphone() as source:
                print("Listening...")
                audio = self.recognizer.listen(source)
                print("Processing...")
                text = self.recognizer.recognize_google(audio)
                return text
        except sr.UnknownValueError:
            print("Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"Could not request results; {str(e)}")
            return None
        except Exception as e:
            print(f"Error transcribing audio: {str(e)}")
            return None 
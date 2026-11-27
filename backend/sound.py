import os
import asyncio, tempfile
import numpy as np
import sounddevice as sd
import pygame
from faster_whisper import WhisperModel

from tts import synthesize

stt = WhisperModel("small", device="cpu", compute_type="int8")
SAMPLE_RATE = 16000
pygame.mixer.init()

# listen() stays exactly as it is

def speak(text):
    audio = asyncio.run(synthesize(text))
    if not audio:
        return
    path = os.path.join(tempfile.gettempdir(), "tutor_reply.mp3")
    with open(path, "wb") as f:
        f.write(audio)
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.wait(100)
    pygame.mixer.music.unload()
import os
import asyncio, re, tempfile
import numpy as np
import sounddevice as sd
import edge_tts, pygame
from faster_whisper import WhisperModel

stt = WhisperModel("small", device="cpu", compute_type="int8")
SAMPLE_RATE = 16000
VOICE = "ja-JP-NanamiNeural"
pygame.mixer.init()

def listen():
    cmd = input("Enter = speak, or type your message (q to quit): ").strip()
    if cmd:
        return cmd
    chunks = []
    def callback(indata, frame_count, time_info, status):
        chunks.append(indata.copy())
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                        dtype="float32", callback=callback):
        input("🎙️ Recording... press Enter to stop.")
    if not chunks:
        return ""
    audio = np.concatenate(chunks).flatten()
    segments, _ = stt.transcribe(audio, language="ja", vad_filter=True)
    text = "".join(s.text for s in segments).strip()
    print(f"あなた: {text}")   # always check what Whisper heard
    return text

def clean_for_speech(text):
    # speak only the Japanese reply, not corrections or English glosses
    for marker in ("✏️", "📘"):
        text = text.split(marker)[0]
    text = re.sub(r"[（(][ぁ-んァ-ンー・]+[）)]", "", text)  # drop furigana
    return text.strip()

def speak(text):
    text = clean_for_speech(text)
    if not text:
        return
    path = os.path.join(tempfile.gettempdir(), "tutor_reply.mp3")
    asyncio.run(edge_tts.Communicate(text, VOICE).save(path))
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.wait(100)
    pygame.mixer.music.unload()

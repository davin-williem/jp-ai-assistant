import re

import edge_tts

VOICE = "ja-JP-NanamiNeural"


def clean_for_speech(text: str) -> str:
    # speak only the Japanese reply, not corrections or English glosses
    for marker in ("✏️", "📘"):
        text = text.split(marker)[0]
    text = re.sub(r"[（(][ぁ-んァ-ンー・]+[）)]", "", text)  # drop furigana
    return text.strip()


async def synthesize(text: str, voice: str = VOICE) -> bytes:
    text = clean_for_speech(text)
    if not text:
        return b""
    audio = bytearray()
    async for chunk in edge_tts.Communicate(text, voice).stream():
        if chunk["type"] == "audio":
            audio.extend(chunk["data"])
    return bytes(audio)
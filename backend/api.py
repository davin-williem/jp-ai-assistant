from typing import Literal

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

from langfuse import get_client

from main import ask     
from tts import synthesize           
from prompts import SYSTEM_PROMPT 

app = FastAPI(title="Japanese Tutor API")


class Msg(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: list[Msg]
    level: str = "JLPT N5"
    lang: str = "English"


class TTSRequest(BaseModel):
    text: str
    

@app.post("/api/tts")
async def tts(req: TTSRequest):
    try:
        audio = await synthesize(req.text)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"TTS failed: {e}")
    if not audio:
        raise HTTPException(status_code=400, detail="Nothing to speak")
    return Response(content=audio, media_type="audio/mpeg")


@app.post("/api/chat")
def chat(req: ChatRequest):  # plain def: FastAPI runs it in a thread, so blocking calls are fine
    system = SYSTEM_PROMPT.format(level=req.level, lang=req.lang)
    msgs = [m.model_dump() for m in req.messages][-20:]
    while msgs and msgs[0]["role"] != "user":
        msgs.pop(0)
    if not msgs:
        raise HTTPException(status_code=400, detail="No user message")
    try:
        reply = ask(system, msgs)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"reply": reply}


@app.on_event("shutdown")
def _flush():
    get_client().flush()

@app.get("/api/health")
def health():
    return {"ok": True}
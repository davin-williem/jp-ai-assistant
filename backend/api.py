from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from main import ask                
from prompts import SYSTEM_PROMPT 

app = FastAPI(title="Japanese Tutor API")


class Msg(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: list[Msg]
    level: str = "JLPT N5"
    lang: str = "English"


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


@app.get("/api/health")
def health():
    return {"ok": True}
# backend_app.py
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI   # official SDK
from typing import List

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Set OPENAI_API_KEY environment variable")

client = OpenAI(api_key=OPENAI_API_KEY)   # create client

app = FastAPI(title="Simple Chat API")

class MessageIn(BaseModel):
    role: str           # "user" typically
    content: str

class ChatRequest(BaseModel):
    messages: List[MessageIn]
    model: str = "gpt-4o"   # choose model you have access to; change as needed

@app.post("/chat")
def chat(req: ChatRequest):
    # Build messages list for the API
    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    try:
        completion = client.chat.completions.create(
            model=req.model,
            messages=messages,
            # optional parameters:
            max_tokens=512,
            temperature=0.6,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # The SDK returns choices; take the assistant message content
    assistant_msg = completion.choices[0].message["content"]
    return {"reply": assistant_msg}

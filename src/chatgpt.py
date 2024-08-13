from openai import OpenAI
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import asyncio

router = APIRouter()

# OpenAI 클라이언트 초기화
client = OpenAI(api_key="sk-O-vaqq3fH3RMr2OddqtEKXFH75HSXYNu-Xbyu4jsFHT3BlbkFJVTb5lyCsFD2CcR3cO4HEK2JH2DEjD5bjc90Nws_iwA")

class ChatRequest(BaseModel):
    message: str

async def gpt_stream_response(message: str):
    try:
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message}],
            stream=True,
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content
                await asyncio.sleep(0)  # 비동기 제어
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def chat_with_gpt(chat_request: ChatRequest):
    try:
        return StreamingResponse(gpt_stream_response(chat_request.message), media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

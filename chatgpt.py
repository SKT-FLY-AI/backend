import os
from openai import OpenAI
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import asyncio
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# .env 파일에서 API 키를 가져오기
api_key = os.getenv("OPENAI_API_KEY")

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=api_key)

class ChatRequest(BaseModel):
    message: str

async def gpt_stream_response2(message: str):
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
        return StreamingResponse(gpt_stream_response2(chat_request.message), media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

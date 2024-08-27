from openai import OpenAI
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from typing import List
import asyncio
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from database import get_db
from models import Image, ChatLog
from schemas import ChatLogResponse, PooptRequest
from datetime import datetime, timedelta
import os
from pydantic import ValidationError
load_dotenv()

router = APIRouter()

# .env 파일에서 API 키를 가져오기
api_key = os.getenv("OPENAI_API_KEY")

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=api_key)

class ChatRequest(BaseModel):
    user_id: int
    message: str

async def gpt_stream_response(message: str, past_messages: List[dict]):
    try:
        messages = past_messages + [{"role": "user", "content": message}]
        
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            stream=True,
        )
        assistant_response = ""
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                assistant_response += content
                yield content
                await asyncio.sleep(0)  # 비동기 제어

        # GPT 응답을 대화 기록에 추가
        past_messages.append({"role": "assistant", "content": assistant_response})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chatgpt/poopt")
async def chat_with_gpt_poopt(request: ChatRequest):
    try:
        # 여기서 사용자가 보낸 메시지를 기반으로 초기 프롬프트를 생성합니다.
        user_prompt = (
            f"사용자가 입력한 메시지: '{request.message}'입니다. "
            "이와 관련된 건강 상태를 확인하고 답변을 작성해주세요."
        )

        # 초기 프롬프트에 대한 응답을 스트리밍으로 보냅니다.
        return StreamingResponse(gpt_stream_response(user_prompt, []), media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chatgpt/chat")
async def chat_with_gpt(chat_request: ChatRequest):
    try:
        # 예를 들어 사용자의 이전 대화 기록을 가져온다.
        # 이 예제에서는 간단히 빈 리스트로 시작하지만, 실제로는 DB나 세션에서 이전 대화 기록을 가져와야 합니다.
        past_messages = []

        return StreamingResponse(gpt_stream_response(chat_request.message, past_messages), media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

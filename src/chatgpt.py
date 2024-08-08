import openai
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

OPENAI_API_KEY = "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"

# OpenAI API Key 설정
openai.api_key = OPENAI_API_KEY

@router.post("/chat", response_model=ChatResponse)
async def chat_with_gpt(chat_request: ChatRequest):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", # 모델 업데이트 필요
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": chat_request.message}
            ]
        )
        answer = response.choices[0].message['content'].strip()
        return ChatResponse(response=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

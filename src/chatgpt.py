import openai
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

# OpenAI API Key 설정
openai.api_key = "sk-O-vaqq3fH3RMr2OddqtEKXFH75HSXYNu-Xbyu4jsFHT3BlbkFJVTb5lyCsFD2CcR3cO4HEK2JH2DEjD5bjc90Nws_iwA"  # 여기에 직접 API 키 입력

@router.post("/chat", response_model=ChatResponse)
async def chat_with_gpt(chat_request: ChatRequest):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": chat_request.message}
            ]
        )
        answer = response['choices'][0]['message']['content'].strip()
        return ChatResponse(response=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

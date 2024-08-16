from Input_text_generator import json_to_query
from openai import OpenAI
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import asyncio
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from database import get_db
from models import Image

load_dotenv()

router = APIRouter()

# OpenAI 클라이언트 초기화
client = OpenAI(api_key="sk-O-vaqq3fH3RMr2OddqtEKXFH75HSXYNu-Xbyu4jsFHT3BlbkFJVTb5lyCsFD2CcR3cO4HEK2JH2DEjD5bjc90Nws_iwA")

class ChatRequest(BaseModel):
    message: str

async def gpt_stream_response(poo_type: str, poo_color: str, poo_blood: str):
    try:
        prompt = (
            f"사용자의 대변 색상 코드: {poo_color}, 브리스톨 지수: {poo_type}, 혈액 존재: {'있음' if poo_blood else '없음'}이야, 이에 대한 건강 상태와 관련된 의심되는 상황을 해결하기 위해나에게 추가적인 질문을 한가지만 해줘. 그리고 내 변의 색과 Type, 출혈유무를 다시말해줘"
        )

        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content
                await asyncio.sleep(0)  # 비동기 제어
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_latest_image_analysis(db: Session, user_id: int):
    latest_image = db.query(Image).filter(Image.user_id == user_id).order_by(Image.upload_time.desc()).first()
    if latest_image is None:
        raise HTTPException(status_code=404, detail="No image found for this user.")
    return latest_image

@router.post("/poopt")
async def chat_with_gpt(user_id: int, db: Session = Depends(get_db)):
    try:
        # 가장 최근의 분석 결과를 불러옴
        latest_image = get_latest_image_analysis(db, user_id)

        # GPT에게 전달할 프롬프트 생성 및 응답
        return StreamingResponse(
            gpt_stream_response(
                latest_image.poo_type,
                latest_image.poo_color,
                latest_image.poo_blood
            ),
            media_type="text/plain"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

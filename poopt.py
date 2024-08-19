from Input_text_generator import json_to_query
from openai import OpenAI
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from typing import List
import asyncio
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from database import get_db
from models import Image, ChatLog
from datetime import datetime
from schemas import ChatLogResponse
from datetime import datetime, timedelta


load_dotenv()

router = APIRouter()

# OpenAI 클라이언트 초기화
client = OpenAI(api_key="sk-O-vaqq3fH3RMr2OddqtEKXFH75HSXYNu-Xbyu4jsFHT3BlbkFJVTb5lyCsFD2CcR3cO4HEK2JH2DEjD5bjc90Nws_iwA")

class ChatRequest(BaseModel):
    message: str

async def gpt_stream_response(poo_type: str, poo_color: str, poo_blood: int, user_id: int, db: Session, image_id: int):
    try:
        prompt = (
            f"사용자의 대변 색상 코드: {poo_color}, 브리스톨 지수: {poo_type}, 혈액 존재: {'있음' if poo_blood else '없음'}이야. 이와 관련된 건강 상태를 확인하고 상황을 해결하기 위해 나에게 추가적인 질문을 한가지만 해줘. 그리고 내 변의 색과 Type, 출혈유무를 다시말해줘."
        )

        # 사용자 질문을 DB에 저장
        user_log = ChatLog(
            user_id=user_id,
            role='user',
            message=prompt,
            timestamp=datetime.now(),
            image_id=image_id,  # 이미지 ID 저장
            poo_color=poo_color,  # poo_color 저장
            poo_type=poo_type,  # poo_type 저장
            poo_blood=poo_blood  # poo_blood 저장
        )
        db.add(user_log)
        db.commit()

        # GPT 스트림 시작
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )

        chatbot_response = ""

        # 스트림에서 데이터 읽기 및 응답 생성
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                chatbot_response += content
                yield content
                await asyncio.sleep(0)  # 비동기 제어

        # 챗봇의 응답을 DB에 저장
        assistant_log = ChatLog(
            user_id=user_id,
            role='assistant',
            message=chatbot_response,
            timestamp=datetime.now(),
            image_id=image_id,  # 이미지 ID 저장
            poo_color=poo_color,  # poo_color 저장
            poo_type=poo_type,  # poo_type 저장
            poo_blood=poo_blood  # poo_blood 저장
        )
        db.add(assistant_log)
        db.commit()

    except Exception as e:
        # 응답 시작 전에 예외 발생을 처리합니다.
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
        stream_response = gpt_stream_response(
            latest_image.poo_type,
            latest_image.poo_color,
            latest_image.poo_blood,
            user_id,  # user_id 추가
            db,  # db 추가
            latest_image.id  # image_id 추가
        )

        # StreamingResponse 생성
        return StreamingResponse(stream_response, media_type="text/plain")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# Chatlog 전부다 호출
@router.get("/chatlogs", response_model=List[ChatLogResponse])
async def get_chat_logs(request: Request, db: Session = Depends(get_db)):
    # 세션에서 사용자 ID 가져오기
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not logged in")

    # 사용자 ID를 기준으로 ChatLog 조회
    chat_logs = db.query(ChatLog).filter(ChatLog.user_id == user_id).order_by(ChatLog.timestamp.desc()).all()

    if not chat_logs:
        raise HTTPException(status_code=404, detail="No chat logs found for the user")

    return chat_logs


@router.get("/chatlogs/date_range", response_model=List[ChatLogResponse])
async def get_chat_logs_by_date_range(
    start_date: str, 
    end_date: str, 
    request: Request, 
    db: Session = Depends(get_db)
):
    # 세션에서 사용자 ID 가져오기
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not logged in")

    try:
        # 날짜 문자열을 datetime 객체로 변환
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)

        # 사용자 ID와 날짜 범위를 기준으로 ChatLog 조회
        chat_logs = db.query(ChatLog).filter(
            ChatLog.user_id == user_id,
            ChatLog.timestamp >= start_datetime,
            ChatLog.timestamp < end_datetime
        ).order_by(ChatLog.timestamp.desc()).all()

        if not chat_logs:
            raise HTTPException(status_code=404, detail="No chat logs found for the given date range")

        return chat_logs

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Please use YYYY-MM-DD format.")
    




@router.get("/chatlogs/scroll", response_model=List[ChatLogResponse])
async def get_chat_logs_by_offset(
    request: Request, 
    offset: int = 0, 
    limit: int = 40, 
    db: Session = Depends(get_db)
):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not logged in")

    chat_logs = db.query(ChatLog).filter(ChatLog.user_id == user_id)\
                                  .order_by(ChatLog.timestamp.desc())\
                                  .offset(offset)\
                                  .limit(limit)\
                                  .all()

    if not chat_logs:
        raise HTTPException(status_code=404, detail="No chat logs found for the given user")

    return chat_logs

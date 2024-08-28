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

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ChatRequest(BaseModel):
    message: str


async def gpt_stream_response(poo_type: str, poo_color: str, poo_blood: int, user_id: int, db: Session, image_id: int,prompt: str):
    try:
        prompt = (
            f"사용자의 대변 색상 코드: {poo_color}, 브리스톨 지수: {poo_type}, 혈액 존재: {'있음' if poo_blood else '없음'}입니다. "
            "이와 관련된 건강 상태를 확인하고 상황을 해결하기 위해 나에게 추가적인 질문을 한가지만 해줘. 그리고 내 변의 색과 Type, 출혈유무를 다시말해줘."
        )

        user_log = ChatLog(
            user_id=user_id,
            role='user',
            message=prompt,
            timestamp=datetime.now(),
            image_id=image_id,
            poo_color=poo_color,
            poo_type=poo_type,
            poo_blood=poo_blood
        )
        db.add(user_log)
        db.commit()

        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )

        chatbot_response = ""
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                chatbot_response += content
                yield content
                await asyncio.sleep(0)

        assistant_log = ChatLog(
            user_id=user_id,
            role='assistant',
            message=chatbot_response,
            timestamp=datetime.now(),
            image_id=image_id,
            poo_color=poo_color,
            poo_type=poo_type,
            poo_blood=poo_blood
        )
        db.add(assistant_log)
        db.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



def get_latest_image_analysis(db: Session, user_id: int):
    latest_image = db.query(Image).filter(Image.user_id == user_id).order_by(Image.upload_time.desc()).first()
    if latest_image is None:
        raise HTTPException(status_code=404, detail="No image found for this user.")
    return latest_image

# @router.post("/poopt")
# async def chat_with_gpt(request: PooptRequest, db: Session = Depends(get_db)):
#     user_id = request.user_id
#     try:
#         latest_image = get_latest_image_analysis(db, user_id)

#         stream_response = gpt_stream_response(
#             latest_image.poo_type,
#             latest_image.poo_color,
#             latest_image.poo_blood,
#             user_id,
#             db,
#             latest_image.id
#         )

#         return StreamingResponse(stream_response, media_type="text/plain")

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@router.post("/poopt")
async def chat_with_gpt(request: PooptRequest, db: Session = Depends(get_db)):
    try:
        print(f"Received request data: {request.dict()}")
        print(f"Received user_id: {request.user_id}")  # user_id를 출력
        print(f"Received message: {request.message}")  # message를 출력
        print(f"Received request: {request.json()}")  # 여기에서 요청 내용을 확인

        request = PooptRequest.parse_obj(request)   

        user_id = request.user_id
        user_prompt = request.message  # 사용자가 보낸 프롬프트

        latest_image = get_latest_image_analysis(db, user_id)

        prompt = (
            f"사용자가 입력한 메시지: '{user_prompt}'입니다. "
            f"대변 색상 코드: {latest_image.poo_color}, 브리스톨 지수: {latest_image.poo_type}, "
            f"혈액 존재: {'있음' if latest_image.poo_blood else '없음'}입니다. "
            "이와 관련된 건강 상태를 확인하고 상황을 해결하기 위해 답변을 작성해주세요."
        )

        print(f"Generated prompt: {prompt}")  # 생성된 프롬프트를 출력

        stream_response = gpt_stream_response(
            poo_type=latest_image.poo_type,  # poo_type 인수 추가
            poo_color=latest_image.poo_color,  # poo_color 인수 추가
            poo_blood=latest_image.poo_blood,  # poo_blood 인수 추가
            prompt=prompt,  # prompt 인수 추가
            user_id=user_id,
            db=db,  # db 인수 추가
            image_id=latest_image.id  # image_id 인수 추가
        )

        return StreamingResponse(stream_response, media_type="text/plain")

    except HTTPException as e:
        print(f"HTTP Exception: {e.detail}")
        raise e
    except ValidationError as e:
        print(f"Validation error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        print(f"General Exception: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/chatlogs", response_model=List[ChatLogResponse])
async def get_chat_logs(user_id: int = Query(...), db: Session = Depends(get_db)):
    # 사용자 ID를 기준으로 ChatLog 조회
    chat_logs = db.query(ChatLog).filter(ChatLog.user_id == user_id).order_by(ChatLog.timestamp.desc()).all()

    if not chat_logs:
        raise HTTPException(status_code=404, detail="No chat logs found for the user")

    return chat_logs


@router.get("/chatlogs/date_range", response_model=List[ChatLogResponse])
async def get_chat_logs_by_date_range(
    user_id: int = Query(...), 
    start_date: str = Query(...), 
    end_date: str = Query(...), 
    db: Session = Depends(get_db)
):
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
    user_id: int = Query(...), 
    offset: int = 0, 
    limit: int = 40, 
    db: Session = Depends(get_db)
):
    chat_logs = db.query(ChatLog).filter(ChatLog.user_id == user_id)\
                                  .order_by(ChatLog.timestamp.desc())\
                                  .offset(offset)\
                                  .limit(limit)\
                                  .all()

    if not chat_logs:
        raise HTTPException(status_code=404, detail="No chat logs found for the given user")

    return chat_logs
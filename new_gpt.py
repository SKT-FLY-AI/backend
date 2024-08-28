from openai import OpenAI
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from typing import List
import asyncio
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from database import get_db
from models import Image, ChatLog
from datetime import datetime
import os
from schemas import ChatLogResponse

load_dotenv()

router = APIRouter()

# .env 파일에서 API 키를 가져오기
api_key = os.getenv("OPENAI_API_KEY")

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=api_key)

class ChatRequest(BaseModel):
    user_id: int
    message: str
    poo_color: str
    poo_type: str
    image_id: int  # 추가된 필드

async def gpt_stream_response(poo_color: str, poo_type: str, message: str, past_messages: List[dict], db: Session, user_id: int, image_id: int):
    try:
        chat_prompt = [
            {"role": "system", "content": "당신은 필요한 말만 하는, 강아지 대변에 특화된 수의사입니다."},
            {
                "role": "user",
                "content": f"""
                나한테 우리 강아지 건강 상태를 파악하기 위해서, 
                FAISS 내 저장되어있는 문서를 기반으로
                {poo_color}를 갖고 있는 {poo_type}형태의 대변에 대한 분석 결과를 바탕으로 건강상태를 분석하기 위한 질문을 한가지 던져줘
                """
            }
        ]
        
        messages = chat_prompt + past_messages + [{"role": "user", "content": message}]
        
        # 사용자 메시지를 ChatLog에 저장
        user_log = ChatLog(
            user_id=user_id,
            role='user',
            message=message,
            timestamp=datetime.now(),
            poo_color=poo_color,
            poo_type=poo_type,
            image_id=image_id  # image_id 저장
        )
        db.add(user_log)
        db.commit()

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
                await asyncio.sleep(0)

        # GPT 응답을 ChatLog에 저장
        assistant_log = ChatLog(
            user_id=user_id,
            role='assistant',
            message=assistant_response,
            timestamp=datetime.now(),
            poo_color=poo_color,
            poo_type=poo_type,
            image_id=image_id  # image_id 저장
        )
        db.add(assistant_log)
        db.commit()

    except Exception as e:
        # 예외가 발생하면 클라이언트에 오류 메시지를 보냄
        yield f"\n[Error]: {str(e)}\n"

async def gpt_stream_response_mini(poo_color: str, poo_type: str, message: str, past_messages: List[dict], db: Session, user_id: int, image_id: int):
    try:
        chat_prompt = [
            {"role": "system", "content": "당신은 필요한 말만 하는, 강아지 대변에 특화된 수의사입니다."},
            {
                "role": "user",
                "content": f"""
                답변을 "분석: 분석내용, 색상: poo_color를 6가지 색으로 변환한 리스트(색상, 확률)"의 형태로 줘.
                6가지 색은 다음과 같아 : "갈색, 검은색, 빨간색, 흰색, 녹색, 노랑색" 으로 poo_color의 색상 코드값을 변환해줘.
                분석내용은 
                나한테 우리 강아지 건강 상태를 파악하기 위해서, 
                FAISS 내 저장되어있는 문서를 기반으로
                {poo_color}를 갖고 있는 {poo_type}형태의 대변에 대해 간단하게 10자 이내로 알려줘. 예를들면 "묽고 초록의 변입니다. 주의가 필요합니다." 처럼 줘.
                """
            }
        ]
        
        messages = chat_prompt + past_messages + [{"role": "user", "content": message}]
        
        # 사용자 메시지를 ChatLog에 저장
        user_log = ChatLog(
            user_id=user_id,
            role='user',
            message=message,
            timestamp=datetime.now(),
            poo_color=poo_color,
            poo_type=poo_type,
            image_id=image_id  # image_id 저장
        )
        db.add(user_log)
        db.commit()

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
                await asyncio.sleep(0)

        # GPT 응답을 ChatLog에 저장
        assistant_log = ChatLog(
            user_id=user_id,
            role='assistant',
            message=assistant_response,
            timestamp=datetime.now(),
            poo_color=poo_color,
            poo_type=poo_type,
            image_id=image_id  # image_id 저장
        )
        db.add(assistant_log)
        db.commit()

    except Exception as e:
        # 예외가 발생하면 클라이언트에 오류 메시지를 보냄
        yield f"\n[Error]: {str(e)}\n"

@router.post("/poopt")
async def chat_with_gpt_poopt(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        # 프롬프트에 필요한 변수들 ChatRequest에서 가져오기
        poo_color = request.poo_color
        poo_type = request.poo_type
        user_id = request.user_id
        image_id = request.image_id

        # 초기 프롬프트에 대한 응답을 스트리밍으로 보냅니다.
        return StreamingResponse(gpt_stream_response(poo_color, poo_type, request.message, [], db, user_id, image_id), media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/poopt_mini")
async def chat_with_gpt_poopt_mini(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        # 프롬프트에 필요한 변수들 ChatRequest에서 가져오기
        poo_color = request.poo_color
        poo_type = request.poo_type
        user_id = request.user_id
        image_id = request.image_id

        print(f"Received Request - user_id: {user_id}, poo_color: {poo_color}, poo_type: {poo_type}")  # 로그 추가

        # 초기 프롬프트에 대한 응답을 스트리밍으로 보냅니다.
        return StreamingResponse(
            gpt_stream_response_mini(poo_color, poo_type, request.message, [], db, user_id, image_id), 
            media_type="text/plain"
        )
    except Exception as e:
        print(f"Exception occurred: {str(e)}")  # 에러 발생 시 출력
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/chatlogs/{user_id}", response_model=List[ChatLogResponse])
async def get_chat_logs_by_user_id(user_id: int, db: Session = Depends(get_db)):
    """
    주어진 user_id에 해당하는 챗로그를 불러오는 API 엔드포인트
    """
    # user_id에 맞는 ChatLog 조회
    chat_logs = db.query(ChatLog).filter(ChatLog.user_id == user_id).order_by(ChatLog.timestamp.desc()).all()

    # 챗로그가 없을 경우 404 에러 발생
    if not chat_logs:
        raise HTTPException(status_code=404, detail="No chat logs found for the user")

    # 조회된 챗로그 반환
    return chat_logs
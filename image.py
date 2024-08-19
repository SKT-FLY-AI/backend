from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os
import shutil
from pydantic import BaseModel
from database import get_db 
from models import Image, User, ChatLog
from schemas import ImageResponse, ImageResponseWithoutPoints
from werkzeug.utils import secure_filename
from typing import List
import traceback
import register
from analyze import analyze_image
from pydantic import BaseModel
import json
import httpx
import poopt

router = APIRouter()

class ImageData(BaseModel):
    image_name: str
    user_id: int

class ImageResponse(BaseModel):
    id: int
    user_id: int
    file_path: str
    upload_time: datetime
    file_name: str
    poo_type: int
    poo_color: str
    poo_blood: int
    usersex: int
    class Config:
        orm_mode = True

async def call_poopt_endpoint(user_id: int, db: Session, image_id: int, poo_type: int, poo_color: str, poo_blood: int):
    url = f"http://223.194.44.32:8000/chatgpt/poopt"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                params={
                    "user_id": user_id,
                    "image_id": image_id,
                    "poo_type": poo_type,
                    "poo_color": poo_color,
                    "poo_blood": poo_blood
                }
            )
            response.raise_for_status()  # HTTP 에러가 있는 경우 예외 발생

            # chat_response = response.text

            # # 사용자 질문을 chat_logs에 저장
            # user_log = ChatLog(
            #     user_id=user_id,
            #     role='user',
            #     message=chat_response,
            #     timestamp=datetime.now(),
            #     image_id=image_id,
            #     poo_color=poo_color,
            #     poo_type=poo_type,
            #     poo_blood=poo_blood
            # )
            # db.add(user_log)
            # db.commit()

            # # 챗봇의 응답을 chat_logs에 저장
            # assistant_log = ChatLog(
            #     user_id=user_id,
            #     role='assistant',
            #     message=chat_response,
            #     timestamp=datetime.now(),
            #     image_id=image_id,
            #     poo_color=poo_color,
            #     poo_type=poo_type,
            #     poo_blood=poo_blood
            # )
            # db.add(assistant_log)
            # db.commit()

            # return chat_response

    except httpx.HTTPStatusError as e:
        print(f"HTTP error calling {url}: {e.response.status_code} - {e.response.text}")
        raise HTTPException(
            status_code=500,
            detail=f"Error calling /poopt: {e.response.status_code} - {e.response.text}"
        )
    except httpx.RequestError as e:
        print(f"Request error while calling {url}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Request error calling /poopt: {str(e)}"
        )
    except Exception as e:
        print(f"Unexpected error calling {url}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error calling /poopt: {str(e)}"
        )




#ai 서버 포함  
# 이미지 업로드 엔드포인트
# poo_color에 따른 의심되는 병명 매핑
doubt_mapping = {
    "danger" : [
        "#AD1A2A",
        "#AC192A", # 빨강
        "#1D4F36",
        "#4E5534", # 초록
        "#F4F0E5", # 하양
        "#000000", # 검은색
        "#F4F0E5", # INANTION
        "#D2C6B4",
        "#AE9C88",
        "#8E7861",
        "#D7C384",
        "#B7A05D",
        "#B49C1E",
        "#342113", # Constipation
        "#180B05",
        "#010101",
        "#534228",
        "#3D2C18",
    ]
}

@router.post("/upload", response_model=ImageResponse)
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        # 세션에서 사용자 ID 가져오기
        user_id = request.session.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not logged in")

        # 사용자 정보 확인
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        safe_filename = secure_filename(file.filename)
        if not safe_filename:
            raise HTTPException(status_code=400, detail="Invalid file name")

        # # 이미지 분석 요청
        analysis_result = analyze_image(file)  # AI 서버로 이미지 파일 객체를 전달하여 분석 요청
        poo_type = analysis_result['poo_type']
        poo_color = analysis_result['poo_color']
        poo_blood = analysis_result['poo_blood']

        # 의심되는 병명 설정 위에 매핑 참고
        # doubt = doubt_mapping.get(poo_color, "")
        
        # poo_type = 1  # 예시로 하드코딩된 값 사용
        # poo_color = "#AD1A2A"  # 내일 승호형 서버열리면 다시해보기
        # poo_blood = 1  
        # doubt = "스트레스"


        # 데이터베이스에 이미지 정보 저장
        new_image = Image(
            user_id=user.id,
            file_path=safe_filename,
            upload_time=datetime.now(),
            file_name=safe_filename,
            poo_type=poo_type,
            poo_color=poo_color,
            poo_blood=poo_blood,
            usersex=user.usersex

            #doubt=dobut
        )
        try:
            db.add(new_image)
            db.commit()
            db.refresh(new_image)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save image to the database: {str(e)}")

        # poo_blood가 1이거나 특정 poo_color일 때 /poopt 엔드포인트 호출
        if (
            poo_blood == 1 or
            poo_color in doubt_mapping.keys()
        ):
            await call_poopt_endpoint(user_id=user.id, db=db, image_id=new_image.id, poo_type=poo_type, poo_color=poo_color, poo_blood=poo_blood)

        # 응답에서 points를 제거하고 usersex를 포함
        return {
            "id": new_image.id,
            "user_id": new_image.user_id,
            "file_path": new_image.file_path,
            "upload_time": new_image.upload_time,
            "file_name": safe_filename,
            "poo_type": new_image.poo_type,
            "poo_color": new_image.poo_color,
            "poo_blood": new_image.poo_blood,
            "usersex": user.usersex, 
            # "doubt"=doubt
        }
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error during image upload: {e}\n{error_trace}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")



# 날짜별 이미지 조회 엔드포인트
@router.get("/date/{date}", response_model=List[ImageResponseWithoutPoints])
async def get_images_by_date_and_user(date: str, request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not logged in")

    try:
        start_date = datetime.strptime(date, '%Y-%m-%d')
        end_date = start_date + timedelta(days=1) - timedelta(seconds=1)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    images = db.query(Image).filter(
        Image.upload_time >= start_date,
        Image.upload_time <= end_date,
        Image.user_id == int(user_id)
    ).all()

    if not images:
        raise HTTPException(status_code=404, detail="No images found for the given date and user")

    return images

# 사용자별 이미지 조회 엔드포인트
@router.get("/user/{user_id}", response_model=List[ImageResponseWithoutPoints])
async def get_images_by_user(user_id: int, db: Session = Depends(get_db)):
    images = db.query(Image).filter(Image.user_id == user_id).all()
    if not images:
        raise HTTPException(status_code=404, detail="No images found for the given user")
    return images

@router.delete("/delete")
async def delete_image(user_id: int, date: str, request: Request, db: Session = Depends(get_db)):
    # 세션에서 사용자 ID를 가져오기
    logged_in_user_id = request.session.get("user_id")
    if not logged_in_user_id:
        raise HTTPException(status_code=401, detail="User not logged in")

    if int(logged_in_user_id) != user_id:
        raise HTTPException(status_code=403, detail="Cannot delete images of another user")

    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    images = db.query(Image).filter(
        Image.user_id == user_id,
        Image.upload_time.between(date_obj, date_obj + timedelta(days=1))
    ).all()

    if not images:
        raise HTTPException(status_code=404, detail="No images found for the given user and date")

    for image in images:
        file_path = image.file_path
        db.delete(image)
        db.commit()

        if os.path.exists(file_path):
            os.remove(file_path)
    
    return {"message": "Images deleted successfully", "user_id": user_id, "date": date}

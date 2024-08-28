from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request,Query, Form, FastAPI
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os
import traceback
from pydantic import BaseModel
from database import get_db 
from models import Image, User, DogInfo
from schemas import ImageResponse, ImageResponseWithoutPoints
from werkzeug.utils import secure_filename
from typing import List
import httpx
from analyze import analyze_image
from dotenv import load_dotenv
import register
from fastapi.middleware.cors import CORSMiddleware
import json



load_dotenv()

router = APIRouter()
app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인에서의 접근을 허용. 필요에 따라 특정 도메인으로 제한 가능
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)



# AI 서버 URL을 환경 변수에서 가져오기
AI_SERVER_URL = os.getenv("AI_SERVER_URL")

class ImageData(BaseModel):
    image_name: str
    user_id: int

async def call_poopt_endpoint(user_id: int, db: Session, image_id: int, poo_type: str, poo_color: str, poo_blood: int):
    url = f"{AI_SERVER_URL}/chatgpt/poopt"
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
            response.raise_for_status()

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

# 의심되는 병명 매핑
doubt_mapping = {
    "danger": [
        "#AD1A2A", "#AC192A", "#1D4F36", "#4E5534",
        "#F4F0E5", "#000000", "#D2C6B4", "#AE9C88",
        "#8E7861", "#D7C384", "#B7A05D", "#B49C1E",
        "#342113", "#180B05", "#010101", "#534228",
        "#3D2C18"
    ]
}

# @router.post("/upload", response_model=ImageResponse)
# async def upload_image(
#     request: Request,
#     file: UploadFile = File(...),
#     db: Session = Depends(get_db)
# ):
#     try:
#         # 세션에서 사용자 ID 가져오기
#         user_id = request.session.get("user_id")
#         if not user_id:
#             raise HTTPException(status_code=401, detail="User not logged in")

#         # 사용자 정보 확인
#         user = db.query(User).filter(User.id == user_id).first()
#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")

#         safe_filename = secure_filename(file.filename)
#         if not safe_filename:
#             raise HTTPException(status_code=400, detail="Invalid file name")

#         # 이미지 분석 요청
#         analysis_result = analyze_image(file)
#         poo_type = analysis_result['poo_type']
#         poo_color = analysis_result['poo_color']
#         poo_blood = analysis_result['poo_blood']

#         # 데이터베이스에 이미지 정보 저장
#         new_image = Image(
#             user_id=user.id,
#             file_path=safe_filename,
#             upload_time=datetime.now(),
#             file_name=safe_filename,
#             poo_type=poo_type,
#             poo_color=poo_color,
#             poo_blood=poo_blood,
#             usersex=user.usersex
#         )
#         try:
#             db.add(new_image)
#             db.commit()
#             db.refresh(new_image)
#         except Exception as e:
#             raise HTTPException(status_code=500, detail=f"Failed to save image to the database: {str(e)}")

#         # poo_blood가 1이거나 특정 poo_color일 때 /poopt 엔드포인트 호출
#         if poo_blood == 1 or poo_color in doubt_mapping.keys():
#             await call_poopt_endpoint(user_id=user.id, db=db, image_id=new_image.id, poo_type=poo_type, poo_color=poo_color, poo_blood=poo_blood)

#         return {
#             "id": new_image.id,
#             "user_id": new_image.user_id,
#             "file_path": new_image.file_path,
#             "upload_time": new_image.upload_time,
#             "file_name": safe_filename,
#             "poo_type": new_image.poo_type,
#             "poo_color": new_image.poo_color,
#             "poo_blood": new_image.poo_blood,
#             "usersex": user.usersex
#         }
#     except Exception as e:
#         error_trace = traceback.format_exc()
#         print(f"Error during image upload: {e}\n{error_trace}")
#         raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    


# @router.post("/upload", response_model=dict)
# async def upload_image(
#     request: Request,
#     file: UploadFile = File(...),
#     db: Session = Depends(get_db)
# ):
#     try:
#         # 세션에서 사용자 ID 가져오기
#         user_id = request.session.get("user_id")
#         if not user_id:
#             raise HTTPException(status_code=401, detail="User not logged in")

#         # 사용자 정보 확인
#         user = db.query(User).filter(User.id == user_id).first()
#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")

#         dog = db.query(DogInfo).filter(DogInfo.user_id == user_id).first()
#         if not dog:
#             raise HTTPException(status_code=404, detail="Dog not found for the user")


#         safe_filename = secure_filename(file.filename)
#         if not safe_filename:
#             raise HTTPException(status_code=400, detail="Invalid file name")

#         # 이미지 분석 요청
#         analysis_result = analyze_image(file)
#         poo_type = analysis_result['poo_type']
#         poo_color = analysis_result['poo_color']
#         poo_blood = analysis_result['poo_blood']

#         # 데이터베이스에 이미지 정보 저장
#         new_image = Image(
#             user_id=user.id,
#             file_path=safe_filename,
#             upload_time=datetime.now(),
#             file_name=safe_filename,
#             poo_type=poo_type,
#             poo_color=poo_color,
#             poo_blood=poo_blood,
#             dogsex = dog.dogsex  # 예시로 dogsex 필드를 포함
#         )
#         try:
#             db.add(new_image)
#             db.commit()
#             db.refresh(new_image)
#         except Exception as e:
#             raise HTTPException(status_code=500, detail=f"Failed to save image to the database: {str(e)}")


#         return {
#             "id": new_image.id,
#             "file_path": new_image.file_path,
#             "upload_time": new_image.upload_time,
#             "file_name": safe_filename,
#             "poo_type": new_image.poo_type,
#             "poo_color": new_image.poo_color,
#             "poo_blood": new_image.poo_blood,
#         }
#     except Exception as e:
#         error_trace = traceback.format_exc()
#         print(f"Error during image upload: {e}\n{error_trace}")
#         raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

LOCAL_SERVER_URL = os.getenv("LOCAL_SERVER_URL")
BACK_SERVER_URL = os.getenv("BACK_SERVER_URL")

def get_logged_in_user_id(session: dict) -> int:
    user_id = session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not logged in")
    return user_id
@router.post("/upload")
async def upload_image(
    user_id: int = Form(...),  # user_id를 Form 데이터로 받습니다.
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        # 사용자 정보 확인
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        dog = db.query(DogInfo).filter(DogInfo.user_id == user_id).first()
        if not dog:
            raise HTTPException(status_code=404, detail="Dog not found for the user")

        safe_filename = secure_filename(file.filename)
        if not safe_filename:
            raise HTTPException(status_code=400, detail="Invalid file name")

        # 이미지 분석 요청
        analysis_result = analyze_image(file)
        poo_type = analysis_result['poo_type']  # poo_type은 이제 string으로 반환됩니다.
        poo_color = json.dumps(analysis_result['poo_color'])  # 리스트를 JSON 문자열로 변환

        # 데이터베이스에 이미지 정보 저장
        new_image = Image(
            user_id=user.id,
            file_path=safe_filename,
            upload_time=datetime.now(),
            file_name=safe_filename,
            poo_type=poo_type,  # string 타입의 poo_type 저장
            poo_color=poo_color,  # JSON 문자열로 변환한 poo_color 저장
            dogsex=dog.dogsex  # dog 정보에 따라 sex 값을 저장합니다.
        )
        try:
            db.add(new_image)
            db.commit()
            db.refresh(new_image)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save image to the database: {str(e)}")
            
        return {
            "id": new_image.id,
            "file_path": new_image.file_path,
            "upload_time": new_image.upload_time,
            "file_name": safe_filename,
            "poo_type": new_image.poo_type,
            "poo_color": new_image.poo_color,
        }
    except Exception as e:
        print(f"Error during image upload: {str(e)}")
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다.")



@router.get("/date/{date}", response_model=List[ImageResponseWithoutPoints])
async def get_images_by_date_and_user(date: str, user_id: int = Query(...), db: Session = Depends(get_db)):
    try:
        start_date = datetime.strptime(date, '%Y-%m-%d')
        end_date = start_date + timedelta(days=1) - timedelta(seconds=1)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    images = db.query(Image).filter(
        Image.upload_time >= start_date,
        Image.upload_time <= end_date,
        Image.user_id == user_id
    ).all()

    if not images:
        raise HTTPException(status_code=404, detail="No images found for the given date and user")

    return images

@router.get("/user/{user_id}", response_model=List[ImageResponseWithoutPoints])
async def get_images_by_user(user_id: int, db: Session = Depends(get_db)):
    images = db.query(Image).filter(Image.user_id == user_id).all()
    if not images:
        raise HTTPException(status_code=404, detail="No images found for the given user")
    return images

@router.delete("/delete")
async def delete_image(user_id: int, date: str, db: Session = Depends(get_db)):
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
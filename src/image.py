from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os
import shutil
from database import get_db 
from models import Image, User
from schemas import ImageResponse
from werkzeug.utils import secure_filename
from typing import List
import traceback
import register
from analyze import analyze_image
from pydantic import BaseModel
import json



router = APIRouter()

class ImageData(BaseModel):
    image_name: str
    user_id: int

# ai 서버에 보내는거 미포함
"""
# 이미지 업로드 엔드포인트
@router.post("/upload", response_model=ImageResponse)
async def upload_image(
    request: Request,  # FastAPI의 Request 객체를 통해 세션 또는 쿠키 접근 가능
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    try:
        # 세션에서 사용자 ID 가져오기 (예시)
        user_id = request.session.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not logged in")

        # 사용자 정보 확인
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # 사용자별 파일 업로드 디렉토리 설정
        upload_dir = os.path.join("uploads", str(user_id))
        if not os.path.exists(upload_dir):
            try:
                os.makedirs(upload_dir, exist_ok=True)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to create directory: {str(e)}")

        # 안전한 파일 이름 생성
        safe_filename = secure_filename(file.filename)
        if not safe_filename:
            raise HTTPException(status_code=400, detail="Invalid file name")

        # 파일 저장 경로 설정
        file_path = os.path.join(upload_dir, safe_filename)
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

        # 데이터베이스에 이미지 정보 저장
        new_image = Image(
            user_id=user.id, 
            file_path=file_path, 
            upload_time=datetime.now(),
            file_name=safe_filename
        )
        try:
            db.add(new_image)
            db.commit()
            db.refresh(new_image)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save image to the database: {str(e)}")

        # 이미지 URL 생성
        image_url = f"http://223.194.44.32:8000/uploads/{user_id}/{safe_filename}"

        return {
            "id": new_image.id,
            "user_id": new_image.user_id,
            "file_path": image_url,
            "upload_time": new_image.upload_time,
            "file_name": safe_filename,
            "points": user.points  # 현재 포인트 반환
        }
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error during image upload: {e}\n{error_trace}")  # 에러 추적 정보 출력
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
"""


#ai 서버 포함  
# 이미지 업로드 엔드포인트
@router.post("/upload", response_model=ImageResponse)
async def upload_image(
    request: Request,  # FastAPI의 Request 객체를 통해 세션 또는 쿠키 접근 가능
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    try:
        # 세션에서 사용자 ID 가져오기 (예시)
        user_id = request.session.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not logged in")

        # 사용자 정보 확인
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")



        # 사용자별 파일 업로드 디렉토리 설정
        upload_dir = os.path.join("uploads", str(user_id))
        if not os.path.exists(upload_dir):
            try:
                os.makedirs(upload_dir, exist_ok=True)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to create directory: {str(e)}")

        # 안전한 파일 이름 생성
        safe_filename = secure_filename(file.filename)
        if not safe_filename:
            raise HTTPException(status_code=400, detail="Invalid file name")

        # 파일 저장 경로 설정
        file_path = os.path.join(upload_dir, safe_filename)
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

        # 이미지 분석 요청
        analysis_result = analyze_image(file_path)  # AI 서버로 이미지 파일 경로 전달하여 분석 요청
        poo_type = analysis_result['poo_type']
        poo_color = analysis_result['poo_color']
        poo_blood = analysis_result['poo_isBlood']

        # 데이터베이스에 이미지 정보 저장
        new_image = Image(
            user_id=user.id, 
            file_path=file_path, 
            upload_time=datetime.now(),
            file_name=safe_filename,
            poo_type=poo_type,
            poo_color=poo_color,
            poo_blood=poo_blood
        )
        try:
            db.add(new_image)
            db.commit()
            db.refresh(new_image)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save image to the database: {str(e)}")

        # 이미지 URL 생성
        image_url = f"http://223.194.44.32:8000/uploads/{user_id}/{safe_filename}"

        return {
            "id": new_image.id,
            "user_id": new_image.user_id,
            "file_path": image_url,
            "upload_time": new_image.upload_time,
            "file_name": safe_filename,
            "poo_type": new_image.poo_type,
            "poo_color": new_image.poo_color,
            "poo_blood": new_image.poo_blood,
            "points": user.points  # 현재 포인트 반환
        }
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error during image upload: {e}\n{error_trace}")  # 에러 추적 정보 출력
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")








# 날짜별 이미지 조회 엔드포인트
@router.get("/{date}", response_model=List[ImageResponse])
async def get_images_by_date_and_user(date: str, request: Request, db: Session = Depends(get_db)):
    # 세션에서 사용자 ID를 가져오기
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
@router.get("/{user_id}", response_model=List[ImageResponse])
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

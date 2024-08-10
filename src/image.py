from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
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

router = APIRouter()

# 이미지 업로드 엔드포인트
@router.post("/upload/", response_model=ImageResponse)
async def upload_image(file: UploadFile = File(...), Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    try:
        # JWT 토큰에서 사용자 ID 가져오기
        Authorize.jwt_required()
        user_id = Authorize.get_jwt_subject()

        # 사용자 정보 확인
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        # 사용자에게 포인트 추가
        user.points += 10  # 이미지를 업로드할 때 10 포인트 추가
        db.commit()

        # 사용자별 파일 업로드 디렉토리 설정
        upload_dir = os.path.join("uploads", str(user_id))
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir, exist_ok=True)

        # 안전한 파일 이름 생성
        safe_filename = secure_filename(file.filename)
        if not safe_filename:
            raise HTTPException(status_code=400, detail="Invalid file name")

        # 파일 저장 경로 설정
        file_path = os.path.join(upload_dir, safe_filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 데이터베이스에 이미지 정보 저장
        new_image = Image(
            user_id=user.id, 
            file_path=file_path, 
            upload_time=datetime.now(),
            file_name=safe_filename
        )
        db.add(new_image)
        db.commit()
        db.refresh(new_image)

        # 이미지 URL 생성
        image_url = f"http://127.0.0.1:8000/uploads/{user_id}/{safe_filename}"

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

# 날짜별 이미지 조회 엔드포인트
@router.get("/date/{date}", response_model=List[ImageResponse])
async def get_images_by_date_and_user(date: str, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()

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
@router.get("/users/{user_id}", response_model=List[ImageResponse])
async def get_images_by_user(user_id: int, db: Session = Depends(get_db)):
    images = db.query(Image).filter(Image.user_id == user_id).all()
    if not images:
        raise HTTPException(status_code=404, detail="No images found for the given user")
    return images

# 이미지 삭제 엔드포인트
@router.delete("/delete/")
async def delete_image(user_id: int, date: str, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    logged_in_user_id = Authorize.get_jwt_subject()

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

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os
import shutil
from database import get_db
from models import Image, User
from schemas import ImageResponse
from typing import List

router = APIRouter()

# 이미지 업로드 엔드포인트
@router.post("/upload/", response_model=ImageResponse)
async def upload_image(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    # 세션에서 사용자 ID 가져오기
    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authorized")

    # 사용자 정보 확인
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # 사용자가 오늘 업로드한 이미지 개수 확인 (최대 3개)
    today = datetime.now().date()
    count_today_images = db.query(Image).filter(
        Image.user_id == user.id,
        Image.upload_time.between(today, today + timedelta(days=1))
    ).count()

    if count_today_images >= 3:
        raise HTTPException(status_code=400, detail="You can only upload 3 images per day")

    # 파일 업로드 디렉토리 설정
    upload_dir = "uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    # 파일 저장
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 데이터베이스에 이미지 정보 저장
    new_image = Image(
        user_id=user.id, 
        file_path=file_path, 
        upload_time=datetime.now(),
        file_name=file.filename  # file_name 저장
    )
    db.add(new_image)
    db.commit()
    db.refresh(new_image)

    # 이미지 URL 생성
    image_url = f"http://127.0.0.1:8000/uploads/{file.filename}"

    return {
        "id": new_image.id,
        "user_id": new_image.user_id,
        "file_path": image_url,
        "upload_time": new_image.upload_time,
        "file_name": file.filename
    }

# 날짜별 이미지 조회 엔드포인트
@router.get("/date/{date}", response_model=List[ImageResponse])
async def get_images_by_date(date: str, db: Session = Depends(get_db)):
    try:
        # 입력된 날짜를 기준으로 시작과 끝 시간 설정
        start_date = datetime.strptime(date, '%Y-%m-%d')
        end_date = start_date + timedelta(days=1) - timedelta(seconds=1)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    # 날짜 범위에 맞는 이미지 쿼리
    images = db.query(Image).filter(
        Image.upload_time >= start_date,
        Image.upload_time <= end_date
    ).all()

    if not images:
        raise HTTPException(status_code=404, detail="No images found for the given date")

    return images

# 사용자별 이미지 조회 엔드포인트
@router.get("/user/{user_id}", response_model=List[ImageResponse])
async def get_images_by_user(user_id: int, db: Session = Depends(get_db)):
    images = db.query(Image).filter(Image.user_id == user_id).all()
    if not images:
        raise HTTPException(status_code=404, detail="No images found for the given user")
    return images

# 이미지 삭제 엔드포인트
@router.delete("/delete/")
async def delete_image(user_id: int, date: str, request: Request, db: Session = Depends(get_db)):
    # 세션에서 로그인된 사용자 ID 가져오기
    logged_in_user_id = request.session.get("user_id")
    if logged_in_user_id is None:
        raise HTTPException(status_code=401, detail="Not authorized")

    # 다른 사용자의 이미지를 삭제하려는 경우
    if logged_in_user_id != user_id:
        raise HTTPException(status_code=403, detail="Cannot delete images of another user")

    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    # 지정된 날짜의 이미지 검색
    images = db.query(Image).filter(
        Image.user_id == user_id,
        Image.upload_time.between(date_obj, date_obj + timedelta(days=1))
    ).all()

    if not images:
        raise HTTPException(status_code=404, detail="No images found for the given user and date")

    # 이미지 삭제
    for image in images:
        file_path = image.file_path
        db.delete(image)
        db.commit()

        # 파일 시스템에서 이미지 삭제
        if os.path.exists(file_path):
            os.remove(file_path)
    
    return {"message": "Images deleted successfully", "user_id": user_id, "date": date}

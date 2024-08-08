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

@router.post("/upload/", response_model=ImageResponse)
async def upload_image(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authorized")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if the user has already uploaded 3 images today
    today = datetime.now().date()
    count_today_images = db.query(Image).filter(
        Image.user_id == user.id,
        Image.upload_time.between(today, today + timedelta(days=1))
    ).count()
    if count_today_images >= 3:
        raise HTTPException(status_code=400, detail="You can only upload 3 images per day")

    upload_dir = "uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_image = Image(user_id=user.id, file_path=file_path, upload_time=datetime.now())
    db.add(new_image)
    db.commit()
    db.refresh(new_image)

    # 이미지 URL 생성
    image_url = f"http://127.0.0.1:8000/uploads/{file.filename}"

    return {"id": new_image.id, "user_id": new_image.user_id, "file_path": image_url, "upload_time": new_image.upload_time, "file_name": file.filename}

@router.get("/date/{date}", response_model=List[ImageResponse])
async def get_images_by_date(date: str, db: Session = Depends(get_db)):
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    images = db.query(Image).filter(
        Image.upload_time.between(date_obj, date_obj + timedelta(days=1))
    ).all()

    return images

@router.get("/user/{user_id}", response_model=List[ImageResponse])
async def get_images_by_user(user_id: int, db: Session = Depends(get_db)):
    images = db.query(Image).filter(Image.user_id == user_id).all()
    return images

@router.delete("/delete/")
async def delete_image(user_id: int, date: str, request: Request, db: Session = Depends(get_db)):
    logged_in_user_id = request.session.get("user_id")
    if logged_in_user_id is None:
        raise HTTPException(status_code=401, detail="Not authorized")

    if logged_in_user_id != user_id:
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
        # 삭제할 파일 경로
        file_path = image.file_path
        # 데이터베이스에서 이미지 삭제
        db.delete(image)
        db.commit()

        # 파일 시스템에서 이미지 삭제
        if os.path.exists(file_path):
            os.remove(file_path)
    
    return {"message": "Images deleted successfully", "user_id": user_id, "date": date}

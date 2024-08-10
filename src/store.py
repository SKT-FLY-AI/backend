from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import User, Item, UserItem
from schemas import Item, ItemCreate
from database import get_db
from fastapi_jwt_auth import AuthJWT
from typing import List

router = APIRouter()

@router.post("/items/", response_model=Item)
async def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = Item(name=item.name, description=item.description, price=item.price)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.get("/items/", response_model=List[Item])
async def read_items(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    items = db.query(Item).offset(skip).limit(limit).all()
    return items

@router.post("/buy-item/{item_id}")
async def buy_item(item_id: int, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()

    user = db.query(User).filter(User.id == user_id).first()
    item = db.query(Item).filter(Item.id == item_id).first()

    if not user or not item:
        raise HTTPException(status_code=404, detail="User or Item not found")

    if user.points < item.price:
        raise HTTPException(status_code=400, detail="Not enough points")

    user.points -= item.price
    user_item = UserItem(user_id=user_id, item_id=item.id)
    db.add(user_item)
    db.commit()
    return {"message": "Item purchased successfully"}

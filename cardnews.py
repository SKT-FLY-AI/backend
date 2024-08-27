import os
import requests
from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv

router = APIRouter()

# .env 파일에서 환경 변수 로드
load_dotenv()

# 환경 변수에서 Google API Key와 Search Engine ID 가져오기
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")

@router.get("/cardnews")
async def get_card_news(query: str):
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": GOOGLE_API_KEY,
            "cx": SEARCH_ENGINE_ID,
            "q": query,
            "num": 5  # 최대 5개의 결과를 가져옴
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        results = response.json().get('items', [])
        card_news = []

        for item in results:
            card = {
                "title": item.get("title"),
                "link": item.get("link"),
                "snippet": item.get("snippet"),
                "image": item.get("pagemap", {}).get("cse_image", [{}])[0].get("src")
            }
            card_news.append(card)
        
        return {"cards": card_news}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

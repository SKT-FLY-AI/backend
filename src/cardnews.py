import requests
from fastapi import APIRouter, HTTPException

router = APIRouter()


# settings.py (예시)
GOOGLE_API_KEY = "AIzaSyAUrHGKxUv4uolLpQeYaeoduMS0oCCC_kE"
SEARCH_ENGINE_ID = "424e29605a7c34b85"


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


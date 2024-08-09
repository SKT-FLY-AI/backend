from fastapi import FastAPI, HTTPException, Depends
import httpx

app = FastAPI()

# T Map API Key
T_MAP_API_KEY = "8AV1r6kuU83P0xkCqthoN15d19fX6AjM6E1Hl4VL" 

# T Map API URL
T_MAP_BASE_URL = "https://apis.openapi.sk.com"

# 병원 추천 API
@app.get("/recommend/hospitals")
async def recommend_hospitals(lat: float, lon: float):
    # POI 검색 API를 사용하여 주변 병원 검색
    params = {
        "version": "1",
        "centerLat": lat,
        "centerLon": lon,
        "categories": "병원",
        "radius": "1000",
        "count": "10",
        "appKey": T_MAP_API_KEY
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{T_MAP_BASE_URL}/tmap/pois/search/around", params=params)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch hospital data")

    data = response.json()
    pois = data.get("searchPoiInfo", {}).get("pois", {}).get("poi", [])
    
    if not pois:
        return {"message": "No hospitals found within 1km radius"}

    # 필요한 정보만 추출하여 반환
    hospitals = [
        {
            "name": poi["name"],
            "address": poi["newAddressList"]["newAddress"][0]["fullAddressRoad"] if poi.get("newAddressList") else poi.get("frontLat"), # 주소가 없는 경우 좌표를 사용
            "distance": poi["distance"],
            "tel": poi.get("telNo")
        }
        for poi in pois
    ]

    return {"hospitals": hospitals}


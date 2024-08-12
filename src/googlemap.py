from fastapi import FastAPI, Depends, HTTPException, APIRouter
from pydantic import BaseModel, Field
import googlemaps

router = APIRouter()


# Google Maps API Key
GOOGLE_MAPS_API_KEY = "AIzaSyAUrHGKxUv4uolLpQeYaeoduMS0oCCC_kE"
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

# 기본위치 정의
class Location(BaseModel):
    latitude: float = Field(37.49202451946862, description="위도 (기본값: 37.49202451946862)")
    longitude: float = Field(126.92630733625505, description="경도 (기본값: 126.92630733625505)")



# int = 1000 -> 1km 
@router.post("/maps/nearby-hospitals/")
async def nearby_hospitals(location: Location = Depends(), radius: int = 1000):
    """
    # 디폴트 값으로 SKT 보라매사옥으로 설정해놨음
    """
    try:
        places_result = gmaps.places_nearby(
            location=(location.latitude, location.longitude),
            radius=radius,
            type='hospital'
        )
        
        hospitals = []
        for place in places_result.get('results', []):
            hospitals.append({
                "name": place['name'],
                "address": place.get('vicinity', 'Address not available'),
                "location": place['geometry']['location']
            })

        return {"hospitals": hospitals}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/maps/directions/")
async def get_directions(origin: Location = Depends(), destination: Location = Depends()):
    """
    사용자 현재 위치를 가져와서 목적지까지 길안내 Google api
    """
    try:
        directions_result = gmaps.directions(
            origin=(origin.latitude, origin.longitude),
            destination=(destination.latitude, destination.longitude),
            mode="driving"
        )

        if not directions_result:
            raise HTTPException(status_code=404, detail="No directions found")

        steps = []
        for step in directions_result[0]['legs'][0]['steps']:
            steps.append({
                "distance": step['distance']['text'],
                "duration": step['duration']['text'],
                "instructions": step['html_instructions']
            })

        return {"directions": steps}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, HTTPException
from typing import Dict
import requests
import warnings

warnings.filterwarnings("ignore")

APP_KEY = 'M4iHDgDxhH2ekATfumuLL3Xx0UpIkrtm9GahH1iJ'

router = APIRouter()

def get_total_time(start_poi: Dict[str, float], end_poi: Dict[str, float]) -> int:
    url = f'https://apis.openapi.sk.com/tmap/routes?version=1&appKey={APP_KEY}'
    data = {
        'startX': start_poi['longitude'],
        'startY': start_poi['latitude'],
        'endX': end_poi['longitude'],
        'endY': end_poi['latitude']
    }
    response = requests.post(url, json=data, verify=False)
    result = response.json()
    total_time = result['features'][0]['properties']['totalTime']
    return total_time

def get_poi_by_keyword(keyword: str) -> Dict[str, float]:
    url = f'https://apis.openapi.sk.com/tmap/pois?version=1&appKey={APP_KEY}&searchKeyword={keyword}'
    response = requests.get(url, verify=False)
    result = response.json()
    
    if 'searchPoiInfo' in result and 'pois' in result['searchPoiInfo']:
        pois = result['searchPoiInfo']['pois'].get('poi', [])
        if pois:
            first_poi = pois[0]
            latitude = first_poi['noorLat']
            longitude = first_poi['noorLon']
            name = first_poi['name']
            poi = {
                'latitude': latitude,
                'longitude': longitude,
                'name': name
            }
            return poi
        else:
            raise HTTPException(status_code=404, detail=f"No POI found for keyword: {keyword}")
    else:
        raise HTTPException(status_code=400, detail=f"Invalid response for keyword: {keyword}, response: {result}")

def get_nearby_digestive_hospitals(latitude, longitude, radius=5000):
    """
    사용자 위치 주변의 소화기 관련 병원을 검색합니다.
    :param latitude: 사용자의 위도
    :param longitude: 사용자의 경도
    :param radius: 검색 반경 (미터 단위, 기본값 1000m)
    :return: 주변 소화기 관련 병원 목록
    """
    keywords = ["병원"]
    hospitals = []

    for keyword in keywords:
        url = f'https://apis.openapi.sk.com/tmap/pois/search/around?version=1&appKey={APP_KEY}'
        params = {
            'centerLat': latitude,
            'centerLon': longitude,
            'radius': radius,
            'searchKeyword': keyword,
            'searchtypCd': 'A',  # A: 관련 검색어 주변 POI 검색
            'reqCoordType': 'WGS84GEO',
            'resCoordType': 'WGS84GEO',
            'count': 100  # 최대 결과 수
        }
        
        response = requests.get(url, params=params, verify=False)
        result = response.json()
        
        if 'searchPoiInfo' in result and 'pois' in result['searchPoiInfo']:
            pois = result['searchPoiInfo']['pois'].get('poi', [])
            for poi in pois:
                if any(kw in poi['name'] for kw in ["병원", "의원"]):
                    hospital = {
                        'name': poi['name'],
                        'latitude': poi['noorLat'],
                        'longitude': poi['noorLon'],
                        'distance': poi['radius'],
                        'department': keyword
                    }
                    hospitals.append(hospital)
    
    # 중복 제거
    unique_hospitals = list({v['name']:v for v in hospitals}.values())
    return sorted(unique_hospitals, key=lambda x: float(x['distance']))

# 사용 예시
user_lat = 37.566381  # 서울시청 위도
user_lon = 126.92630733625505  # 서울시청 경도

nearby_hospitals = get_nearby_digestive_hospitals(user_lat, user_lon)
print(f"Found {len(nearby_hospitals)} digestive-related hospitals within 1km:")
for hospital in nearby_hospitals:
    print(f"Name: {hospital['name']}, Department: {hospital['department']}, Distance: {hospital['distance']}m")
# FastAPI 엔드포인트

@router.get("/time")
async def calculate_total_time(start_lat: float, start_lon: float, end_lat: float, end_lon: float):
    start_poi = {"latitude": start_lat, "longitude": start_lon}
    end_poi = {"latitude": end_lat, "longitude": end_lon}
    try:
        total_time = get_total_time(start_poi, end_poi)
        return {"total_time": total_time}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/poi")
async def search_poi(keyword: str):
    try:
        poi = get_poi_by_keyword(keyword)
        return poi
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hospitals")
async def search_nearby_hospitals(lat: float, lon: float, radius: int = 5000):
    try:
        hospitals = get_nearby_digestive_hospitals(lat, lon, radius)
        return {"hospitals": hospitals}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

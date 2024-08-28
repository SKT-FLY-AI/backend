import requests
import warnings

warnings.filterwarnings("ignore")

APP_KEY = 'M4iHDgDxhH2ekATfumuLL3Xx0UpIkrtm9GahH1iJ'

def get_total_time(start_poi, end_poi):
    url = f'https://apis.openapi.sk.com/tmap/routes/pedestrian?version=1&appKey={APP_KEY}'
    data = {
        'startX': start_poi['longitude'],
        'startY': start_poi['latitude'],
        'endX': end_poi['longitude'],
        'endY': end_poi['latitude'],
        'reqCoordType': 'WGS84GEO',
        'resCoordType': 'WGS84GEO'
    }
    response = requests.post(url, json=data, verify=False)
    result = response.json()
    # Tmap API에서 시간은 초 단위로 반환되므로, 분 단위로 변환합니다.
    total_time = result['features'][0]['properties']['totalTime'] // 60
    return total_time

def get_nearby_digestive_hospitals_with_time(latitude, longitude, radius=1000):
    """
    사용자 위치 주변의 소화기 관련 병원을 검색하고, 각 병원까지의 시간을 계산합니다.
    :param latitude: 사용자의 위도
    :param longitude: 사용자의 경도
    :param radius: 검색 반경 (미터 단위, 기본값 1000m)
    :return: 주변 소화기 관련 병원 목록과 각 병원까지의 이동 시간
    """
    keywords = ["병원"]
    hospitals_with_time = []

    for keyword in keywords:
        url = f'https://apis.openapi.sk.com/tmap/pois/search/around?version=1&appKey={APP_KEY}'
        params = {
            'centerLat': latitude,
            'centerLon': longitude,
            'radius': radius,
            'searchKeyword': keyword,
            'searchtypCd': 'A',
            'reqCoordType': 'WGS84GEO',
            'resCoordType': 'WGS84GEO',
            'count': 100
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
                    start_poi = {'latitude': latitude, 'longitude': longitude}
                    end_poi = {'latitude': hospital['latitude'], 'longitude': hospital['longitude']}
                    travel_time = get_total_time(start_poi, end_poi)
                    hospital['travel_time'] = travel_time
                    hospitals_with_time.append(hospital)

    # 중복 제거
    unique_hospitals = list({v['name']: v for v in hospitals_with_time}.values())
    return sorted(unique_hospitals, key=lambda x: float(x['distance']))

# 사용 예시
user_lat = 37.49202451946862
user_lon = 126.92630733625505  

nearby_hospitals = get_nearby_digestive_hospitals_with_time(user_lat, user_lon)
print(f"Found {len(nearby_hospitals)} digestive-related hospitals within 1km:")
for hospital in nearby_hospitals:
    print(f"Name: {hospital['name']}, Department: {hospital['department']}, Distance: {hospital['distance']}m, Travel time: {hospital['travel_time']} minutes")

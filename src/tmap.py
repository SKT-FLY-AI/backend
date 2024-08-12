import requests
import warnings

warnings.filterwarnings("ignore")

APP_KEY = 'M4iHDgDxhH2ekATfumuLL3Xx0UpIkrtm9GahH1iJ'  # 발급받은 API 키를 입력하세요

def get_total_time(start_poi, end_poi):
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

def get_poi_by_keyword(keyword):
    """
    poi: points of interest
    """
    url = f'https://apis.openapi.sk.com/tmap/pois?version=1&appKey={APP_KEY}&searchKeyword={keyword}'
    response = requests.get(url, verify=False)
    result = response.json()
    
    # 응답에 'searchPoiInfo' 키가 있는지 확인합니다.
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
            raise ValueError(f"No POI found for keyword: {keyword}")
    else:
        raise ValueError(f"Invalid response for keyword: {keyword}, response: {result}")


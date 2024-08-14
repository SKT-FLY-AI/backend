import requests

def analyze_image(file):
    ai_server_url = "http://223.194.44.78:8000/analysis"  # AI 서버의 엔드포인트

    # 파일 객체를 전송
    files = {'file': (file.filename, file.file, file.content_type)}
    
    response = requests.post(ai_server_url, files=files)  # 파일을 multipart/form-data로 전송
    
    if response.status_code == 200:
        return response.json()  # 분석 결과를 JSON으로 반환
    else:
        raise Exception(f"Failed to analyze image: {response.status_code}, {response.text}")
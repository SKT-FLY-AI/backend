import os
import requests
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

def analyze_image(file):
    # 환경 변수에서 AI 서버 URL 가져오기
    ai_server_url = os.getenv("AI_SERVER_URL")
    
    if not ai_server_url:
        raise Exception("AI_SERVER_URL is not set in the environment variables.")

    # 파일 객체를 전송
    files = {'file': (file.filename, file.file, file.content_type)}
    
    response = requests.post(ai_server_url, files=files)  # 파일을 multipart/form-data로 전송
    
    if response.status_code == 200:
        return response.json()  # 분석 결과를 JSON으로 반환
    else:
        raise Exception(f"Failed to analyze image: {response.status_code}, {response.text}")





"""'
# /analysis 경로에 대한 POST 요청 처리
@app.post("/analysis")
async def analyze_image(data: ImageData):
    # @TODO : 이미지를 로드하는 부분 
    try:
        device = 'cuda:0' if torch.cuda.is_available() else "cpu"
        masked_img, mask = predict(data.image_path, encoder, decoder, device)
        # @TODO : masked_img를 입력으로 사용하는 Classification
        color = "#800000"
        type = 4
        isBlood = True
        result = {"poo_type" : type, "poo_color" : color, "poo_isBlood" : isBlood}
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
"""
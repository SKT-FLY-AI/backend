FROM python:3.10

# 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && apt-get clean \
    apt-get install -y openssh-client

# 작업 디렉토리 설정
WORKDIR /app

# 현재 디렉토리의 모든 파일을 Docker 컨테이너의 /app 디렉토리로 복사
COPY . /app

# Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 실행 명령어
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


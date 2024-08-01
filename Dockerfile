FROM python:3.10

COPY ./src /src
WORKDIR /src

RUN pip install fastapi uvicorn

EXPOSE 80

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]

# Cmd 순서
# 1. docker build -t {이미지명} .
# 2. docker run --network=host -it --name {컨테이너명지정} -d -p 9090:80 {이미지명}
# 3. ex) docker run --name fastapi -it --network=host -d --rm -p 8080:80 fastapi
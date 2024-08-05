from fastapi import FastAPI, Query
from typing import List

app = FastAPI()

# 샘플 데이터 예시일 뿐 수정
items = [
    {"id": 1, "name": "Apple"},
    {"id": 2, "name": "Banana"},
    {"id": 3, "name": "Cherry"},
    {"id": 4, "name": "Date"},
    {"id": 5, "name": "Elderberry"},
]

@app.get("/search", response_model=List[dict])
def search_items(query: str = Query(..., min_length=1)):
    results = [item for item in items if query.lower() in item["name"].lower()] #경로 수정
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# 
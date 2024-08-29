import json
from openai import OpenAI
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from typing import List
import asyncio
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from database import get_db
from models import Image, ChatLog
from datetime import datetime
import os
from schemas import ChatLogResponse
# langchain model과의 통합
from langchain_openai import ChatOpenAI
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain, LLMChain
from database import add_vectorDB
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate,  HumanMessagePromptTemplate
from langchain.memory import ConversationBufferWindowMemory

load_dotenv()

router = APIRouter()

# .env 파일에서 API 키를 가져오기
api_key = os.getenv("OPENAI_API_KEY")

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=api_key)
def make_templete():
    #! 6. prompt template 정의
    chat_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(
            "당신은 필요한 말만 하는, 강아지 대변에 특화된 수의사입니다."
        ),
        HumanMessagePromptTemplate.from_template(
            """
            나한테 우리 강아지 건강 상태를 파악하기 위해서, 
            Chroma DB에 저장되어있는 문서를 기반으로,
            {poo_color}를 갖고 있는 {poo_type}형태의 대변에 대한 분석 결과를 바탕으로 건강상태를 분석하기 위한 질문을 한가지 던져줘.
            """
        )
    ])
    return chat_prompt

def init_chatbot(key):
    """
    대변 모양, 색깔 받아서 Langchain 모듈 생성, 그에 대한 첫 질문 반환
    :return: langchain_model, 첫 번째 질문
    """
    data_list = ["vector_store/Dog_Stool_Analysis.pdf"]
    for data_path in data_list:
        vector_index = add_vectorDB(data_path)
    retriever = vector_index.as_retriever(
        search_type="similarity", # Cosine Similarity
        search_kwargs={
            "k": 3, # Select top k search results
        } 
    )
    # LLM 초기화
    gptai = ChatOpenAI(api_key=key, temperature=0.7, model="gpt-4", max_tokens=1000)
    chat_prompt = make_templete()
    llm_chain = LLMChain(llm=gptai, prompt=chat_prompt)

    return llm_chain, retriever

# ChatOpenAI와 검색해주는애 반환
llm_chain, retriever = init_chatbot(api_key)

class ChatRequest(BaseModel):
    user_id: int
    message: str
    poo_color: str
    poo_type: str
    image_id: int  # 추가된 필드

# async def gpt_stream_response(poo_color: list, poo_type: str, message: str, past_messages: List[dict], db: Session, user_id: int, image_id: int):
#     count = 0
#     try:
#         count += 1
#         # 모델 실행 및 첫 질문 생성
#         initial_response = llm_chain.invoke({
#             "poo_type": poo_type,
#             "poo_color": poo_color
#         })
#         # 대변 색/모양 전달, 미리 설정한 프롬프트를 통해 첫 질문 생성
#         first_question = initial_response['text']
#         # 메모리 버퍼 생성
#         memory = ConversationBufferWindowMemory(memory_key="chat_history", k=10, output_key="answer", return_messages=True)
#         # ConversationalRetrievalChain allows to seamlessly add historical context or memory to chain.
#         rag_chain = ConversationalRetrievalChain.from_llm(
#             ChatOpenAI(api_key=api_key, temperature=0, model="gpt-4"), 
#             retriever=retriever,
#             chain_type="stuff", 
#             memory=memory,
#             return_source_documents=True
#         )

#         poo_color = json.dumps(poo_color)
#         first_poo_info = {
#             "role": "user",
#             "content": f"대변 모양: {poo_type} / 대변 색상: {poo_color}"
#         }
#         first_question = {"role": "assistant", "content": first_question}
#         # 1. 대변 정보 추가 (human)
#         memory.chat_memory.add_user_message(first_poo_info["content"])
#         # 2. 첫 번째 질문 추가 (ai)
#         memory.chat_memory.add_ai_message(first_question["content"])
#         # 3. 그에 대한 답변 (human)
#         memory.chat_memory.add_user_message(message)
        
#         # 사용자 메시지를 ChatLog에 저장
#         user_log = ChatLog(
#             user_id=user_id,
#             role='user',
#             message=message,
#             timestamp=datetime.now(),
#             poo_color=poo_color,
#             poo_type=poo_type,
#             image_id=image_id  # image_id 저장
#         )
#         db.add(user_log)
#         db.commit()
#         if count == 2:
#             first_poo_info = [{"role" : "user", "content" : f"대변 모양: {poo_type} / 대변 색상: {poo_color}"},
#                             {"role" : "assistant", "content" : first_question}]
#             messages = memory.chat_memory.messages
#             print(messages)
#             messages_for_gpt = []
#             for message in messages:
#                 type = "user" if message.type == "human" else "assistant"
#                 messages_for_gpt.append({"role" : type, "content" : message.content})
#             # 1. 대변 정보 + 2.과거 내역 + 3. 답변 내용
#             # 1단계 : RAG 체인을 사용해 관련 문서 검색
#             stream = client.chat.completions.create(
#                 model="gpt-3.5-turbo",
#                 messages=messages_for_gpt,
#                 stream=True,
#             )
#             assistant_response = ""
#             for chunk in stream:
#                 content = chunk.choices[0].delta.content
#                 if content:
#                     assistant_response += content
#                     yield content
#                     await asyncio.sleep(0)
                    
#             # GPT 응답을 ChatLog에 저장
#             assistant_log = ChatLog(
#                 user_id=user_id,
#                 role='assistant',
#                 message=assistant_response,
#                 timestamp=datetime.now(),
#                 poo_color=poo_color,
#                 poo_type=poo_type,
#                 image_id=image_id  # image_id 저장
#             )
#             db.add(assistant_log)
#             db.commit()
            
#         else:
#             retrieved_docs = rag_chain({
#                 "question": message,
#                 "chat_history": memory.chat_memory.messages
#             })
            
#             # 2단계 : 검색된 문서를 LLMChain에 전달하여 최종 응답 생성
#             # 문서 검색 결과가 있으면 해당 내용을 바탕으로 답변 생성 / 없으면 LLM model로 가버려잇.
#             if 'source_documents' in retrieved_docs and retrieved_docs['source_documents']:
#                 context = "\n".join([doc.page_content for doc in retrieved_docs['source_documents']])

#                 stream = llm_chain.invoke({
#                     "poo_type": poo_type,
#                     "poo_color": poo_color,
#                     "context": context,
#                     "question": message
#                 })

#             else:
#                 # 문서 검색 결과가 없으면 LLMChain을 사용해 질문에 대한 일반적인 답변 생성
#                 stream = llm_chain.invoke({
#                     "poo_type": poo_type,
#                     "poo_color": poo_color,
#                     "context": "관련 문서가 저장되어 있지 않습니다. 강아지 대변과 관련한 정보로 수의사처럼 상담을 진행하되 간단하게 질문을 하나씩 던지세요.",    # LLMChain한테 던지는 말.
#                     "question": message
#                 })
            
#             assistant_response = ""
#             for chunk in stream['text']:
#                 content = chunk
#                 if content:
#                     assistant_response += content
#                     yield content
#                     await asyncio.sleep(0)

#             # GPT 응답을 ChatLog에 저장
#             assistant_log = ChatLog(
#                 user_id=user_id,
#                 role='assistant',
#                 message=assistant_response,
#                 timestamp=datetime.now(),
#                 poo_color=poo_color,
#                 poo_type=poo_type,
#                 image_id=image_id  # image_id 저장
#             )
#             db.add(assistant_log)
#             db.commit()

#     except Exception as e:
#         # 예외가 발생하면 클라이언트에 오류 메시지를 보냄
#         yield f"\n[Error]: {str(e)}\n"

async def gpt_stream_response_mini(poo_color: str, poo_type: str, message: str, past_messages: List[dict], db: Session, user_id: int, image_id: int):
    try:
        chat_prompt = [
            {"role": "system", "content": "당신은 필요한 말만 하는, 강아지 대변에 특화된 수의사입니다."},
            {
                "role": "user",
                "content": f"""
                답변을 "분석: 분석내용, 색상: poo_color를 6가지 색으로 변환한 리스트(색상, 확률)"의 형태로 줘.
                6가지 색은 다음과 같아 : "갈색, 검은색, 빨간색, 흰색, 녹색, 노랑색" 으로 poo_color의 색상 코드값을 변환해줘.
                분석내용은 
                나한테 우리 강아지 건강 상태를 파악하기 위해서, 
                FAISS 내 저장되어있는 문서를 기반으로
                {poo_color}를 갖고 있는 {poo_type}형태의 대변에 대해 간단하게 10자 이내로 알려줘. 예를들면 "묽고 초록의 변입니다. 주의가 필요합니다." 처럼 줘.
                """
            }
        ]
        
        messages = chat_prompt + past_messages + [{"role": "user", "content": message}]
        
        # 사용자 메시지를 ChatLog에 저장
        user_log = ChatLog(
            user_id=user_id,
            role='user',
            message=message,
            timestamp=datetime.now(),
            poo_color=poo_color,
            poo_type=poo_type,
            image_id=image_id  # image_id 저장
        )
        db.add(user_log)
        db.commit()

        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            stream=True,
        )

        assistant_response = ""
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                assistant_response += content
                yield content
                await asyncio.sleep(0)

        # GPT 응답을 ChatLog에 저장
        assistant_log = ChatLog(
            user_id=user_id,
            role='assistant',
            message=assistant_response,
            timestamp=datetime.now(),
            poo_color=poo_color,
            poo_type=poo_type,
            image_id=image_id  # image_id 저장
        )
        db.add(assistant_log)
        db.commit()

    except Exception as e:
        # 예외가 발생하면 클라이언트에 오류 메시지를 보냄
        yield f"\n[Error]: {str(e)}\n"

# @router.post("/poopt")
# async def chat_with_gpt_poopt(request: ChatRequest, db: Session = Depends(get_db)):
#     try:
#         # 프롬프트에 필요한 변수들 ChatRequest에서 가져오기
#         poo_color = request.poo_color
#         poo_type = request.poo_type
#         user_id = request.user_id
#         image_id = request.image_id

#         # 초기 프롬프트에 대한 응답을 스트리밍으로 보냅니다.
#         return StreamingResponse(gpt_stream_response(poo_color, poo_type, request.message, [], db, user_id, image_id), media_type="text/plain")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))



# 더미 응답 시나리오 설정
scenario_responses = {
    1: "최근에 검은색 계열의 음식을 먹거나 사료를 변경한 적이 있나요?",
    2: "반려견이 식욕이 줄거나, 활동력이 저하되었다고 생각하시나요?",
    3: "반려견의 대변 색깔이 검정색으로 변하고, 식욕 감소 및 활동력 저하가 관찰되는 경우, 여러 가지 건강 문제를 의심해 볼 수 있습니다. 최근에 먹인 음식이나 간식이 무엇인지, 평소 식단과의 차이를 확인해두는 것도 중요합니다. 반려견의 건강이 염려되므로 가능한 한 빨리 수의사와 상담하시길 권장드립니다."
}
count = 0
async def gpt_stream_response(poo_color: str, poo_type: str, message: str, past_messages: List[dict], db: Session, user_id: int, image_id: int):
    global count
    try:
        count += 1
        scenario = None

        # 시나리오에 맞게 고정된 AI 답변 제공
        if count == 1:
            scenario = scenario_responses[1]
        elif count == 2:
            # 2번 질문
            scenario = scenario_responses[2]
        else:
            # 3번 답변
            scenario = scenario_responses[3]
                # GPT 응답을 ChatLog에 저장
        
        assistant_log = ChatLog(
            user_id=user_id,
            role='assistant',
            message=scenario,
            timestamp=datetime.now(),
            poo_color=poo_color,
            poo_type=poo_type,
            image_id=image_id  # image_id 저장
        )
        db.add(assistant_log)
        db.commit()
        
        assistant_response = ""
        for chunk in scenario:
            content = chunk
            if content:
                assistant_response += content
                yield content
                await asyncio.sleep(0)
        
        user_log = ChatLog(
            user_id=user_id,
            role='user',
            message=message,
            timestamp=datetime.now(),
            poo_color=poo_color,
            poo_type=poo_type,
            image_id=image_id  # image_id 저장
        )
        db.add(user_log)
        db.commit()
    
    except Exception as e:
        # 예외가 발생하면 클라이언트에 오류 메시지를 보냄
        yield f"\n[Error]: {str(e)}\n"

@router.post("/poopt")
async def chat_with_gpt_poopt(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        # 프롬프트에 필요한 변수들 ChatRequest에서 가져오기
        poo_color = request.poo_color
        poo_type = request.poo_type
        user_id = request.user_id
        image_id = request.image_id
        
        # 초기 프롬프트에 대한 응답을 스트리밍으로 보냅니다.
        return StreamingResponse(gpt_stream_response(poo_color, poo_type, request.message, [], db, user_id, image_id), media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/poopt_mini")
async def chat_with_gpt_poopt_mini(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        # 프롬프트에 필요한 변수들 ChatRequest에서 가져오기
        poo_color = request.poo_color
        poo_type = request.poo_type
        user_id = request.user_id
        image_id = request.image_id

        print(f"Received Request - user_id: {user_id}, poo_color: {poo_color}, poo_type: {poo_type}")  # 로그 추가

        # 초기 프롬프트에 대한 응답을 스트리밍으로 보냅니다.
        return StreamingResponse(
            gpt_stream_response_mini(poo_color, poo_type, request.message, [], db, user_id, image_id), 
            media_type="text/plain"
        )
    except Exception as e:
        print(f"Exception occurred: {str(e)}")  # 에러 발생 시 출력
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/chatlogs/{user_id}", response_model=List[ChatLogResponse])
async def get_chat_logs_by_user_id(user_id: int, db: Session = Depends(get_db)):
    """
    주어진 user_id에 해당하는 챗로그를 불러오는 API 엔드포인트
    """
    # user_id에 맞는 ChatLog 조회
    chat_logs = db.query(ChatLog).filter(ChatLog.user_id == user_id).order_by(ChatLog.timestamp.desc()).all()

    # 챗로그가 없을 경우 404 에러 발생
    if not chat_logs:
        raise HTTPException(status_code=404, detail="No chat logs found for the user")

    # 조회된 챗로그 반환
    return chat_logs
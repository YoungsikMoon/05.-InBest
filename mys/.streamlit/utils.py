import streamlit as st

from langchain_core.messages import ChatMessage
from langchain_community.chat_models import ChatOllama
from langchain_ollama.llms import OllamaLLM

from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
import os

# llm = ChatOllama(model= 'MoonYoungSik') # 여러가지 속성 값이 나옴.
# llm = OllamaLLM(model= 'MoonYoungSik') # 출력값이 답변만 나옴.
llm = ChatOllama(model= 'gemma2') # ollama 자체 gemma2-9b 입니다. 질의 응답 수준이 따로 설정한것 없이 SYSTEM 설정이 잘되어있는 듯 함.
output_parser = StrOutputParser()
store = {}

def start_streamlit(page_title="MoonYoungSik"):
    st.set_page_config(page_title=page_title,  page_icon="💬")
    st.title("💬"+ page_title+" Test")

def make_session():
    if "messages" not in st.session_state: #세션이 없으면 만들어라
        st.session_state["messages"] = []

def print_messages():
    # 세션이 있고 세션에 메세지가 있다면 이전 대화 기록을 출력
    if "messages" in st.session_state and len(st.session_state["messages"]) > 0:
        # for role, message in st.session_state["messages"]:
        #     st.chat_message(role).write(message)
        for chat_message in st.session_state["messages"]:
            st.chat_message(chat_message.role).write(chat_message.content)

# 세션 ID를 기반으로 세션 기록을 가져오는 함수
def get_session_history(session_ids: str) -> BaseChatMessageHistory:
    print(session_ids)
    if session_ids not in store: # 세션 ID가 store에 없는 경우
        # 새로운 ChatMessageHistory 객체를 생성하여 store에 저장
        store[session_ids] = ChatMessageHistory()
    return store[session_ids] # 해당 세션 ID에 대한 세션 기록 변환

def input_output(): #User input 활성화 -> AI 응답 출력
    if user_input := st.chat_input("메세지를 입력해 주세요."): # 예시 메시지
        # 사용자가 입력한 내용
        st.chat_message("user").write(f"{user_input}") # 유저의 메세지를 출력
        st.session_state["messages"].append(ChatMessage(role="user", content=user_input))
        
        prompt = ChatPromptTemplate.from_messages(
            [
                # (
                #     "system", 
                #     # "시스템은 {ability} 전문가입니다."
                #     "간결하게 사전 형식으로 설명해주세요."
                # ),
                # 대화 기록을 변수로 사용, history가 MessageHistory의 key가 됨.
                MessagesPlaceholder(variable_name="history"),
                ("user", "{question}"), #사용자 질문 입력
            ]
        )

        chain = prompt | llm | output_parser

        chain_with_memory = (
            RunnableWithMessageHistory( # RunnableWithMessageHistory 객체 생성
                chain, # 실행할 런어블 객체
                get_session_history, # 세션 기록을 가져오는 함수
                history_messages_key="history", # 기록 메세지의 key
                input_messages_key="question", # 사용자 질문의 key
            )
        )

        msg = chain_with_memory.invoke(
            # 프롬프트 변수 할당
            # {"ability": "주식", "question" : user_input,},
            {"question" : user_input,},
            # 세션 정보 설정
            config={"configurable": {"session_id": "abc123"}}
        )

        # AI의 답변
        with st.chat_message("assistant"): # 어시스턴트 
            st.write(msg) # 어시스턴트 답변
            # st.session_state["messages"].append(("assistant", msg))
            st.session_state["messages"].append(ChatMessage(role="assistant", content=msg))

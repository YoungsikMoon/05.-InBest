# 스트림릿
import streamlit as st

# 모델 불러오는 방식 2가지
from langchain_community.chat_models import ChatOllama
from langchain_ollama.llms import OllamaLLM

# 프롬프트 관련
from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 대화 기록 관련
from langchain_core.messages import ChatMessage
from langchain_core.prompts import MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# 스트리밍 기능 관련
from langchain_core.callbacks.base import BaseCallbackHandler

import os

def start_streamlit(page_title="MoonYoungSik"): 
    # 페이지 기본 셋팅
    st.set_page_config(page_title=page_title,  page_icon="💬")
    st.title("💬"+ page_title+" Test")
    # 사이드바 생성
    with st.sidebar:
        st.session_state.session_id = st.text_input("사용자명", value="문영식")
        clear_btn = st.button("대화기록 초기화")
        if clear_btn:
            # 해당 session_id에 대한 대화 기록만 초기화
            if st.session_state.session_id in st.session_state["store"]:
                del st.session_state["store"][st.session_state.session_id]
            st.session_state["messages"] = []  # 전체 메시지 초기화
            st.rerun  # 변경 사항 반영을 위해 rerun 호출

def service_init(): 
    # 세션 초기화
    if "messages" not in st.session_state: # 대화 기록 출력용
        st.session_state["messages"] = []

    if "store" not in st.session_state:  # 대화 기록 참고용
        st.session_state["store"] = dict()

def print_messages(): 
    # 챗봇은 질문을 한 번 하고 답변을 할때마다 새로고침이 일어나는 특성이 있다.
    # 이전 대화기록을 출력하기 위해 messages 리스트가 필요하다.
    # 세션이 있고 세션에 메세지가 있다면 이전 대화 기록을 출력
    if "messages" in st.session_state and len(st.session_state["messages"]) > 0:
        for chat_message in st.session_state["messages"]:
            st.chat_message(chat_message.role).write(chat_message.content)

def get_session_history(session_ids: str) -> BaseChatMessageHistory:
    # 세션 ID를 기반으로 세션 기록을 가져오는 함수
    if session_ids not in st.session_state["store"]:
        st.session_state["store"][session_ids] = ChatMessageHistory()
    return st.session_state["store"][session_ids] # 해당 세션 ID에 대한 세션 기록 변환

class StreamHandler(BaseCallbackHandler): 
    # AI 답변 생성 방식 바꾸기 : 전체 토큰 생성되고 나오는 방식 -> 토큰 생성될 때마다 출력 방식
    def __init__(self, container, initial_text=""):
        self.container = container
        self.text = initial_text
    def on_llm_new_token(self, token:str, **kwargs) -> None:
        self.text += token
        self.container.markdown(self.text)

# # llm = ChatOllama(model= 'MoonYoungSik') # 여러가지 속성 값이 나옴.
# # llm = OllamaLLM(model= 'MoonYoungSik') # 출력값이 답변만 나옴.
# # llm = ChatOllama(model= 'gemma2') # ollama 자체 gemma2-9b 입니다. 질의 응답 수준이 따로 설정한것 없이 SYSTEM 설정이 잘되어있는 듯 함.
output_parser = StrOutputParser()
def input_output():
    # 유저의 입력과 출력까지 전반적인 코드
    if user_input := st.chat_input("메세지를 입력해 주세요."):
        st.chat_message("user").write(f"{user_input}") # 유저의 메세지를 출력
        st.session_state["messages"].append(ChatMessage(role="user", content=user_input)) # 유저의 메세지를 messages 리스트에 담는다. print_messages() 함수를 보면 이유를 알 수 있다.

        # AI의 답변
        with st.chat_message("assistant"): 
            # 스트림 핸들러와 함께 AI 모델 설정
            stream_handler = StreamHandler(st.empty())
            # llm = ChatOllama(model= 'gemma2', streaming=True, callbacks=[stream_handler])
            llm = ChatOllama(model='gemma2', streaming=True, callbacks=[stream_handler], max_input_tokens=None, max_output_tokens=None)

            # 프롬프트 템플릿 생성
            prompt = ChatPromptTemplate.from_messages([
                ("system", "이 시스템은 한국인 '{username}' 님을 대상으로 답변합니다. 그리고 {ability} 분석을 잘하고 투자 조언도 잘합니다."),
                MessagesPlaceholder(variable_name="history"),
                ("user", "{question}"),
            ])

            # 프롬프트와 AI 모델을 연결
            chain = prompt | llm | output_parser

            # 메세지 기록을 활용한 체인 객체 생성
            chain_with_memory = RunnableWithMessageHistory( 
                chain, # 체인
                get_session_history, # 세션 기록을 가져오는 함수
                history_messages_key="history", # 기록 메세지의 key
                input_messages_key="question", # 사용자 질문의 key
            )

            # AI 응답 생성
            response = chain_with_memory.invoke(
                {"ability": "주식", "username": st.session_state.session_id ,"question": user_input},
                config={"configurable": {"session_id": st.session_state.session_id}}
            )
            # 응답을 메시지에 추가
            st.session_state["messages"].append(ChatMessage(role="assistant", content=response))
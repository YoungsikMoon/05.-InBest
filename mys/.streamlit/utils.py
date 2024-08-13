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

# 주가 데이터 리더
import FinanceDataReader as fdr
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
import datetime
import os

# 주식 종목 데이터셋
df_krx = fdr.StockListing('KRX')
df_krx = df_krx[['Code','Name']]

def start_streamlit(page_title="MoonYoungSik"): 
    # 페이지 기본 셋팅
    st.set_page_config(page_title=page_title,  page_icon="💰📉📈🤑")
    st.title("💰📉📈🤑"+ page_title)
    # 사이드바 생성
    with st.sidebar:
        # 사용자 특화 시키기 위한 이름 받기 (로그인 기능을 대체하기 위함)
        st.session_state.session_id = st.text_input("사용자명", value="")
        # KRX 상장 주식 데이터 가져오기
        view_krx = st.button("주식 목록 보기")
        if view_krx:
            # Streamlit 애플리케이션 제목
            st.title('주식 목록')
            st.dataframe(df_krx, width=400, height=200)
        # 주식 데이터 조회
        st.session_state.code = st.text_input(
            '종목코드', 
            value='',
            placeholder='종목코드를 입력해 주세요'
        )
        current_year = datetime.datetime.now().year
        current_month = datetime.datetime.now().month
        current_day = datetime.datetime.now().day
        st.session_state.start_date = st.date_input(
            "조회 시작일을 선택해 주세요",
            datetime.datetime(current_year, current_month, current_day-1)
        )
        st.session_state.end_date = st.date_input(
            "조회 종료일을 선택해 주세요",
            datetime.datetime(current_year, current_month, current_day)
        )
        if st.session_state.start_date > st.session_state.end_date:
            st.error("시작일은 종료일보다 이전이어야 합니다.")

        # 세션 초기화
        clear_btn = st.button("대화기록 초기화")
        if clear_btn:
            # 해당 session_id에 대한 대화 기록만 초기화
            if st.session_state.session_id in st.session_state["store"]:
                del st.session_state["store"][st.session_state.session_id]
            st.session_state["messages"] = []  # 전체 메시지 초기화
            # 입력 필드 초기화
            st.session_state.code = ''  # 종목코드 초기화
            st.session_state.start_date = datetime.datetime(current_year, current_month, current_day-1)  # 시작일 초기화
            st.session_state.end_date = datetime.datetime(current_year, current_month, current_day)  # 종료일 초기화
            # 변경 사항 반영을 위해 rerun 호출
            st.rerun  

        def prepare_price_data(df):
            """가격 데이터를 정리하여 DataFrame으로 반환하는 함수"""
            return pd.DataFrame({
                '시가': df['Open'],
                '종가': df['Close'],
                '고가': df['High'],
                '저가': df['Low']
            })

        def display_chart(title, data):
            """차트를 표시하는 함수"""
            st.header(title)
            st.line_chart(data)

        if st.session_state.start_date and st.session_state.end_date and st.session_state.code:
            try:
                df = fdr.DataReader(st.session_state.code, st.session_state.start_date, st.session_state.end_date)
                df_sorted = df.sort_index(ascending=True)

                price_data = prepare_price_data(df_sorted)
                volume = df_sorted['Volume']
                change = df_sorted['Change']

                st.title(f"종목코드 : {st.session_state.code}")
                display_chart(f"시가 종가 고가 저가", price_data)
                display_chart("거래량", volume)
                display_chart("변동폭", change)

            except Exception as e:
                st.error(f"데이터를 가져오는 데 오류가 발생했습니다: {e}")


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
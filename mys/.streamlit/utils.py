import streamlit as st

# 사이드바 관련
import datetime
import pandas as pd
import sidebar_sctock
import importlib
# importlib.reload(sidebar_sctock)

# LLM 생성과 저장 관련
from langchain_community.chat_models import ChatOllama
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import ChatMessage
from langchain_core.callbacks.base import BaseCallbackHandler

# 챗 기억 저장 관련
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory


import sidebar_sctock
import importlib
# importlib.reload(sidebar_sctock)

def start_streamlit(page_title="MoonYoungSik"):
    st.set_page_config(
        page_title=page_title, 
        page_icon="📈", 
        # page_icon="💰📉📈🤑", 
        layout='wide',
        initial_sidebar_state="expanded",
        menu_items={
        'About': "문영식 : 010-9008-4362"
        }
    )
    st.markdown("""<style> div[data-testid="stToolbar"] { display: none;} </style>""", unsafe_allow_html=True)
    st.title(f"💰📉📈🤑 {page_title}")
    st.session_state.session_id = ""


def side_bar():
    with st.sidebar:
        # 사용자 생성 입력
        st.session_state.session_id = st.text_input("사용자 추가", value="")

        if st.session_state.session_id:
            if not st.session_state["user_df"]["사용자명"].str.contains(st.session_state.session_id).any():
                creation_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_user = pd.DataFrame([[st.session_state.session_id, creation_date]], columns=["사용자명", "생성일자"])
                st.session_state["user_df"] = pd.concat([st.session_state["user_df"], new_user], ignore_index=True)
        
        # 데이터프레임 표시
        selected_user = st.selectbox("사용자 선택", st.session_state["user_df"]["사용자명"].tolist())
        if selected_user:
            st.session_state.session_id = selected_user  # 선택한 사용자명으로 session_id 업데이트

        st.dataframe(st.session_state["user_df"], width=400, height=150)
        
        if st.button("현재 사용자 대화기록 지우기"):
            if st.session_state.session_id in st.session_state["store"]:
                del st.session_state["store"][st.session_state.session_id]
            st.rerun()

        sidebar_sctock.about_stock()
        

def session_init():
    if "store" not in st.session_state:
        st.session_state["store"] = {}
    
    if "user_df" not in st.session_state:
        st.session_state["user_df"] = pd.DataFrame(columns=["사용자명", "생성일자"])
    
    session_id = st.session_state.session_id
    if session_id not in st.session_state["store"]:
        st.session_state["store"][session_id] = {
            "messages": [],
            "history": ChatMessageHistory(),
            "advice_df": pd.DataFrame(columns=['stock_name', 'stock_advice'])
        }

def print_messages():
    session_id = st.session_state.session_id
    if session_id in st.session_state["store"]:
        messages = st.session_state["store"][session_id]["messages"]
        for chat_message in messages:
            st.chat_message(chat_message.role).write(chat_message.content)

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    return st.session_state["store"][session_id]["history"]

class StreamHandler(BaseCallbackHandler):
    def __init__(self, container, initial_text=""):
        self.container = container
        self.text = initial_text

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.text += token
        self.container.markdown(self.text)

def llm_init(user_input):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "이 시스템이름은 InBest입니다. 한국인 '{username}' 님을 대상으로 답변합니다. 그리고 {ability} 분석을 잘하고 투자 조언도 잘합니다."),
        MessagesPlaceholder(variable_name="history"),
        ("user", "{question}"),
    ])
    
    stream_handler = StreamHandler(st.empty())
    output_parser = StrOutputParser()
    llm = ChatOllama(model='gemma2', streaming=True, callbacks=[stream_handler])

    session_id = st.session_state.session_id
    chain_with_memory = RunnableWithMessageHistory(
        prompt | llm | output_parser,
        get_session_history,
        history_messages_key="history",
        input_messages_key="question"
    )
    
    response = chain_with_memory.invoke(
        {"ability": "주식", "username": session_id, "question": user_input},
        config={"configurable": {"session_id": session_id}}
    )
    
    st.session_state["store"][session_id]["messages"].append(ChatMessage(role="assistant", content=response))

def chatbot():
    session_id = st.session_state.session_id
    session_init()
    if user_input := st.chat_input("메세지를 입력해 주세요."):
        st.chat_message("user").write(f"{user_input}")
        st.session_state["store"][session_id]["messages"].append(ChatMessage(role="user", content=user_input))
        with st.chat_message("assistant"):
            llm_init(user_input)
import streamlit as st
from langchain_core.messages import ChatMessage

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

def input_output():
    # 유저 입력과 어시스턴트 출력
    if user_input := st.chat_input("메세지를 입력해 주세요."): # 예시 메시지
        # 사용자가 입력한 내용
        st.chat_message("user").write(f"{user_input}") # 유저의 메세지를 출력
        # st.session_state["messages"].append(("user", user_input))
        st.session_state["messages"].append(ChatMessage(role="user", content=user_input))
        
        # AI의 답변
        with st.chat_message("assistant"): # 어시스턴트 
            msg = f"당신이 입력한 내용 : {user_input}"
            st.write(msg) # 어시스턴트 답변
            # st.session_state["messages"].append(("assistant", msg))
            st.session_state["messages"].append(ChatMessage(role="assistant", content=msg))


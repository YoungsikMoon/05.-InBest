import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import datetime
import plotly.graph_objects as go
import plotly.express as px

from langchain_community.chat_models import ChatOllama
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import ChatMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.callbacks.base import BaseCallbackHandler

# 주식 종목 데이터셋 로드
df_krx = fdr.StockListing('KRX')[['Code', 'Name']]

def start_streamlit(page_title="MoonYoungSik"):
    st.set_page_config(page_title=page_title, page_icon="💰📉📈🤑")
    st.title(f"💰📉📈🤑 {page_title}")
    st.session_state.session_id = ""

def side_bar():
    with st.sidebar:
        st.session_state.session_id = st.text_input("사용자명", value="")
        if st.session_state.session_id:
            # Check if the username already exists in the dataframe
            if not st.session_state["user_df"]["사용자명"].str.contains(st.session_state.session_id).any():
                creation_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_user = pd.DataFrame([[st.session_state.session_id, creation_date]], columns=["사용자명", "생성일자"])
                st.session_state["user_df"] = pd.concat([st.session_state["user_df"], new_user], ignore_index=True)
        
        st.dataframe(st.session_state["user_df"], width=400, height=150)
        
        if st.button("대화기록 초기화"):
            if st.session_state.session_id in st.session_state["store"]:
                del st.session_state["store"][st.session_state.session_id]
            st.rerun()
        
        about_stock()
        
def about_stock():
    st.write('주식 목록')
    st.dataframe(df_krx, width=400, height=200)

    st.session_state.code = st.text_input('종목코드', value='', placeholder='종목코드를 입력해 주세요')
    st.session_state.start_date = st.date_input("조회 시작일을 선택해 주세요", datetime.datetime.now() - datetime.timedelta(days=30))
    st.session_state.end_date = st.date_input("조회 종료일을 선택해 주세요", datetime.datetime.now())

    if st.session_state.start_date > st.session_state.end_date:
        st.error("조회 날짜가 올바르지 않습니다.")

    if st.session_state.start_date and st.session_state.end_date and st.session_state.code:
        try:
            # 데이터 가져오기
            df = fdr.DataReader(st.session_state.code, st.session_state.start_date, st.session_state.end_date).sort_index(ascending=True)
            st.title(f"종목코드: {st.session_state.code}")

            # 이동 평균선 (SMA) 계산
            # 사용자 입력을 받기 위한 필드 추가 (이동 평균선 기간)
            sma_period = st.number_input("이동 평균선 기간 (일수)", min_value=1, value=1)
            df['SMA'] = df['Close'].rolling(window=sma_period).mean()  # 이동 평균
            # 이동 평균선 차트 생성
            def plot_sma_chart(df):
                sma_fig = go.Figure()
                sma_fig.add_trace(go.Scatter(
                    x=df.index,
                    y=df['SMA'],
                    mode='lines',
                    name=f'{sma_period}일 이동 평균',
                    line=dict(color='orange'),
                    hoverinfo='text',
                    text=[f'날짜: {index.strftime("%Y-%m-%d")}<br>가격: {sma:.2f}' for index, sma in zip(df.index, df['SMA'])]
                ))
                sma_fig.update_layout(
                    title="이동 평균선 차트",
                    title_x=0,
                    xaxis_title='날짜',
                    yaxis_title='가격',
                    xaxis=dict(showticklabels=False),
                    plot_bgcolor='rgba(0,0,0,0)',
                )
                return sma_fig
            st.plotly_chart(plot_sma_chart(df))

            # 볼린저 밴드 차트 생성
            df['UpperBand'] = df['SMA'] + (df['Close'].rolling(window=sma_period).std() * 2)
            df['LowerBand'] = df['SMA'] - (df['Close'].rolling(window=sma_period).std() * 2)
            def plot_bollinger_chart(df):
                bollinger_fig = go.Figure(data=[
                    go.Candlestick(
                        x=df.index,
                        open=df['Open'],
                        high=df['High'],
                        low=df['Low'],
                        close=df['Close'],
                        name='캔들봉',
                        hoverinfo='text',
                        text=[f'날짜: {index.strftime("%Y-%m-%d")}<br>시가: {open_}<br>종가: {close_}' for index, open_, close_ in zip(df.index, df['Open'], df['Close'])]
                    ),
                    go.Scatter(
                        x=df.index,
                        y=df['UpperBand'],
                        mode='lines',
                        name='상단 볼린저 밴드',
                        line=dict(color='red', dash='dash'),
                        hoverinfo='text',
                        text=[f'날짜: {index.strftime("%Y-%m-%d")}<br>상단 밴드: {upper:.2f}' for index, upper in zip(df.index, df['UpperBand'])]
                    ),
                    go.Scatter(
                        x=df.index,
                        y=df['LowerBand'],
                        mode='lines',
                        name='하단 볼린저 밴드',
                        line=dict(color='green', dash='dash'),
                        hoverinfo='text',
                        text=[f'날짜: {index.strftime("%Y-%m-%d")}<br>하단 밴드: {lower:.2f}' for index, lower in zip(df.index, df['LowerBand'])]
                    )
                ])
                bollinger_fig.update_layout(
                    xaxis_rangeslider_visible=False,
                    title="볼린저 밴드 차트",
                    title_x=0,
                    xaxis_title='날짜',
                    yaxis_title='가격',
                    xaxis=dict(showticklabels=False),
                    plot_bgcolor='rgba(0,0,0,0)',
                )
                return bollinger_fig
            st.plotly_chart(plot_bollinger_chart(df))

            # 거래량 차트
            def plot_volume_chart(df):
                volume_fig = go.Figure()
                volume_colors = ['green' if df['Volume'].iloc[i] >= df['Volume'].iloc[i-1] else 'red' for i in range(1, len(df['Volume']))]
                volume_colors = ['blue'] + volume_colors  # 첫 번째 값은 기본 색상으로 설정
                volume_fig.add_trace(go.Bar(
                    x=df.index,
                    y=df['Volume'],
                    name='거래량',
                    marker_color=volume_colors,
                    hoverinfo='text',
                    text=[f'날짜: {index.strftime("%Y-%m-%d")}<br>거래량: {volume}' for index, volume in zip(df.index, df['Volume'])]
                ))
                volume_fig.update_layout(
                    title_text='거래량 차트',
                    title_x=0,
                    xaxis_title='날짜',
                    yaxis_title='거래량',
                    xaxis=dict(showticklabels=False),
                    xaxis_rangeslider_visible=False,
                    plot_bgcolor='rgba(0,0,0,0)',
                    yaxis=dict(
                        showgrid=True,
                        zeroline=True,
                        zerolinecolor='gray',
                        zerolinewidth=1,
                        title_standoff=10
                    ),
                    margin=dict(l=40, r=40, t=40, b=40)
                )
                return volume_fig
            st.plotly_chart(plot_volume_chart(df))

            # 일일 수익률 계산
            df['Daily Return'] = df['Close'].pct_change()
            def plot_daily_return_chart(df):
                daily_return_fig = go.Figure()
                daily_return_fig.add_trace(go.Bar(
                    x=df.index,
                    y=df['Daily Return'],
                    marker_color=['green' if x >= 0 else 'red' for x in df['Daily Return']],
                    hoverinfo='text',
                    text=[f'날짜: {index.strftime("%Y-%m-%d")}<br>수익률: {x:.2%}' for index, x in zip(df.index, df['Daily Return'])],
                    name='일일 수익률'
                ))
                daily_return_fig.update_layout(
                    title_text='일일 수익률',
                    title_x=0, 
                    xaxis_title='날짜',
                    yaxis_title='수익률',
                    xaxis=dict(showticklabels=False),
                    hovermode='x unified',
                    margin=dict(l=40, r=40, t=40, b=40),
                    plot_bgcolor='rgba(0,0,0,0)',
                )
                return daily_return_fig

            st.plotly_chart(plot_daily_return_chart(df))

        except Exception as e:
            st.error(f"데이터를 가져오는 데 오류가 발생했습니다: {e}")


def session_init():
    if "store" not in st.session_state:
        st.session_state["store"] = {}
    
    if "user_df" not in st.session_state:
        st.session_state["user_df"] = pd.DataFrame(columns=["사용자명", "생성일자"])
    
    session_id = st.session_state.session_id
    if session_id and session_id not in st.session_state["store"]:
        st.session_state["store"][session_id] = {
            "messages": [],
            "history": ChatMessageHistory()
        }

def print_messages():
    session_id = st.session_state.session_id
    if session_id in st.session_state["store"]:
        messages = st.session_state["store"][session_id]["messages"]
        for chat_message in messages:
            st.chat_message(chat_message.role).write(chat_message.content)

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in st.session_state["store"]:
        st.session_state["store"][session_id] = {
            "messages": [],
            "history": ChatMessageHistory()
        }
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
        ("system", "이 시스템은 한국인 '{username}' 님을 대상으로 답변합니다. 그리고 {ability} 분석을 잘하고 투자 조언도 잘합니다."),
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
    session_init()
    session_id = st.session_state.session_id
    if user_input := st.chat_input("메세지를 입력해 주세요."):
        st.chat_message("user").write(f"{user_input}")
        if session_id not in st.session_state["store"]:
            st.session_state["store"][session_id] = {
                "messages": [],
                "history": ChatMessageHistory()
            }
        st.session_state["store"][session_id]["messages"].append(ChatMessage(role="user", content=user_input))
        with st.chat_message("assistant"):
            llm_init(user_input)
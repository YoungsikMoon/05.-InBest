import streamlit as st
import FinanceDataReader as fdr
import datetime
import pandas as pd
import plotly.graph_objects as go


# CSV 파일 읽기
import pandas as pd
def get_news_data(code):
    file_path = '/home/alpaco/mys/projects/news/datas/네이버_뉴스기사/naver_news_origin_duplicates.csv'
    news_df = pd.read_csv(file_path, index_col=False, dtype={'href':str, 'context':str, 'stock':str, 'code':str})
    # 필요한 열 선택 및 특정 코드 필터링
    news_df = news_df[['context', 'stock', 'day', 'code', 'href']]
    news_df = news_df[news_df['code'] == code].reset_index(drop=True)
    # 'day'가 같은 행의 'context' 통합
    news_df = news_df.groupby(['day', 'code'], as_index=False).agg({
        'context': lambda x: ''.join(x),  # context를 순서대로 합치기
        'stock': 'first',                  # 첫 번째 'stock' 값 유지
        'href': lambda x: list(x)          # href를 리스트로 통합
    })
    # 'day' 값을 datetime 형식으로 변환
    news_df['day'] = pd.to_datetime(news_df['day'], format='%Y%m%d').dt.date
    # 'day'를 'yyyy년 m월 d일' 형식으로 변환하고 'context'에 추가
    news_df['context'] = news_df.apply(lambda row: f"{row['day'].year}년 {row['day'].month}월 {row['day'].day}일 {row['stock']}의 통합 기사입니다. {row['context']}", axis=1)
    # 'context' 내용을 순서대로 합쳐서 all_context라는 변수에 저장
    all_context = ' '.join(news_df['context'].tolist())
    # 날짜 오름차순 정렬 후 인덱스 재설정
    news_df = news_df.sort_values(by='day', ascending=True).reset_index(drop=True)
    return news_df, all_context


def stock_advice(code, select_day):
    session_id = st.session_state.session_id
    import utils as ut
    ut.session_init()
    news_df, all_context = get_news_data(code)
    stock_name = news_df.loc[news_df['code'] == st.session_state.code, 'stock'].values[0]
    advice_df = st.session_state["store"][session_id]["advice_df"]

    # 선택한 날짜에 대한 기존 조언 데이터 확인
    existing_advice = advice_df.loc[advice_df['day'] == select_day, 'stock_advice']

    if st.button("뉴스 요약"):
        if existing_advice.empty:
            # Prompt 템플릿 정의
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            from langchain_core.prompts import ChatPromptTemplate
            prompt = ChatPromptTemplate.from_messages([
                ("system", "이 시스템 이름은 InbestService 입니다. {ability} 분석을 잘하고 금융 전문가 입니다. 오늘 date는 {now} 입니다. 한국인 '{username}'님에게 정보를 제공합니다. 단발성 대화입니다."),
                ("user", "{stock} 종목 통합 기사: {all_context}. / 질문 : {question}"),
            ])

            import utils as ut
            stream_handler = ut.StreamHandler(st.empty())
            from langchain_core.output_parsers import StrOutputParser
            output_parser = StrOutputParser()
            from langchain_community.chat_models import ChatOllama
            llm = ChatOllama(model='gemma2', streaming=True, callbacks=[stream_handler])

            chain = prompt | llm | output_parser

            # 질문을 정의
            question = f"{select_day} 뉴스 전문적으로 상세하고 보기쉽게 정리해서 알려줘"

            chain_with_memory = ut.RunnableWithMessageHistory(
                prompt | llm | output_parser,
                ut.get_session_history,
                history_messages_key="history",
                input_messages_key="question"
            )

            response = chain_with_memory.invoke(
                {"now": now, "stock": stock_name, "ability": "주식", "username": session_id, "all_context": all_context, "question": question},
                config={"configurable": {"session_id": session_id}}
            )

            # 새로운 조언 추가
            advice_data = pd.DataFrame({'day': [select_day], 'stock_name': [stock_name], 'stock_advice': [response]})
            
            st.session_state["store"][session_id]["advice_df"] = pd.concat([advice_df, advice_data], ignore_index=True)
            st.session_state["store"][session_id]["messages"].append(ut.ChatMessage(role="assistant", content=response))

        else:
            # 기존 조언 출력
            st.write(f"{existing_advice.values[0]}")



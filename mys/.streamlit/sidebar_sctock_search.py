import streamlit as st
import FinanceDataReader as fdr
import datetime
import pandas as pd
import plotly.graph_objects as go

import sidebar_stock_advice
import sidebar_stock_chart
import locale  # locale 모듈 가져오기
# import importlib
# importlib.reload()

# 한국어 로케일 설정
locale.setlocale(locale.LC_TIME, 'ko_KR.UTF-8')

# 주식 종목 데이터셋 로드
df_krx = fdr.StockListing('KRX')[['Name','Code']]

# 상한가 데이터셋 로드
sanghanga_df = pd.read_csv('/home/alpaco/mys/projects/news/datas/new_real_final_sanghanga_df.csv', index_col=False, dtype={'종목코드': str, '종목명' :str})
sanghanga_df = sanghanga_df[['종목명','종목코드', '날짜', '라벨']]
# 상한가 데이터 타입 변환
sanghanga_df['날짜'] = pd.to_datetime(sanghanga_df['날짜'], format='%Y%m%d').dt.date   # 날짜 형식 변경
sanghanga_df = sanghanga_df.sort_values(by='날짜', ascending=False).reset_index(drop=True) # 날짜 내림차순 정렬 후 인덱스 재설정
sanghanga_df['라벨'] = sanghanga_df['라벨'].replace({1: 'Good', 0: 'Normal'}) # 라벨값 수정
# 상한가 컬럼 이름 별칭 지정
sanghanga_df = sanghanga_df.rename(columns={
    '라벨': 'SuperUP'
})

def about_stock():
    st.write('KRX 전체 종목 코드')
    st.dataframe(df_krx, use_container_width=True, height=200)
    
    st.write('상한가 종목')
    st.dataframe(sanghanga_df, use_container_width=True, height=200)
    st.session_state.code = st.text_input('종목코드', value='', placeholder='분석할 종목코드를 입력해 주세요')
    
    if st.session_state.code:
        # 종목 코드가 상한가 데이터프레임에 존재하는지 확인
        if st.session_state.code not in sanghanga_df['종목코드'].values:
            st.warning("상한가 종목 코드를 입력해주세요.")
            return

        news_df = sidebar_stock_advice.get_news_data(st.session_state.code)[0]
        select_day = st.selectbox("뉴스 날짜 선택", news_df["day"].tolist())
        # 특정 종목 상한가 데이터셋
        select_sanghanga_data(st.session_state.code)
        # 뉴스 정보 요약
        sidebar_stock_advice.stock_advice(st.session_state.code, select_day)
    
    st.session_state.start_date = st.date_input("조회 시작일을 선택해 주세요", datetime.datetime.now() - datetime.timedelta(days=365))
    st.session_state.end_date = st.date_input("조회 종료일을 선택해 주세요", datetime.datetime.now())

    if st.session_state.start_date > st.session_state.end_date:
        st.error("조회 날짜가 올바르지 않습니다.")
        return
    
    if st.session_state.code:
        try:
            df = fdr.DataReader(st.session_state.code, st.session_state.start_date, st.session_state.end_date).sort_index(ascending=True)
            if df.empty:
                st.error("해당 기간에 데이터가 없습니다.")
                return

            # 차트 호출
            sidebar_stock_chart.plot_stock_charts(df)

        except Exception as e:
            st.error(f"데이터를 가져오는 데 오류가 발생했습니다: {e}")



def select_sanghanga_data(code):
  return st.dataframe(sanghanga_df[sanghanga_df['종목코드'] == code], use_container_width=True, height=200)

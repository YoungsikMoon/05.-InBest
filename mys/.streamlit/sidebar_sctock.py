import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import datetime
import plotly.graph_objects as go
import plotly.express as px
# 주식 종목 데이터셋 로드
df_krx = fdr.StockListing('KRX')[['Code', 'Name']]

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

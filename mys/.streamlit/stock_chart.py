import streamlit as st
import FinanceDataReader as fdr
import datetime
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import load_model, Sequential
from tensorflow.keras.layers import Dense, LSTM, Conv1D
from datetime import timedelta
import os


import warnings
# 경고 무시 설정
warnings.filterwarnings("ignore")

def plot_stock_charts(df):
    sma_period = st.number_input("이동 평균선 기간 (일수)", min_value=1, value=20)
    # 이동 평균 및 볼린저 밴드 계산
    df['SMA'] = df['Close'].rolling(window=sma_period).mean()
    df['UpperBand'] = df['SMA'] + (df['Close'].rolling(window=sma_period).std() * 2)
    df['LowerBand'] = df['SMA'] - (df['Close'].rolling(window=sma_period).std() * 2)
    df['Daily Return'] = df['Close'].pct_change()

    # 차트 생성 및 표시
    if st.button('10일 예측'):
        plot_predict_chart(df)
    st.plotly_chart(plot_sma_chart(df, sma_period))
    st.plotly_chart(plot_bollinger_chart(df))
    st.plotly_chart(plot_volume_chart(df))
    st.plotly_chart(plot_daily_return_chart(df))


def plot_sma_chart(df, sma_period):
    sma_fig = go.Figure()
    sma_fig.add_trace(go.Scatter(
        x=df.index, y=df['SMA'], mode='lines',
        name=f'{sma_period}일 이동 평균', line=dict(color='orange'),
        hoverinfo='text', text=[f'날짜: {index.strftime("%Y-%m-%d")}<br>가격: {sma:.2f}' for index, sma in zip(df.index, df['SMA'])]
    ))
    sma_fig.update_layout(
        title="이동 평균선 차트", xaxis_title='날짜', yaxis_title='가격',
        xaxis=dict(
            rangeslider=dict(visible=True),
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1개월", step="month", stepmode="backward"),
                    dict(count=3, label="3개월", step="month", stepmode="backward"),
                    dict(count=6, label="6개월", step="month", stepmode="backward"),
                    dict(step="all", label="전체")
                ])
            )
        ),
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return sma_fig


def plot_bollinger_chart(df):
    bollinger_fig = go.Figure(data=[
        go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']),
        go.Scatter(x=df.index, y=df['UpperBand'], line=dict(color='red', width=1), name='상단 밴드'),
        go.Scatter(x=df.index, y=df['LowerBand'], line=dict(color='green', width=1), name='하단 밴드')
    ])
    bollinger_fig.update_layout(
        title="볼린저 밴드 차트", xaxis_title='날짜', yaxis_title='가격',
        xaxis=dict(
            rangeslider=dict(visible=True),
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1개월", step="month", stepmode="backward"),
                    dict(count=3, label="3개월", step="month", stepmode="backward"),
                    dict(count=6, label="6개월", step="month", stepmode="backward"),
                    dict(step="all", label="전체")
                ])
            )
        ),
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return bollinger_fig



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
        xaxis=dict(
            rangeslider=dict(visible=True),
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1개월", step="month", stepmode="backward"),
                    dict(count=3, label="3개월", step="month", stepmode="backward"),
                    dict(count=6, label="6개월", step="month", stepmode="backward"),
                    dict(step="all", label="전체")
                ])
            )
        ),
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
        xaxis=dict(
            rangeslider=dict(visible=True),
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1개월", step="month", stepmode="backward"),
                    dict(count=3, label="3개월", step="month", stepmode="backward"),
                    dict(count=6, label="6개월", step="month", stepmode="backward"),
                    dict(step="all", label="전체")
                ])
            )
        ),
        hovermode='x unified',
        margin=dict(l=40, r=40, t=40, b=40),
        plot_bgcolor='rgba(0,0,0,0)',
    )
    return daily_return_fig



def plot_predict_chart(df):
    WINDOW_SIZE = 20
    filename = os.path.join('/home/alpaco/chs/data/model/02_LSTM', 'ckeckpointer.weights.h5')
    model = Sequential([
        Conv1D(filters=32, kernel_size=5, padding="causal", activation="relu", input_shape=[WINDOW_SIZE, 1]),
        LSTM(16, activation='tanh'),
        Dense(16, activation="relu"),
        Dense(1),
    ])
    model.load_weights(filename)

    # 종가 데이터만 사용
    data = df['Close'].values.reshape(-1, 1)

    # 이전에 학습된 스케일러와 동일한 범위로 정규화
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data)

    # 모델이 학습한 타임 스텝
    time_step = 20

    # 테스트 데이터셋 준비
    test_data = scaled_data[-time_step:].reshape(1, -1)
    temp_input = test_data[0].tolist()

    # 향후 10일간 예측
    lst_output = []
    n_steps = time_step
    for _ in range(10):
        x_input = np.array(temp_input[-time_step:]).reshape((1, n_steps, 1))
        yhat = model.predict(x_input, verbose=0)
        temp_input.extend(yhat[0].tolist())
        lst_output.append(yhat[0][0])

    # 결과를 원래 스케일로 되돌림
    predicted_stock_price = scaler.inverse_transform(np.array(lst_output).reshape(-1, 1))

    # 예측 결과를 pandas Series로 변환 (날짜 인덱스 추가)
    last_date = df.index[-1]
    forecast_dates = pd.date_range(start=last_date + timedelta(days=1), periods=10, freq='B')
    forecast_series = pd.Series(predicted_stock_price.flatten(), index=forecast_dates)

    # 예측 결과 시각화
    # df_new = df[-30:]
    predict_fig = go.Figure()

    # 실제 가격 데이터
    predict_fig.add_trace(go.Scatter(
        x=df.index, y=df['Close'], mode='lines',
        name='실제 주가', line=dict(color='yellow'),
        hoverinfo='text', text=[f'날짜: {index.strftime("%Y-%m-%d")}<br>가격: {close:.2f}원' for index, close in zip(df.index, df['Close'])]
    ))

    # 예측 가격 데이터
    predict_fig.add_trace(go.Scatter(
        x=forecast_series.index, y=forecast_series.values, mode='lines',
        name='예측 주가', line=dict(color='red', width=3, dash='dash'),
        hoverinfo='text', text=[f'날짜: {index.strftime("%Y-%m-%d")}<br>예측 가격: {pred:.2f}원' for index, pred in zip(forecast_series.index, forecast_series.values)]
    ))

    # 레이아웃 설정
    predict_fig.update_layout(
        title="향후 10일간 주가 예측",
        xaxis_title='날짜',
        yaxis_title='가격 (원)',
        xaxis=dict(
            rangeslider=dict(visible=True),
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1개월", step="month", stepmode="backward"),
                    dict(count=3, label="3개월", step="month", stepmode="backward"),
                    dict(count=6, label="6개월", step="month", stepmode="backward"),
                    dict(step="all", label="전체")
                ])
            )
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        hovermode='x unified',
    )

    st.plotly_chart(predict_fig)
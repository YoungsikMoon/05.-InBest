import streamlit as st
import FinanceDataReader as fdr
import datetime
import plotly.graph_objects as go

# 주식 종목 데이터셋 로드
df_krx = fdr.StockListing('KRX')[['Code', 'Name']]

def about_stock():
    st.write('주식 목록')
    st.dataframe(df_krx, width=400, height=200)

    st.session_state.code = st.text_input('종목코드', value='', placeholder='종목코드를 입력해 주세요')
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

            st.title(f"종목코드: {st.session_state.code}")
            plot_stock_charts(df)

        except Exception as e:
            st.error(f"데이터를 가져오는 데 오류가 발생했습니다: {e}")

def plot_stock_charts(df):
    sma_period = st.number_input("이동 평균선 기간 (일수)", min_value=1, value=20)

    # 이동 평균 및 볼린저 밴드 계산
    df['SMA'] = df['Close'].rolling(window=sma_period).mean()
    df['UpperBand'] = df['SMA'] + (df['Close'].rolling(window=sma_period).std() * 2)
    df['LowerBand'] = df['SMA'] - (df['Close'].rolling(window=sma_period).std() * 2)
    df['Daily Return'] = df['Close'].pct_change()

    # 차트 생성 및 표시
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
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=3, label="3m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(step="all")
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
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=3, label="3m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(step="all")
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
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=3, label="3m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(step="all")
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
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=3, label="3m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(step="all")
                ])
            )
        ),
        hovermode='x unified',
        margin=dict(l=40, r=40, t=40, b=40),
        plot_bgcolor='rgba(0,0,0,0)',
    )
    return daily_return_fig

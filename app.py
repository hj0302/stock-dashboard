# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import pickle
import copy
import pathlib
import urllib.request
import dash
import math
import datetime as dt
import pandas as pd
from dash.dependencies import Input, Output, State, ClientsideFunction
import dash_core_components as dcc
import dash_html_components as html
import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import datetime
from dateutil.relativedelta import relativedelta
from datetime import date


# get relative data folder
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("data").resolve()

app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}],
)
app.title = "Analysis of stock market"
server = app.server

# Create controls

sector_list = ['제약', '자동차', '의류', '보험', '식품,음료', '운송', '복합기업', '포장재,종이와목재',
            '건설,건축제품,건축자재', '자동차부품', '에너지', '비철금속', '기계', '전기장비', '철강', '반도체',
            '핸드셋', '화학', '통신서비스', '상사', '증권', '디스플레이장비', '전기제품', '미디어',
            '완구,레저용품', '생명과학', '문구,가정용품', '화장품', '유틸리티', '가구', '건강관리장비,서비스',
            '백화점', '전자장비,사무용전자제품', '컴퓨터', '기타금융', '기타자본재', '은행', '호텔,레저서비스',
            '소프트웨어', '기타유통', '전자제품', '조선', '필수가정용품', '통신장비', '게임소프트웨어', '담배',
            '교육', '디스플레이패널']

time_list = ['1일전 대비 수익률','7일전 대비 수익률','1달전 대비 수익률','3달전 대비 수익률','6달전 대비 수익률','1년전 대비 수익률']

sector_options = [
    {"label": sector, "value": sector} for sector in sector_list
]

time_options = [
    {"label": time, "value": time} for time in time_list
]

def check_closed_day(day):
    while True:
        if day in date_list :
            return day
        else :
            day = datetime.datetime.strptime(str(day), '%Y-%m-%d') - datetime.timedelta(days=1)
            day = datetime.datetime.strftime(day, '%Y-%m-%d')

# 입력일자가 토요일, 일요일이면 해당 주 금요일로 변경하는 함수 

def check_week(day):
    week_day = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
    
    if week_day[day.weekday()] == '토요일':
        day = datetime.datetime.strptime(str(day), '%Y-%m-%d %H:%M:%S') - datetime.timedelta(days=1)
        return datetime.datetime.strftime(day, '%Y-%m-%d')
    elif week_day[day.weekday()] == '일요일':
        day = datetime.datetime.strptime(str(day), '%Y-%m-%d %H:%M:%S') - datetime.timedelta(days=2)
        return datetime.datetime.strftime(day, '%Y-%m-%d')
    else :
        return datetime.datetime.strftime(day, '%Y-%m-%d')

# 분석일자 세팅하는 함수

def setting_date(date):
    ago_1_day = datetime.datetime.strptime(date, '%Y-%m-%d') - datetime.timedelta(days=1)#하루전
    ago_7_day = datetime.datetime.strptime(date, '%Y-%m-%d') - datetime.timedelta(weeks=1)#일주일전
    ago_30_day = datetime.datetime.strptime(date, '%Y-%m-%d') - relativedelta(months=1)#한달전
    ago_90_day = datetime.datetime.strptime(date, '%Y-%m-%d') - relativedelta(months=3)#세달전
    ago_240_day = datetime.datetime.strptime(date, '%Y-%m-%d') - relativedelta(months=6)#세달전
    ago_360_day = datetime.datetime.strptime(date, '%Y-%m-%d') - relativedelta(years=1)#일년전
    
    ago_1_day = check_week(ago_1_day)
    ago_7_day = check_week(ago_7_day)
    ago_30_day = check_week(ago_30_day)
    ago_90_day = check_week(ago_90_day)
    ago_240_day = check_week(ago_240_day)
    ago_360_day = check_week(ago_360_day)

    ago_1_day = check_closed_day(ago_1_day)
    ago_7_day = check_closed_day(ago_7_day)
    ago_30_day = check_closed_day(ago_30_day)
    ago_90_day = check_closed_day(ago_90_day)
    ago_240_day = check_closed_day(ago_240_day)
    ago_360_day = check_closed_day(ago_360_day)  

    return ago_1_day,ago_7_day,ago_30_day,ago_90_day,ago_240_day,ago_360_day


# Load data
# 종목 리스트 (안에 섹터정보 포함)

def load_stock_info_df():
    '''
    주요 필드
    - stockCode : 종목코드
    - stockName : 종목명
    - sectorName : 섹터명
    - industry_index_name : {시장}_{규모} (시장: Kospi/Kosdaq, 규모: L/M/S)
    '''
    file_path = '{}/stock_list.json'.format(DATA_PATH)
    with open(file_path) as f:
        stock_list = [json.loads(line) for line in f]
    return pd.DataFrame(stock_list)

# 일별/종목별 주가 테이블

def load_stock_price_df():
    '''
    테이블 형식
    - date : YYYY-mm-dd
    - price : 종가
    - stockCode : 종목코드
    - stockName : 종목명
    '''

    file_path = '{}/stock_2018_prices.pkl'.format(DATA_PATH)
    price_df = pd.read_pickle(file_path)

    #price_df = price_df.stack().reset_index()
    #price_df.columns = ['date', 'Code_Name', 'price']
    #price_df[['stockCode', 'stockName']]  = price_df['Code_Name'].str.split('_',expand=True)
    #price_df.drop('Code_Name', axis=1, inplace=True)
    
    return price_df
 
stock_info_df = load_stock_info_df()
stock_price_df = load_stock_price_df()

stock_price_df = stock_price_df[stock_price_df['date'] >= '20180101']

sector_df = pd.merge(stock_price_df, stock_info_df[['stockCode', 'stockName', 'sectorName']], on =['stockCode', 'stockName'])

date_df = sector_df[['date']].drop_duplicates()
date_df['date'] = date_df['date'].apply(lambda x: datetime.datetime.strftime(x, '%Y-%m-%d'))
date_list = date_df['date'].unique().tolist()

layout = dict(
    autosize=True,
    automargin=True,
    margin=dict(l=30, r=30, b=20, t=40),
    hovermode="closest",
    plot_bgcolor="#F9F9F9",
    paper_bgcolor="#F9F9F9",
    legend=dict(font=dict(size=10), orientation="h"),
    title="Satellite Overview",
)

# Create app layout
app.layout = html.Div(
    [
        dcc.Store(id="aggregate_data"),
        # empty Div to trigger javascript file for graph resizing
        html.Div(id="output-clientside"),
        html.Div(
            [
                html.Div(
                    [
                        html.Img(
                            src=app.get_asset_url("vaivcompany_ci_screen_color_h.png"),
                            id="plotly-image",
                            style={
                                "height": "60px",
                                "width": "auto",
                                "margin-bottom": "25px",
                            },
                        )
                    ],
                    className="one-third column",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.H3(
                                    "Analysis of stock market",
                                    style={"margin-bottom": "0px"},
                                ),
                                html.H5(
                                    "섹터별 주요 종목 가격 변화량 차트", style={"margin-top": "0px"}
                                ),
                            ]
                        )
                    ],
                    className="one-half column",
                    id="title",
                ),
                html.Div(
                    [
                        html.A(
                            html.Button("somemoney", id="learn-more-button"),
                            href="https://money.some.co.kr/",
                        )
                    ],
                    className="one-third column",
                    id="button",
                ),
            ],
            id="header",
            className="row flex-display",
            style={"margin-bottom": "25px"},
        ),
        html.Div(
            [
                html.Div(
                    [   
                        html.P("Sector Select:", className="control_label"),
                        dcc.Dropdown(
                            id="sector_option",
                            options=sector_options,
                            value='증권',
                            className="dcc_control",
                        ),
                        html.P("x축 Select:", className="control_label"),
                        dcc.Dropdown(
                            id="x_option",
                            options=time_options,
                            value='7일전 대비 수익률',
                            className="dcc_control",
                        ),
                        html.P("y축 Select:", className="control_label"),
                        dcc.Dropdown(
                            id="y_option",
                            options=time_options,
                            value='1달전 대비 수익률',
                            className="dcc_control",
                        ),
                    ],
                    className="pretty_container two columns",
                    id="cross-filter-options",
                ),
                html.Div(
                    [   
                        html.P("분석일 :", className="control_label"),
                        dcc.DatePickerSingle(
                            id='anal-date-picker-single',
                            min_date_allowed=date(2000, 1, 2),
                            max_date_allowed=date(2021, 8, 25),
                            initial_visible_month=date(2021, 8, 25),
                            date=date(2021, 8, 25)
                        ),
                        html.P("비교일 :", className="control_label"),
                        dcc.DatePickerSingle(
                            id='comp-date-picker-single',
                            min_date_allowed=date(2000, 1, 2),
                            max_date_allowed=date(2021, 8, 25),
                            initial_visible_month=date(2021, 1, 12),
                            date=date(2021, 1, 12)
                        ),
                    ],
                    className="pretty_container two columns",
                    id="output-container-date-picker-single",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [html.P("섹터 종목 개수"), html.H6(id="sector_count")],
                                    id="반도체",
                                    className="pretty_container 2 columns",
                                ),
                                html.Div(
                                    [html.P("전일 대비 수익률"), html.H6(id="ago_1_earnings")],
                                    id="30",
                                    className="pretty_container 2 columns",
                                ),
                                html.Div(
                                    [html.P("7일전 대비 수익률"), html.H6(id="ago_7_earnings")],
                                    id="20",
                                    className="pretty_container 2 columns",
                                ),
                                html.Div(
                                    [html.P("주도주"), html.H6(id="stocks1"),html.H6(id="stocks2")],
                                    id="삼성전자",
                                    className="pretty_container 2 columns",
                                ),
                            ],
                            id="info-container",
                            className="row container-display",
                        ),
                        html.Div(
                            [dcc.Graph(id="count_graph")],
                            id="countGraphContainer",
                            className="pretty_container",
                        ),
                    ],
                    id="right-column",
                    className="eight columns",
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="main_graph")],
                    className="pretty_container twelve columns",
                ),
            ],
            className="row flex-display",
        ),
    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"},
)

def update_date(date_value):
    if date_value is not None:
        date_object = date.fromisoformat(date_value)
        date_string = date_object.strftime('%Y-%m-%d')
        return date_string

def calc_RSI(df, period):
    U = np.where(df.diff(1)['price'] >  0, df.diff(1)['price'], 0)
    D = np.where(df.diff(1)['price'] <  0, df.diff(1)['price'] * (-1), 0)
    date_index = df.index.astype('str')
    AU = pd.DataFrame(U, index=date_index).rolling(window=period).mean()
    AD = pd.DataFrame(D, index=date_index).rolling(window=period).mean()
    RSI = AU / (AD+AU) * 100
    return RSI

# Selectors -> well text
@app.callback(
    Output("sector_count", "children"),
    [
        Input("sector_option", "value"),
    ],
)
def update_sector_count(input_sectorName):
    sector_sub_df = stock_info_df[stock_info_df['sectorName'] == input_sectorName]

    sector_n_count = sector_sub_df['stockCode'].nunique()
    return sector_n_count

# Selectors -> well text
@app.callback(
    Output("ago_1_earnings", "children"),
    Output("ago_7_earnings", "children"),
    Output("stocks1", "children"),
    Output("stocks2", "children"),
    Output('main_graph', 'figure'),
    [
        Input("sector_option", "value"),
        Input("anal-date-picker-single", "date"),
        Input("comp-date-picker-single", "date"),
        Input("x_option", "value"),
        Input("y_option", "value"),
    ],
)
def update_sector_count(input_sectorName, input_anal_date, input_comp_date, xaxis_option, yaxis_option):
    
    sector_sub_df = sector_df[sector_df['sectorName'] == input_sectorName]

    anal_ago_1_day,anal_ago_7_day,anal_ago_30_day,anal_ago_90_day,anal_ago_240_day,anal_ago_360_day = setting_date(input_anal_date)
    comp_ago_1_day,comp_ago_7_day,comp_ago_30_day,comp_ago_90_day,comp_ago_240_day,comp_ago_360_day = setting_date(input_comp_date)

    sector_sub_anal_df = sector_sub_df[sector_sub_df['date'].isin([input_anal_date, anal_ago_1_day,anal_ago_7_day,anal_ago_30_day,anal_ago_90_day,anal_ago_240_day,anal_ago_360_day])]
    sector_sub_comp_df = sector_sub_df[sector_sub_df['date'].isin([input_comp_date, comp_ago_1_day,comp_ago_7_day,comp_ago_30_day,comp_ago_90_day,comp_ago_240_day,comp_ago_360_day])]

    sector_sub_anal_df2 = pd.pivot_table(data=sector_sub_anal_df, index=['stockName', 'stockCode'], columns=['date'],values='price')
    sector_sub_comp_df2 = pd.pivot_table(data=sector_sub_comp_df, index=['stockName', 'stockCode'], columns=['date'],values='price')

    sector_sub_anal_df2.columns = ['ago_360_day','ago_240_day','ago_90_day','ago_30_day','ago_7_day','ago_1_day','day']
    sector_sub_comp_df2.columns = ['ago_360_day','ago_240_day','ago_90_day','ago_30_day','ago_7_day','ago_1_day','day']

    sector_sub_anal_df2['1일전 대비 수익률'] = ((sector_sub_anal_df2['day'] - sector_sub_anal_df2['ago_1_day']) / sector_sub_anal_df2['ago_1_day'] *100).round(2)
    sector_sub_anal_df2['7일전 대비 수익률'] = ((sector_sub_anal_df2['day'] - sector_sub_anal_df2['ago_7_day']) / sector_sub_anal_df2['ago_7_day'] *100).round(2)
    sector_sub_anal_df2['1달전 대비 수익률'] = ((sector_sub_anal_df2['day'] - sector_sub_anal_df2['ago_30_day']) / sector_sub_anal_df2['ago_30_day'] *100).round(2)
    sector_sub_anal_df2['3달전 대비 수익률'] = ((sector_sub_anal_df2['day'] - sector_sub_anal_df2['ago_90_day']) / sector_sub_anal_df2['ago_90_day'] *100).round(2)
    sector_sub_anal_df2['6달전 대비 수익률'] = ((sector_sub_anal_df2['day'] - sector_sub_anal_df2['ago_240_day']) / sector_sub_anal_df2['ago_240_day'] *100).round(2)
    sector_sub_anal_df2['1년전 대비 수익률'] = ((sector_sub_anal_df2['day'] - sector_sub_anal_df2['ago_360_day']) / sector_sub_anal_df2['ago_360_day'] *100).round(2)

    sector_sub_comp_df2['1일전 대비 수익률'] = ((sector_sub_comp_df2['day'] - sector_sub_comp_df2['ago_1_day']) / sector_sub_comp_df2['ago_1_day'] *100).round(2)
    sector_sub_comp_df2['7일전 대비 수익률'] = ((sector_sub_comp_df2['day'] - sector_sub_comp_df2['ago_7_day']) / sector_sub_comp_df2['ago_7_day'] *100).round(2)
    sector_sub_comp_df2['1달전 대비 수익률'] = ((sector_sub_comp_df2['day'] - sector_sub_comp_df2['ago_30_day']) / sector_sub_comp_df2['ago_30_day'] *100).round(2)
    sector_sub_comp_df2['3달전 대비 수익률'] = ((sector_sub_comp_df2['day'] - sector_sub_comp_df2['ago_90_day']) / sector_sub_comp_df2['ago_90_day'] *100).round(2)
    sector_sub_comp_df2['6달전 대비 수익률'] = ((sector_sub_comp_df2['day'] - sector_sub_comp_df2['ago_240_day']) / sector_sub_comp_df2['ago_240_day'] *100).round(2)
    sector_sub_comp_df2['1년전 대비 수익률'] = ((sector_sub_comp_df2['day'] - sector_sub_comp_df2['ago_360_day']) / sector_sub_comp_df2['ago_360_day'] *100).round(2)

    sector_sub_anal_df2 = sector_sub_anal_df2.reset_index()
    sector_sub_comp_df2 = sector_sub_comp_df2.reset_index()

    stocks = sector_sub_anal_df2.sort_values('7일전 대비 수익률', ascending=False)['stockName'].tolist()[:2]

    rsi_df = sector_sub_df[(sector_sub_df['date'] >=anal_ago_30_day) & (sector_sub_df['date'] <= input_anal_date)]
    rsi_df.set_index('date', inplace=True)

    rsi_rslt_df = pd.DataFrame()
    for stock in rsi_df['stockName'].unique():
        t_df = rsi_df[rsi_df['stockName'] == stock][['price']]
        t_df.insert(len(t_df.columns), "RSI", calc_RSI(t_df, 7))
        t_df['stockName'] = stock
        rsi_rslt_df = pd.concat([rsi_rslt_df, t_df])
        
    rsi_rslt_df.reset_index(inplace=True)
    rsi_rslt_df = rsi_rslt_df.round()
    rsi_rslt_df = rsi_rslt_df[rsi_rslt_df['date'] == input_anal_date]

    sector_sub_comp_df2 = pd.merge(sector_sub_comp_df2, rsi_rslt_df[['RSI', 'stockName']], on=['stockName'])
    sector_sub_anal_df2 = pd.merge(sector_sub_anal_df2, rsi_rslt_df[['RSI', 'stockName']], on=['stockName'])
    
    # Create figure
    #fig = go.Figure()
    fig = make_subplots(rows=1, cols=2, subplot_titles=("비교시점", "분석시점"))
    # Add traces
    fig.add_trace(go.Scatter(x=sector_sub_comp_df2[xaxis_option],y=sector_sub_comp_df2[yaxis_option],
                            mode="markers+text", text=sector_sub_comp_df2['stockName'],marker=dict(color=sector_sub_comp_df2['RSI'],coloraxis="coloraxis")),
                row=1, col=1)
    fig.add_trace(go.Scatter(x=[sector_sub_comp_df2[xaxis_option].mean()],y=[sector_sub_comp_df2[yaxis_option].mean()],
                            mode="markers+text",text=['black'],marker=dict(color="black",symbol=4, size=12), name='평균'), row=1, col=1)
    fig.add_trace(go.Scatter(x=sector_sub_anal_df2[xaxis_option],y=sector_sub_anal_df2[yaxis_option],
                            mode="markers+text",text=sector_sub_anal_df2['stockName'],marker=dict(color=sector_sub_anal_df2['RSI'],coloraxis="coloraxis")),
                row=1, col=2)
    fig.add_trace(go.Scatter(x=[sector_sub_anal_df2[xaxis_option].mean()],y=[sector_sub_anal_df2[yaxis_option].mean()],
                            mode="markers+text",text=['black'],marker=dict(color="black",symbol=4, size=12), name='평균'), row=1, col=2)
    fig.update_traces(textposition='top center')
    fig.update_layout(template='plotly_white', height=700,coloraxis=dict(colorscale='Bluered'), showlegend=False)    
    # Set x-axis title
    fig.update_xaxes(title_text="<b>{}</b>".format(xaxis_option))
    # Set y-axes titles
    fig.update_yaxes(title_text="<b>{}</b> ".format(yaxis_option))
    return sector_sub_anal_df2['1일전 대비 수익률'].mean().round(2), sector_sub_anal_df2['7일전 대비 수익률'].mean().round(2), stocks[0], stocks[1], fig

# Main
if __name__ == "__main__":
    app.run_server(debug=True)

# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import pickle
import copy
import pathlib
import dash
import pandas as pd
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import datetime
from dateutil.relativedelta import relativedelta
from datetime import date

# Path Setting
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("data").resolve()

app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}]
)
app.title = "Analysis of stock market"
server = app.server

# OptionList Setting
sector_list = ['제약', '자동차', '의류', '보험', '식품,음료', '운송', '복합기업', '포장재,종이와목재', '건설,건축제품,건축자재', '자동차부품',
               '에너지', '비철금속', '기계', '전기장비', '철강', '반도체', '핸드셋', '화학', '통신서비스', '상사',
               '증권', '디스플레이장비', '전기제품', '미디어','완구,레저용품', '생명과학', '문구,가정용품', '화장품', '유틸리티',
               '가구', '건강관리장비,서비스', '백화점', '전자장비,사무용전자제품', '컴퓨터', '기타금융', '기타자본재', '은행', '호텔,레저서비스', '소프트웨어',
               '기타유통', '전자제품', '조선', '필수가정용품', '통신장비', '게임소프트웨어', '담배','교육', '디스플레이패널']
axis_list = ['1일전 대비 수익률','7일전 대비 수익률','1달전 대비 수익률','3달전 대비 수익률','6달전 대비 수익률','1년전 대비 수익률']

sector_options = [ {"label": sector, "value": sector} for sector in sector_list ]
axis_options = [ {"label": axis, "value": axis} for axis in axis_list ]

# 휴장일일 경우 하루 전 개장일로 날짜 계산
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
    ago_1_day = datetime.datetime.strptime(date, '%Y-%m-%d') - datetime.timedelta(days=1) #하루전
    ago_7_day = datetime.datetime.strptime(date, '%Y-%m-%d') - datetime.timedelta(weeks=1) #일주일전
    ago_30_day = datetime.datetime.strptime(date, '%Y-%m-%d') - relativedelta(months=1) #1달전
    ago_90_day = datetime.datetime.strptime(date, '%Y-%m-%d') - relativedelta(months=3) #3달전
    ago_240_day = datetime.datetime.strptime(date, '%Y-%m-%d') - relativedelta(months=6) #6달전
    ago_360_day = datetime.datetime.strptime(date, '%Y-%m-%d') - relativedelta(years=1) #1년전
    
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

    stock_info_df = pd.DataFrame(stock_list)
    stock_info_df[['Market', 'Scale']] = stock_info_df['Industry_index_name'].str.split('_', expand=True)
    stock_info_df = stock_info_df[['stockCode', 'stockName', 'sectorCode', 'sectorName', 'Market', 'Scale']]
    return stock_info_df

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

# 섹터별 인덱스 데이블
def load_sector_index_df():
    '''
    테이블 형식
    - date : YYYY-mm-dd
    - setorIndex : index
    - stockName : 종목명
    '''
    file_path = '{}/sectorIndex.pkl'.format(DATA_PATH)
    index_df = pd.read_pickle(file_path)
    
    index_df['date'] = index_df['date'].apply(lambda x : '{}-{}-{}'.format(x[:4], x[4:6],x[6:]))
    
    return index_df

stock_info_df = load_stock_info_df()
stock_price_df = load_stock_price_df()
stock_index_df = load_sector_index_df()

sector_df = pd.merge(stock_price_df, stock_info_df, on =['stockCode', 'stockName'])

date_df = sector_df[['date']].drop_duplicates()
date_df['date'] = date_df['date'].apply(lambda x: datetime.datetime.strftime(x, '%Y-%m-%d'))
date_list = date_df['date'].unique().tolist()

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
                            src=app.get_asset_url("vaivcompany_ci_print_color.png"),
                            id="plotly-image",
                            style={
                                "height": "40px",
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
                                    "Sector Analysis",
                                    style={"margin-bottom": "0px"},
                                ),
                                #html.H5(
                                #    "섹터별 주요 종목 가격 변화량 차트", style={"margin-top": "0px"}
                                #),
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
                            value='반도체',
                            className="dcc_control",
                        ),
                        html.P("Market(시장) :", className="control_label"),
                        dcc.Dropdown(
                            id="market-dynamic-dropdown",
                            options=[
                                {'label': 'Kospi', 'value': 'Kospi'},
                                {'label': 'Kosdaq', 'value': 'Kosdaq'},
                            ],
                            multi=True,
                            value="Kospi"
                        ),
                        html.P("Scale(규모) :", className="control_label"),
                        dcc.Dropdown(
                            id="scale-dynamic-dropdown",
                            options=[
                                {'label': 'M', 'value': 'M'},
                                {'label': 'S', 'value': 'S'},
                                {'label': 'L', 'value': 'L'},
                                {'label': 'E', 'value': 'E'}
                            ],
                            multi=True,
                            value=["L","M"]
                        ),
                        html.P("분석일 :", className="control_label"),
                        dcc.DatePickerSingle(
                            id='anal-date-picker-single',
                            min_date_allowed=date(2000, 1, 2),
                            max_date_allowed=date(2021, 8, 25),
                            initial_visible_month=date(2021, 8, 25),
                            date=date(2021, 8, 25),
                        ),
                        html.P("비교일 :", className="control_label"),
                        dcc.DatePickerSingle(
                            id='comp-date-picker-single',
                            min_date_allowed=date(2000, 1, 2),
                            max_date_allowed=date(2021, 8, 25),
                            initial_visible_month=date(2021, 6, 11),
                            date=date(2021, 6, 11),
                        ),
                        html.P("x축 Select:", className="control_label"),
                        dcc.Dropdown(
                            id="x_option",
                            options=axis_options,
                            value='1달전 대비 수익률',
                            className="dcc_control",
                        ),
                        html.P("y축 Select:", className="control_label"),
                        dcc.Dropdown(
                            id="y_option",
                            options=axis_options,
                            value='7일전 대비 수익률',
                            className="dcc_control",
                        ),
                    ],
                    className="pretty_container two columns",
                    id="cross-filter-options",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [html.P("섹터 종목 개수"), html.H6(id="sector_count")],
                                    id="반도체",
                                    className="pretty_container two columns",
                                ),
                                html.Div(
                                    [html.P("전일 대비 수익률"), html.H6(id="ago_1_earnings")],
                                    id="30",
                                    className="pretty_container two columns",
                                ),
                                html.Div(
                                    [html.P("7일전 대비 수익률"), html.H6(id="ago_7_earnings")],
                                    id="20",
                                    className="pretty_container two columns",
                                ),
                                html.Div(
                                    [   
                                        html.P("주도주"),
                                        html.Div(
                                            [
                                                html.H6(id="lead_stock_1")
                                            ],
                                            id="삼성전자",
                                            className="pretty_container five columns",
                                        ),
                                        html.Div(
                                            [
                                                html.H6(id="lead_stock_2")
                                            ],
                                            id="sk하이닉스",
                                            className="pretty_container five columns",
                                        )
                                    ],
                                    className="pretty_container six columns",
                                ),
                            ],
                            id="info-container",
                            className="row container-display",
                        ),
                        html.Div(
                            [html.P("섹터별 지수"), dcc.Graph(id="sector_index_graph")],
                            id="countGraphContainer",
                            className="pretty_container",
                        ),
                    ],
                    id="right-column",
                    className="ten columns",
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                    [html.P("비교 시점"), dcc.Graph(id="main_scatter_graph2")],
                    className="pretty_container twelve columns",
                ),
                html.Div(
                    [html.P("분석 시점"), dcc.Graph(id="main_scatter_graph1")],
                    className="pretty_container twelve columns",
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                    [html.P("종목별 종가 추이"), dcc.Graph(id="sub_line_graph")],
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

# RSI 계산하는 함수
def calc_RSI(df, period):
    U = np.where(df.diff(1)['price'] >  0, df.diff(1)['price'], 0)
    D = np.where(df.diff(1)['price'] <  0, df.diff(1)['price'] * (-1), 0)
    date_index = df.index.astype('str')
    AU = pd.DataFrame(U, index=date_index).rolling(window=period).mean()
    AD = pd.DataFrame(D, index=date_index).rolling(window=period).mean()
    RSI = AU / (AD+AU) * 100
    return RSI

@app.callback(
    Output("sector_count", "children"),
    [
        Input("sector_option", "value"),
        Input("market-dynamic-dropdown", "value"),
        Input("scale-dynamic-dropdown", "value"),
    ],
)
def update_sector_count(input_sectorName, mareket_option, scale_option):
    if isinstance(mareket_option, list) == False:
        mareket_option = mareket_option.split(',')
    if isinstance(scale_option, list) == False:
        scale_option = scale_option.split(',')

    sector_sub_df = stock_info_df[stock_info_df['sectorName'] == input_sectorName]
    sector_sub_df = sector_sub_df[sector_sub_df['Market'].isin(mareket_option)]
    sector_sub_df = sector_sub_df[sector_sub_df['Scale'].isin(scale_option)]
    sector_n_count = sector_sub_df['stockCode'].nunique()
    return sector_n_count


@app.callback(
    Output('sector_index_graph', 'figure'),
    [
        Input("sector_option", "value"),
    ],
)
def update_sector_index_graph(input_sectorName):    
    df = stock_index_df[stock_index_df['sectorName'] == input_sectorName]
    df = df[df['date'] >= '2015-01-01'] 
    # Create figure
    #fig = go.Figure()
    fig = make_subplots(rows=1, cols=1)
    # Add traces
    fig.add_trace(go.Scatter(x=df['date'], y=df['setorIndex'], mode="lines",
                             line=dict(shape="linear", color="#1c751c") #spline
                             ), row=1, col=1)

    fig.update_layout(template='plotly_white', height=400,
                      xaxis=dict(
                          rangeselector=dict(
                              buttons=list([
                                  dict(count=1, label="1m", step="month", stepmode="backward"),
                                  dict(count=6, label="6m", step="month", stepmode="backward"),
                                  dict(count=1, label="1y", step="year", stepmode="backward"),
                                  dict(step="all")
                                  ]
                                )
                            ),
                    rangeslider=dict(visible=False),
                    type="date"
                    )
                )    
    # Set x-axis title
    fig.update_xaxes(title_text="<b>{}</b>".format('날짜'))
    # Set y-axes titles
    fig.update_yaxes(title_text="<b>{}</b> ".format('Sector Index'))

    return fig

@app.callback(
    Output("ago_1_earnings", "children"),
    Output("ago_7_earnings", "children"),
    Output("lead_stock_1", "children"),
    Output("lead_stock_2", "children"),
    Output('main_scatter_graph1', 'figure'),
    [
        Input("sector_option", "value"),
        Input("anal-date-picker-single", "date"),
        Input("market-dynamic-dropdown", "value"),
        Input("scale-dynamic-dropdown", "value"),
        Input("x_option", "value"),
        Input("y_option", "value"),
        Input("main_scatter_graph1", "selectedData"),
        Input("main_scatter_graph2", "selectedData"),

    ],
)
def update_main_graph(input_sectorName, input_anal_date, mareket_option, scale_option, xaxis_option, yaxis_option, selection1, selection2):
    
    sector_sub_df = sector_df[sector_df['sectorName'] == input_sectorName]
    if isinstance(mareket_option, list) == False:
        mareket_option = mareket_option.split(',')
    if isinstance(scale_option, list) == False:
        scale_option = scale_option.split(',')

    sector_sub_df = sector_sub_df[(sector_sub_df['Market'].isin(mareket_option)) & (sector_sub_df['Scale'].isin(scale_option))]

    anal_ago_1_day,anal_ago_7_day,anal_ago_30_day,anal_ago_90_day,anal_ago_240_day,anal_ago_360_day = setting_date(input_anal_date)

    sector_sub_anal_df = sector_sub_df[sector_sub_df['date'].isin([input_anal_date, anal_ago_1_day,anal_ago_7_day,anal_ago_30_day,anal_ago_90_day,anal_ago_240_day,anal_ago_360_day])]

    sector_sub_anal_df2 = pd.pivot_table(data=sector_sub_anal_df, index=['stockName', 'stockCode'], columns=['date'],values='price')

    sector_sub_anal_df2.columns = ['ago_360_day','ago_240_day','ago_90_day','ago_30_day','ago_7_day','ago_1_day','day']

    sector_sub_anal_df2['1일전 대비 수익률'] = ((sector_sub_anal_df2['day'] - sector_sub_anal_df2['ago_1_day']) / sector_sub_anal_df2['ago_1_day'] *100).round(2)
    sector_sub_anal_df2['7일전 대비 수익률'] = ((sector_sub_anal_df2['day'] - sector_sub_anal_df2['ago_7_day']) / sector_sub_anal_df2['ago_7_day'] *100).round(2)
    sector_sub_anal_df2['1달전 대비 수익률'] = ((sector_sub_anal_df2['day'] - sector_sub_anal_df2['ago_30_day']) / sector_sub_anal_df2['ago_30_day'] *100).round(2)
    sector_sub_anal_df2['3달전 대비 수익률'] = ((sector_sub_anal_df2['day'] - sector_sub_anal_df2['ago_90_day']) / sector_sub_anal_df2['ago_90_day'] *100).round(2)
    sector_sub_anal_df2['6달전 대비 수익률'] = ((sector_sub_anal_df2['day'] - sector_sub_anal_df2['ago_240_day']) / sector_sub_anal_df2['ago_240_day'] *100).round(2)
    sector_sub_anal_df2['1년전 대비 수익률'] = ((sector_sub_anal_df2['day'] - sector_sub_anal_df2['ago_360_day']) / sector_sub_anal_df2['ago_360_day'] *100).round(2)

    sector_sub_anal_df2 = sector_sub_anal_df2.reset_index()

    stocks = sector_sub_anal_df2.sort_values('7일전 대비 수익률', ascending=False)['stockName'].tolist()[:2]
    stocks_rate = sector_sub_anal_df2.sort_values('7일전 대비 수익률', ascending=False)['7일전 대비 수익률'].tolist()[:2]

    if len(stocks) == 0:
        output1 = ' '
        output2 = ' '
    elif len(stocks)  == 1:
        output1 = stocks[0] + ' ' + str(stocks_rate[0]) + '%'
        output2 = ' '
    else :
        output1 = stocks[0] + ' ' + str(stocks_rate[0]) + '%'
        output2 = stocks[1] + ' ' + str(stocks_rate[1]) + '%'

    rsi_df = sector_sub_df[(sector_sub_df['date'] >=anal_ago_30_day) & (sector_sub_df['date'] <= input_anal_date)]
    rsi_df.set_index('date', inplace=True)

    rsi_rslt_df = pd.DataFrame()
    for stock in rsi_df['stockName'].unique():
        t_df = rsi_df[rsi_df['stockName'] == stock][['price']]
        t_df.insert(len(t_df.columns), "RSI", calc_RSI(t_df, 14))
        t_df['stockName'] = stock
        rsi_rslt_df = pd.concat([rsi_rslt_df, t_df])
        
    rsi_rslt_df.reset_index(inplace=True)
    rsi_rslt_df = rsi_rslt_df.round()
    rsi_rslt_df = rsi_rslt_df[rsi_rslt_df['date'] == input_anal_date]

    sector_sub_anal_df2 = pd.merge(sector_sub_anal_df2, rsi_rslt_df[['RSI', 'stockName']], on=['stockName'])

    sector_sub_anal_df2 = sector_sub_anal_df2.sort_values('stockName')
    selectedpoints = sector_sub_anal_df2.index
    for selected_data in [selection1, selection2]:
        if selected_data and selected_data['points']:
            selectedpoints = np.intersect1d(selectedpoints,
                [p['customdata'] for p in selected_data['points']])
    
    selectedpoints_local = copy.deepcopy(selection1)

    if selectedpoints_local and selectedpoints_local['range']:
        ranges = selectedpoints_local['range']
        selection_bounds = {'x0': ranges['x'][0], 'x1': ranges['x'][1],
                            'y0': ranges['y'][0], 'y1': ranges['y'][1]}
    else:
        selection_bounds = {'x0': np.min(sector_sub_anal_df2[xaxis_option]), 'x1': np.max(sector_sub_anal_df2[xaxis_option]),
                            'y0': np.min(sector_sub_anal_df2[yaxis_option]), 'y1': np.max(sector_sub_anal_df2[yaxis_option])}

    # Create figure
    fig = go.Figure()
    #fig = make_subplots(rows=1, cols=2, subplot_titles=("비교시점", "분석시점"))
    # Add traces
    fig.add_trace(
        go.Scatter(
            x=sector_sub_anal_df2[xaxis_option],
            y=sector_sub_anal_df2[yaxis_option],
            mode="markers+text",
            text=sector_sub_anal_df2['stockName'],
            marker=dict(color=sector_sub_anal_df2['RSI'],
            coloraxis="coloraxis",
            )
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[sector_sub_anal_df2[xaxis_option].mean()],
            y=[sector_sub_anal_df2[yaxis_option].mean()],
            mode="markers+text",
            text=['섹터 평균'],
            marker=dict(color="black",symbol=4, size=12),
            name='평균'
        )
    )
    fig.update_traces(
        selectedpoints=selectedpoints,
        customdata=sector_sub_anal_df2.index,
        mode='markers+text', 
        #marker={ 'color': 'rgba(0, 116, 217, 0.7)', 'size': 20 }, 
        textposition='top center',
        unselected={
            'marker': { 'opacity': 0.3 }, 
            'textfont': { 'color': 'rgba(0, 0, 0, 0)'}
        }
    )
    fig.update_layout(
        template='plotly_white', 
        height=500,
        coloraxis=dict(colorscale='Bluered', cmax=100, cmin=0),
        showlegend=False,
        margin={'l': 20, 'r': 0, 'b': 15, 't': 5},
        dragmode='select',
        hovermode=False,
    )    
    x_max_range = 30
    x_min_range = -30
    y_max_range = 15
    y_min_range = -15
    if sector_sub_anal_df2[xaxis_option].max() >= 30 :
        x_max_range = sector_sub_anal_df2[xaxis_option].max() + 3
    if sector_sub_anal_df2[xaxis_option].min() <= -30 :
        x_min_range = sector_sub_anal_df2[xaxis_option].min() - 3
    if sector_sub_anal_df2[yaxis_option].max() >= 15 :
        y_max_range = sector_sub_anal_df2[xaxis_option].max() + 3
    if sector_sub_anal_df2[yaxis_option].min() <= -15 :
        y_min_range = sector_sub_anal_df2[xaxis_option].min() -3 
    # Set x-axis title
    fig.update_xaxes(title_text="<b>{}</b>".format(xaxis_option), range=[x_min_range, x_max_range])
    # Set y-axes titles
    fig.update_yaxes(title_text="<b>{}</b> ".format(yaxis_option), range=[y_min_range, y_max_range])

    rate1 = str(sector_sub_anal_df2['1일전 대비 수익률'].mean().round(2))+'%'
    rate2 = str(sector_sub_anal_df2['7일전 대비 수익률'].mean().round(2))+'%'
    
    return rate1, rate2, output1, output2, fig

@app.callback(
    Output('main_scatter_graph2', 'figure'),
    [
        Input("sector_option", "value"),
        Input("comp-date-picker-single", "date"),
        Input("market-dynamic-dropdown", "value"),
        Input("scale-dynamic-dropdown", "value"),
        Input("x_option", "value"),
        Input("y_option", "value"),
        Input("main_scatter_graph1", "selectedData"),
        Input("main_scatter_graph2", "selectedData"),
    ],
)
def update_main_graph2(input_sectorName, input_comp_date, mareket_option, scale_option, xaxis_option, yaxis_option, selection1, selection2, ):
    
    sector_sub_df = sector_df[sector_df['sectorName'] == input_sectorName]
    sector_sub_df = sector_df[sector_df['sectorName'] == input_sectorName]
    if isinstance(mareket_option, list) == False:
        mareket_option = mareket_option.split(',')
    if isinstance(scale_option, list) == False:
        scale_option = scale_option.split(',')

    sector_sub_df = sector_sub_df[sector_sub_df['Market'].isin(mareket_option)]
    sector_sub_df = sector_sub_df[sector_sub_df['Scale'].isin(scale_option)]

    comp_ago_1_day,comp_ago_7_day,comp_ago_30_day,comp_ago_90_day,comp_ago_240_day,comp_ago_360_day = setting_date(input_comp_date)

    sector_sub_comp_df = sector_sub_df[sector_sub_df['date'].isin([input_comp_date, comp_ago_1_day,comp_ago_7_day,comp_ago_30_day,comp_ago_90_day,comp_ago_240_day,comp_ago_360_day])]

    sector_sub_comp_df2 = pd.pivot_table(data=sector_sub_comp_df, index=['stockName', 'stockCode'], columns=['date'],values='price')

    sector_sub_comp_df2.columns = ['ago_360_day','ago_240_day','ago_90_day','ago_30_day','ago_7_day','ago_1_day','day']

    sector_sub_comp_df2['1일전 대비 수익률'] = ((sector_sub_comp_df2['day'] - sector_sub_comp_df2['ago_1_day']) / sector_sub_comp_df2['ago_1_day'] *100).round(2)
    sector_sub_comp_df2['7일전 대비 수익률'] = ((sector_sub_comp_df2['day'] - sector_sub_comp_df2['ago_7_day']) / sector_sub_comp_df2['ago_7_day'] *100).round(2)
    sector_sub_comp_df2['1달전 대비 수익률'] = ((sector_sub_comp_df2['day'] - sector_sub_comp_df2['ago_30_day']) / sector_sub_comp_df2['ago_30_day'] *100).round(2)
    sector_sub_comp_df2['3달전 대비 수익률'] = ((sector_sub_comp_df2['day'] - sector_sub_comp_df2['ago_90_day']) / sector_sub_comp_df2['ago_90_day'] *100).round(2)
    sector_sub_comp_df2['6달전 대비 수익률'] = ((sector_sub_comp_df2['day'] - sector_sub_comp_df2['ago_240_day']) / sector_sub_comp_df2['ago_240_day'] *100).round(2)
    sector_sub_comp_df2['1년전 대비 수익률'] = ((sector_sub_comp_df2['day'] - sector_sub_comp_df2['ago_360_day']) / sector_sub_comp_df2['ago_360_day'] *100).round(2)

    sector_sub_comp_df2 = sector_sub_comp_df2.reset_index()

    rsi_df = sector_sub_df[(sector_sub_df['date'] >=comp_ago_30_day) & (sector_sub_df['date'] <= input_comp_date)]
    rsi_df.set_index('date', inplace=True)

    rsi_rslt_df = pd.DataFrame()
    for stock in rsi_df['stockName'].unique():
        t_df = rsi_df[rsi_df['stockName'] == stock][['price']]
        t_df.insert(len(t_df.columns), "RSI", calc_RSI(t_df, 14))
        t_df['stockName'] = stock
        rsi_rslt_df = pd.concat([rsi_rslt_df, t_df])
        
    rsi_rslt_df.reset_index(inplace=True)
    rsi_rslt_df = rsi_rslt_df.round()
    rsi_rslt_df = rsi_rslt_df[rsi_rslt_df['date'] == input_comp_date]

    sector_sub_comp_df2 = pd.merge(sector_sub_comp_df2, rsi_rslt_df[['RSI', 'stockName']], on=['stockName'])

    sector_sub_comp_df2 = sector_sub_comp_df2.sort_values('stockName')
    selectedpoints = sector_sub_comp_df2.index
    for selected_data in [selection1, selection2]:
        if selected_data and selected_data['points']:
            selectedpoints = np.intersect1d(selectedpoints,
                [p['customdata'] for p in selected_data['points']])
    
    selectedpoints_local = copy.deepcopy(selection2)

    if selectedpoints_local and selectedpoints_local['range']:
        ranges = selectedpoints_local['range']
        selection_bounds = {'x0': ranges['x'][0], 'x1': ranges['x'][1],
                            'y0': ranges['y'][0], 'y1': ranges['y'][1]}
    else:
        selection_bounds = {'x0': np.min(sector_sub_comp_df2[xaxis_option]), 'x1': np.max(sector_sub_comp_df2[xaxis_option]),
                            'y0': np.min(sector_sub_comp_df2[yaxis_option]), 'y1': np.max(sector_sub_comp_df2[yaxis_option])}

    # Create figure
    fig = go.Figure()
    #fig = make_subplots(rows=1, cols=2, subplot_titles=("비교시점", "분석시점"))
    # Add traces
    fig.add_trace(
        go.Scatter(
            x=sector_sub_comp_df2[xaxis_option],
            y=sector_sub_comp_df2[yaxis_option],
            mode="markers+text", 
            text=sector_sub_comp_df2['stockName'],
            marker=dict(
                color=sector_sub_comp_df2['RSI'],
                coloraxis="coloraxis"
                )
            )
        )
    fig.add_trace(
        go.Scatter(
            x=[sector_sub_comp_df2[xaxis_option].mean()],
            y=[sector_sub_comp_df2[yaxis_option].mean()],
            mode="markers+text",
            text=['섹터 평균'],
            marker=dict(
                color="black",
                symbol=4, 
                size=12),
                name='평균'
            )
        )
    fig.update_traces(
        selectedpoints=selectedpoints,
        customdata=sector_sub_comp_df2.index,
        mode='markers+text', 
        #marker={ 'color': 'rgba(0, 116, 217, 0.7)', 'size': 20 }, 
        textposition='top center',
        unselected={
            'marker': { 'opacity': 0.3 }, 
            'textfont': { 'color': 'rgba(0, 0, 0, 0)'},
        },
    )
    fig.update_layout(
        template='plotly_white', 
        height=500,
        coloraxis=dict(colorscale='Bluered', cmax=100, cmin=0),#, tickvals=[0,20,40,60,80,100],ticktext=["0","20","40","60","80","100"]
        showlegend=False,
        margin={'l': 20, 'r': 0, 'b': 15, 't': 5},
        dragmode='select',
        hovermode=False,
    ) 
    fig.update_coloraxes(showscale=False)


    x_max_range = 30
    x_min_range = -30
    y_max_range = 15
    y_min_range = -15
    if sector_sub_comp_df2[xaxis_option].max() >= 30 :
        x_max_range = sector_sub_comp_df2[xaxis_option].max() + 3
    if sector_sub_comp_df2[xaxis_option].min() <= -30 :
        x_min_range = sector_sub_comp_df2[xaxis_option].ming() - 3
    if sector_sub_comp_df2[yaxis_option].max() >= 15 :
        y_max_range = sector_sub_comp_df2[xaxis_option].ming() + 3
    if sector_sub_comp_df2[yaxis_option].min() <= -15 :
        y_min_range = sector_sub_comp_df2[xaxis_option].min() - 3
    # Set x-axis title
    fig.update_xaxes(title_text="<b>{}</b>".format(xaxis_option), range=[x_min_range, x_max_range])
    # Set y-axes titles
    fig.update_yaxes(title_text="<b>{}</b> ".format(yaxis_option), range=[y_min_range, y_max_range])

    return fig

@app.callback(
    Output('sub_line_graph', 'figure'),
    [
        Input("anal-date-picker-single", "date"),
        Input("comp-date-picker-single", "date"),
        Input("main_scatter_graph1", "selectedData"),
        Input("main_scatter_graph2", "selectedData"),
    ],
)
def update_sub_graph(input_anal_date, input_comp_date, selection1, selection2):
    color_list = ["#B71C1C","#1A237E","#A1D99B","#006064","#F57F17","#BF360C","#FDBF6F","#FC9272","#D0D1E6","#ABD9E9","#3690C0","#F87A72","#CA6BCC","#DD3497","#4EB3D3","#FFFF33","#FB9A99","#A6D853","#D4B9DA","#AEB0B8","#CCCCCC","#EAE5D9","#C29A84"]
    fig = make_subplots(rows=1, cols=1)
    
    if selection1 == None:
        selection1 = {'points': [{'curveNumber': 0, 'pointNumber': 1, 'pointIndex': 1, 'x': -5.26, 'y': 2.44, 'customdata': 1, 'text': '삼성전자'}, {'curveNumber': 2, 'pointNumber': 0, 'pointIndex': 0, 'x': -10.555, 'y': 0.98, 'customdata': 0, 'text': '섹터 평균'}], 'range': {'x': [-13.614833843393493, 7.796883675586598], 'y': [0.5452102168237216, 3.02651605874812]}}
    if selection2 == None :
        selection2 = {'points': [{'curveNumber': 0, 'pointNumber': 1, 'pointIndex': 1, 'x': -5.26, 'y': 2.44, 'customdata': 1, 'text': '삼성전자'}, {'curveNumber': 2, 'pointNumber': 0, 'pointIndex': 0, 'x': -10.555, 'y': 0.98, 'customdata': 0, 'text': '섹터 평균'}], 'range': {'x': [-13.614833843393493, 7.796883675586598], 'y': [0.5452102168237216, 3.02651605874812]}}
    selection1.update(selection2)
    for i,color in zip(selection1['points'],color_list):
        if i['text'] == '섹터 평균':
            pass
        else:
            print(i['text'])
            # 삼성전자의 20210501~20210520의 주가데이터
            #a_name = stock_info_df[stock_info_df['stockName'] == '{}'.format(i['text'])]['stockCode'].tolist()[0]
            #a_name = a_name[1:]
            #df = stock.get_market_ohlcv_by_date(fromdate="20190501", todate="20210831", ticker=a_name)
            #time.sleep(1)
            #df = df.reset_index()
            
            df = stock_price_df[stock_price_df['stockName'] == i['text']] 
            # Add traces
            fig.add_trace(go.Scatter(x=df['date'], y=df['price'], mode="lines",
                                    line=dict(shape="linear", color=color),name= i['text'],#spline
                                    ), row=1, col=1)


    fig.update_layout(template='plotly_white', height=500,
                    xaxis=dict(
                        rangeselector=dict(
                            buttons=list([
                                dict(count=1, label="1m", step="month", stepmode="backward"),
                                dict(count=6, label="6m", step="month", stepmode="backward"),
                                dict(count=1, label="1y", step="year", stepmode="backward"),
                                dict(step="all")
                                ]
                                )
                            ),
                    rangeslider=dict(visible=True),
                    type="date",
                    )
            ) 
    # Set x-axis title
    fig.update_xaxes(title_text="<b>{}</b>".format('날짜'))
    # Set y-axes titles
    fig.update_yaxes(title_text="<b>{}</b> ".format('종가(Closed)'))

    fig.add_vline(x=input_anal_date, line_width=3, line_dash="dash", line_color="blue")
    fig.add_vline(x=input_comp_date, line_width=3, line_dash="dash", line_color="red")

    return fig
# Main
if __name__ == "__main__":
    app.run_server(debug=True)

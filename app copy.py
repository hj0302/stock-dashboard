# Import required libraries
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


# get relative data folder
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("data").resolve()

app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}],
)
app.title = "Analysis of stock market"
#server = app.server

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
    file_path = '/Users/munhyeonjong/Desktop/dash/stock/data/stock_list.json'
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
    file_path = '/Users/munhyeonjong/Desktop/dash/stock/data/stock_prices.pkl'
    price_df = pd.read_pickle(file_path)

    price_df = price_df.stack().reset_index()
    price_df.columns = ['date', 'Code_Name', 'price']
    price_df[['stockCode', 'stockName']]  = price_df['Code_Name'].str.split('_',expand=True)
    price_df.drop('Code_Name', axis=1, inplace=True)
    
    return price_df

stock_info_df = load_stock_info_df()
stock_price_df = load_stock_price_df()

sector_df = pd.merge(stock_price_df, stock_info_df[['stockCode', 'stockName', 'sectorName']], on =['stockCode', 'stockName'])


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
                        html.P("Filter by well type:", className="control_label"),
                        dcc.Dropdown(
                            id="well_statuses",
                            options=well_status_options,
                            multi=True,
                            value=list(WELL_STATUSES.keys()),
                            className="dcc_control",
                        ),
                        html.P("Filter by well type:", className="control_label"),
                        dcc.Dropdown(
                            id="well_types",
                            options=well_type_options,
                            multi=True,
                            value=list(WELL_TYPES.keys()),
                            className="dcc_control",
                        ),
                    ],
                    className="pretty_container four columns",
                    id="cross-filter-options",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [html.H6(id="well_text"), html.P("No. of Wells")],
                                    id="wells",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.H6(id="gasText"), html.P("Gas")],
                                    id="gas",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.H6(id="oilText"), html.P("Oil")],
                                    id="oil",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.H6(id="waterText"), html.P("Water")],
                                    id="water",
                                    className="mini_container",
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
                    className="pretty_container seven columns",
                ),
                html.Div(
                    [dcc.Graph(id="individual_graph")],
                    className="pretty_container five columns",
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="pie_graph")],
                    className="pretty_container seven columns",
                ),
                html.Div(
                    [dcc.Graph(id="aggregate_graph")],
                    className="pretty_container five columns",
                ),
            ],
            className="row flex-display",
        ),
    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"},
)


# Helper functions
def human_format(num):
    if num == 0:
        return "0"

    magnitude = int(math.log(num, 1000))
    mantissa = str(int(num / (1000 ** magnitude)))
    return mantissa + ["", "K", "M", "G", "T", "P"][magnitude]


def filter_dataframe(df, well_statuses, well_types, year_slider):
    dff = df[
        df["Well_Status"].isin(well_statuses)
        & df["Well_Type"].isin(well_types)
        & (df["Date_Well_Completed"] > dt.datetime(year_slider[0], 1, 1))
        & (df["Date_Well_Completed"] < dt.datetime(year_slider[1], 1, 1))
    ]
    return dff


def produce_individual(api_well_num):
    try:
        points[api_well_num]
    except:
        return None, None, None, None

    index = list(
        range(min(points[api_well_num].keys()), max(points[api_well_num].keys()) + 1)
    )
    gas = []
    oil = []
    water = []

    for year in index:
        try:
            gas.append(points[api_well_num][year]["Gas Produced, MCF"])
        except:
            gas.append(0)
        try:
            oil.append(points[api_well_num][year]["Oil Produced, bbl"])
        except:
            oil.append(0)
        try:
            water.append(points[api_well_num][year]["Water Produced, bbl"])
        except:
            water.append(0)

    return index, gas, oil, water


def produce_aggregate(selected, year_slider):

    index = list(range(max(year_slider[0], 1985), 2016))
    gas = []
    oil = []
    water = []

    for year in index:
        count_gas = 0
        count_oil = 0
        count_water = 0
        for api_well_num in selected:
            try:
                count_gas += points[api_well_num][year]["Gas Produced, MCF"]
            except:
                pass
            try:
                count_oil += points[api_well_num][year]["Oil Produced, bbl"]
            except:
                pass
            try:
                count_water += points[api_well_num][year]["Water Produced, bbl"]
            except:
                pass
        gas.append(count_gas)
        oil.append(count_oil)
        water.append(count_water)

    return index, gas, oil, water


# Create callbacks
app.clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="resize"),
    Output("output-clientside", "children"),
    [Input("count_graph", "figure")],
)


@app.callback(
    Output("aggregate_data", "data"),
    [
        Input("well_statuses", "value"),
        Input("well_types", "value"),
        Input("year_slider", "value"),
    ],
)
def update_production_text(well_statuses, well_types, year_slider):

    dff = filter_dataframe(df, well_statuses, well_types, year_slider)
    selected = dff["API_WellNo"].values
    index, gas, oil, water = produce_aggregate(selected, year_slider)
    return [human_format(sum(gas)), human_format(sum(oil)), human_format(sum(water))]


# Radio -> multi
@app.callback(
    Output("well_statuses", "value"), [Input("well_status_selector", "value")]
)
def display_status(selector):
    if selector == "all":
        return list(WELL_STATUSES.keys())
    elif selector == "active":
        return ["AC"]
    return []


# Radio -> multi
@app.callback(Output("well_types", "value"), [Input("well_type_selector", "value")])
def display_type(selector):
    if selector == "all":
        return list(WELL_TYPES.keys())
    elif selector == "productive":
        return ["GD", "GE", "GW", "IG", "IW", "OD", "OE", "OW"]
    return []


# Slider -> count graph
@app.callback(Output("year_slider", "value"), [Input("count_graph", "selectedData")])
def update_year_slider(count_graph_selected):

    if count_graph_selected is None:
        return [1990, 2010]

    nums = [int(point["pointNumber"]) for point in count_graph_selected["points"]]
    return [min(nums) + 1960, max(nums) + 1961]


# Selectors -> well text
@app.callback(
    Output("well_text", "children"),
    [
        Input("well_statuses", "value"),
        Input("well_types", "value"),
        Input("year_slider", "value"),
    ],
)
def update_well_text(well_statuses, well_types, year_slider):

    dff = filter_dataframe(df, well_statuses, well_types, year_slider)
    return dff.shape[0]


@app.callback(
    [
        Output("gasText", "children"),
        Output("oilText", "children"),
        Output("waterText", "children"),
    ],
    [Input("aggregate_data", "data")],
)
def update_text(data):
    return data[0] + " mcf", data[1] + " bbl", data[2] + " bbl"


# Selectors -> main graph
@app.callback(
    Output("main_graph", "figure"),
    [
        Input("well_statuses", "value"),
        Input("well_types", "value"),
        Input("year_slider", "value"),
    ],
    [State("lock_selector", "value"), State("main_graph", "relayoutData")],
)
def make_main_figure(
    well_statuses, well_types, year_slider, selector, main_graph_layout
):

    dff = filter_dataframe(df, well_statuses, well_types, year_slider)

    traces = []
    for well_type, dfff in dff.groupby("Well_Type"):
        trace = dict(
            type="scattermapbox",
            lon=dfff["Surface_Longitude"],
            lat=dfff["Surface_latitude"],
            text=dfff["Well_Name"],
            customdata=dfff["API_WellNo"],
            name=WELL_TYPES[well_type],
            marker=dict(size=4, opacity=0.6),
        )
        traces.append(trace)

    # relayoutData is None by default, and {'autosize': True} without relayout action
    if main_graph_layout is not None and selector is not None and "locked" in selector:
        if "mapbox.center" in main_graph_layout.keys():
            lon = float(main_graph_layout["mapbox.center"]["lon"])
            lat = float(main_graph_layout["mapbox.center"]["lat"])
            zoom = float(main_graph_layout["mapbox.zoom"])
            layout["mapbox"]["center"]["lon"] = lon
            layout["mapbox"]["center"]["lat"] = lat
            layout["mapbox"]["zoom"] = zoom

    figure = dict(data=traces, layout=layout)
    return figure


# Main graph -> individual graph
@app.callback(Output("individual_graph", "figure"), [Input("main_graph", "hoverData")])
def make_individual_figure(main_graph_hover):

    layout_individual = copy.deepcopy(layout)

    if main_graph_hover is None:
        main_graph_hover = {
            "points": [
                {"curveNumber": 4, "pointNumber": 569, "customdata": 31101173130000}
            ]
        }

    chosen = [point["customdata"] for point in main_graph_hover["points"]]
    index, gas, oil, water = produce_individual(chosen[0])

    if index is None:
        annotation = dict(
            text="No data available",
            x=0.5,
            y=0.5,
            align="center",
            showarrow=False,
            xref="paper",
            yref="paper",
        )
        layout_individual["annotations"] = [annotation]
        data = []
    else:
        data = [
            dict(
                type="scatter",
                mode="lines+markers",
                name="Gas Produced (mcf)",
                x=index,
                y=gas,
                line=dict(shape="spline", smoothing=2, width=1, color="#fac1b7"),
                marker=dict(symbol="diamond-open"),
            ),
            dict(
                type="scatter",
                mode="lines+markers",
                name="Oil Produced (bbl)",
                x=index,
                y=oil,
                line=dict(shape="spline", smoothing=2, width=1, color="#a9bb95"),
                marker=dict(symbol="diamond-open"),
            ),
            dict(
                type="scatter",
                mode="lines+markers",
                name="Water Produced (bbl)",
                x=index,
                y=water,
                line=dict(shape="spline", smoothing=2, width=1, color="#92d8d8"),
                marker=dict(symbol="diamond-open"),
            ),
        ]
        layout_individual["title"] = dataset[chosen[0]]["Well_Name"]

    figure = dict(data=data, layout=layout_individual)
    return figure


# Selectors, main graph -> aggregate graph
@app.callback(
    Output("aggregate_graph", "figure"),
    [
        Input("well_statuses", "value"),
        Input("well_types", "value"),
        Input("year_slider", "value"),
        Input("main_graph", "hoverData"),
    ],
)
def make_aggregate_figure(well_statuses, well_types, year_slider, main_graph_hover):

    layout_aggregate = copy.deepcopy(layout)

    if main_graph_hover is None:
        main_graph_hover = {
            "points": [
                {"curveNumber": 4, "pointNumber": 569, "customdata": 31101173130000}
            ]
        }

    chosen = [point["customdata"] for point in main_graph_hover["points"]]
    well_type = dataset[chosen[0]]["Well_Type"]
    dff = filter_dataframe(df, well_statuses, well_types, year_slider)

    selected = dff[dff["Well_Type"] == well_type]["API_WellNo"].values
    index, gas, oil, water = produce_aggregate(selected, year_slider)

    data = [
        dict(
            type="scatter",
            mode="lines",
            name="Gas Produced (mcf)",
            x=index,
            y=gas,
            line=dict(shape="spline", smoothing="2", color="#F9ADA0"),
        ),
        dict(
            type="scatter",
            mode="lines",
            name="Oil Produced (bbl)",
            x=index,
            y=oil,
            line=dict(shape="spline", smoothing="2", color="#849E68"),
        ),
        dict(
            type="scatter",
            mode="lines",
            name="Water Produced (bbl)",
            x=index,
            y=water,
            line=dict(shape="spline", smoothing="2", color="#59C3C3"),
        ),
    ]
    layout_aggregate["title"] = "Aggregate: " + WELL_TYPES[well_type]

    figure = dict(data=data, layout=layout_aggregate)
    return figure


# Selectors, main graph -> pie graph
@app.callback(
    Output("pie_graph", "figure"),
    [
        Input("well_statuses", "value"),
        Input("well_types", "value"),
        Input("year_slider", "value"),
    ],
)
def make_pie_figure(well_statuses, well_types, year_slider):

    layout_pie = copy.deepcopy(layout)

    dff = filter_dataframe(df, well_statuses, well_types, year_slider)

    selected = dff["API_WellNo"].values
    index, gas, oil, water = produce_aggregate(selected, year_slider)

    aggregate = dff.groupby(["Well_Type"]).count()

    data = [
        dict(
            type="pie",
            labels=["Gas", "Oil", "Water"],
            values=[sum(gas), sum(oil), sum(water)],
            name="Production Breakdown",
            text=[
                "Total Gas Produced (mcf)",
                "Total Oil Produced (bbl)",
                "Total Water Produced (bbl)",
            ],
            hoverinfo="text+value+percent",
            textinfo="label+percent+name",
            hole=0.5,
            marker=dict(colors=["#fac1b7", "#a9bb95", "#92d8d8"]),
            domain={"x": [0, 0.45], "y": [0.2, 0.8]},
        ),
        dict(
            type="pie",
            labels=[WELL_TYPES[i] for i in aggregate.index],
            values=aggregate["API_WellNo"],
            name="Well Type Breakdown",
            hoverinfo="label+text+value+percent",
            textinfo="label+percent+name",
            hole=0.5,
            marker=dict(colors=[WELL_COLORS[i] for i in aggregate.index]),
            domain={"x": [0.55, 1], "y": [0.2, 0.8]},
        ),
    ]
    layout_pie["title"] = "Production Summary: {} to {}".format(
        year_slider[0], year_slider[1]
    )
    layout_pie["font"] = dict(color="#777777")
    layout_pie["legend"] = dict(
        font=dict(color="#CCCCCC", size="10"), orientation="h", bgcolor="rgba(0,0,0,0)"
    )

    figure = dict(data=data, layout=layout_pie)
    return figure


# Selectors -> count graph
@app.callback(
    Output("count_graph", "figure"),
    [
        Input("well_statuses", "value"),
        Input("well_types", "value"),
        Input("year_slider", "value"),
    ],
)
def make_count_figure(well_statuses, well_types, year_slider):

    layout_count = copy.deepcopy(layout)

    dff = filter_dataframe(df, well_statuses, well_types, [1960, 2017])
    g = dff[["API_WellNo", "Date_Well_Completed"]]
    g.index = g["Date_Well_Completed"]
    g = g.resample("A").count()

    colors = []
    for i in range(1960, 2018):
        if i >= int(year_slider[0]) and i < int(year_slider[1]):
            colors.append("rgb(123, 199, 255)")
        else:
            colors.append("rgba(123, 199, 255, 0.2)")

    data = [
        dict(
            type="scatter",
            mode="markers",
            x=g.index,
            y=g["API_WellNo"] / 2,
            name="All Wells",
            opacity=0,
            hoverinfo="skip",
        ),
        dict(
            type="bar",
            x=g.index,
            y=g["API_WellNo"],
            name="All Wells",
            marker=dict(color=colors),
        ),
    ]

    layout_count["title"] = "Completed Wells/Year"
    layout_count["dragmode"] = "select"
    layout_count["showlegend"] = False
    layout_count["autosize"] = True

    figure = dict(data=data, layout=layout_count)
    return figure


# Main
if __name__ == "__main__":
    app.run_server(debug=True)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 01:07:13 2020

@author: TysonWu

Big help from:
https://dash.plot.ly/getting-started
https://dash.plot.ly/live-updates
https://dash.plot.ly/deployment
https://stackoverflow.com/questions/46075960/live-updating-only-the-data-in-dash-plotly

Multiple input output:
https://dash.plot.ly/getting-started-part-2
"""

import pandas as pd
import os
from datetime import datetime
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly
from dash.dependencies import Input, Output
from poisson_graph import poisson_pipeline
from signals import signal_analysis
import utils as u


def data_pipeline(game_date, source): # source is 'YYYYmmddXXXn.csv'
    event_id = source[:-4]
    data_dict, lines = u.separate_by_lines(event_id)

    feed_list_hi = []
    feed_list_low = []
    for line in lines:
        feed_list_hi.append({'x':data_dict[line]['minutes'],
                             'y':data_dict[line]['chl_hi'],
                             'mode':'lines',
                             'name':'{} - hi'.format(line)})
        feed_list_low.append({'x':data_dict[line]['minutes'],
                              'y':data_dict[line]['chl_low'],
                              'mode':'lines',
                              'name':'{} - low'.format(line)})

    # data for # total corner
    data = pd.read_csv('data/'+event_id+'.csv')
    total_corner = data[['minutes','total_corner']]
    # remove unuseful rows
    total_corner = total_corner[(total_corner.total_corner != "---") & (~total_corner.total_corner.isna())]
    total_corner['minutes'] = total_corner['minutes'].apply(
            lambda x: datetime.strptime(str(game_date+x), "%Y%m%d%H:%M:%S")) # convert to date
    total_corner = total_corner.drop_duplicates(keep='first')
    return total_corner, feed_list_hi, feed_list_low


# signal performance
def display_signal_data(peak_change):
    signal_data = signal_analysis(peak_change=peak_change)
#     signal_data = signal_data[signal_data['signal'] != 0]
    signal_data = signal_data[~signal_data['result_corner'].isna()]
#     signal_data['date'] = signal_data.event_id.apply(lambda x: x[:8])
#     signal_data['number'] = signal_data.event_id.apply(lambda x: int(x[11:]))
#     signal_data = signal_data.sort_values(by=['date','number']).reset_index(drop=True)
    signal_data = signal_data[['event_id','line','chl_hi','chl_low',
                               'peak_change','signal','result_corner',
                               'correct_prediction','return']]
    return signal_data


# def data_pipeline_poisson(game_date, source):
#     data = poisson_pipeline(source)
#
#     # split data to data_dict by line
#     lines = list(ssset(data.chl_line))
#     data_dict = {}
#     time_list = sorted(list(set(data.minutes)))
#     feed_list = []
#
#     for line in lines:
#         filtered_data = data[data.chl_line==line].sort_values(by=['minutes'])
#         data_dict[line] = pd.DataFrame({'minutes': time_list})
#         data_dict[line] = data_dict[line].merge(filtered_data, how='outer', on='minutes')
#         data_dict[line]['minutes'] = data_dict[line]['minutes'].apply(
#             lambda x: datetime.strptime(str(game_date+x), "%Y%m%d%H:%M:%S")) # convert to date
#
#
#         feed_list.append({'x':data_dict[line]['minutes'],
#                           'y':data_dict[line]['lower_prob'],
#                           'mode':'lines',
#                           'name':'< - {}'.format(line)})
#
#     return feed_list
#----------------------------------

os.chdir('/Users/TysonWu/dev/odds-crawl-app/odds-crawl-app/development/data_collection/')

# initialize app
app = dash.Dash(__name__)
server = app.server

PEAK_CHANGE = [0.98,1.04]
match_data = pd.read_csv('data/match_data.csv')
current_match = match_data.iloc[-1,]
current_match_event_id = current_match['event_id']
game_date = current_match_event_id[:8] # a string YYYYmmdd
matches = sorted([file for file in os.listdir('data/') if '202' in file],
                 reverse=True)
signal_data = display_signal_data(peak_change=PEAK_CHANGE)

# color codes
color_list = ['#FFA65A', '#E86146', '#E8469A', '#B574FF', '#5D69E8', '#54C3C7',
'#49debb','#49de7d','#84d660', '#e3d864', '#FFA65A', '#E86146', '#E8469A', '#B574FF', '#5D69E8', '#54C3C7',
'#49debb','#49de7d','#84d660', '#e3d864'
#'#f7e557', '#fc7638','#ad332a', '#de4976', '#be49de', '#8049de',
#'#4953de', '#49debb','#49de7d','#76de49','#b9de49'
    ]
defaults = ['#1f77b4','#ff7f0e'] # default muted blue, safety orange
font_color = '#c5c5c5'
grid_color = '#2f373d'
paper_bgcolor = 'rgba(0,0,0,0)'
plot_bgcolor = 'rgba(0,0,0,0)'

app.layout = html.Div(className='app__container', children=
                      [
                      html.Div(children=
                          [
                              html.H1("Live Odds Visualisation")
                              ]),
                      html.Div(className='two columns', children=
                               [
                                   html.Link(rel='stylesheet',
                                             href='/assets/stylesheet.css'
                                             ),
                                   dcc.Dropdown(id='matches-dropdown',
                                                # options=[{'label': i, 'value': i} for i in matches],
                                                value=current_match_event_id+'.csv',
                                                style={'width': '200px'}
                                                ),
                                   html.Table([
                                       html.Tr([html.Td(['Game Starting Time:']), html.Td(id='match-game-starting-time')]),
                                       html.Tr([html.Td(['League:']), html.Td(id='match-league')]),
                                       html.Tr([html.Td(['Home:']), html.Td(id='match-home')]),
                                       html.Tr([html.Td(['Away:']), html.Td(id='match-away')])
                                       ])
                                   ]),
                      html.Div(className='ten columns', children=
                               [
                                   dcc.Graph(id='chl-graph-inverse', animate=False),
                                   dcc.Graph(id='total-corner-graph', animate=False),
                                   # dcc.Graph(id='poisson-prob', animate=False),
                                   dcc.Graph(id='chl-graph', animate=False),
                                   dcc.Interval(id='interval-component',
                                                interval=10*1000,
                                                n_intervals=0),
                                   html.H4(children='Signal Performance'),
                                   html.H5(children=PEAK_CHANGE),
                                   dcc.Graph(id='performance',
                                             figure={
                                                 'data':[{
                                                     'x': signal_data.index,
                                                     'y': signal_data['return'].cumsum(),
                                                     'mode':'lines+markers'
                                                     }],
                                                 'layout':{
                                                     'font': {'color': font_color},
                                                     #'height': 720,
                                                     'axis':{'title': 'Time Since Start of Game',
                                                             'autorange': True,
                                                             'gridcolor': grid_color},
                                                     'yaxis':{'title': 'Return',
                                                              'autorange': True,
                                                              'gridcolor': grid_color},
                                                     'paper_bgcolor': paper_bgcolor,
                                                     'plot_bgcolor': plot_bgcolor,
                                                     'template': "plotly_dark"
                                                     }
                                                 }
                                             ),
                                   html.H4(children='Recent Game Results'),
                                   html.Table(
                                       # Header
                                       [html.Tr([html.Th(col) for col in signal_data.columns])] +

                                        # Body
                                       [html.Tr([
                                           html.Td(signal_data.iloc[i][col]) for col in signal_data.columns
                                           ]) for i in range(-1,-16,-1)]
                                       ),
                                   html.H4(children=' ')


                                   # dcc.Tabs(id='tabs', value='tab-1', children=[
                                   #     dcc.Tab(label='Live Graphs', value='tab-1'),
                                   #     dcc.Tab(label='Performance Metrics', value='tab-2')
                                   #     ]),
                                   # html.Div(id='tabs-content')
                                   ])
                      ])


# @app.callback(Output('tabs-content', 'children'),
#               [Input('tabs', 'value')])

# def render_content(tab):
#     if tab == 'tab-1':
#         return html.Div([
#             ])
#     elif tab == 'tab-2':
#         return html.Div([
#              ])
@app.callback(Output('matches-dropdown', 'options'),
              [Input('interval-component', 'n_intervals')])

def update_dropdown(n):
    match_info = sorted([file for file in os.listdir('data/') if '202' in file],
                     reverse=True)
    options = [{'label': i, 'value': i} for i in match_info]
    return options


@app.callback(Output('chl-graph', 'figure'),
              [Input('interval-component', 'n_intervals'),
               Input('matches-dropdown', 'value')])

def update_graph(n, source):
    _, feed_list_hi, feed_list_low = data_pipeline(game_date, source)
    traces = list()
    for (feed, color_code) in zip(feed_list_hi, color_list):
        traces.append(plotly.graph_objs.Scatter(
            x=feed['x'],
            y=feed['y'],
            name=feed['name'],
            mode=feed['mode'],
            line=dict(width=1.3, dash='solid', color=color_code)
            ))
    for (feed, color_code) in zip(feed_list_low, color_list):
        traces.append(plotly.graph_objs.Scatter(
            x=feed['x'],
            y=feed['y'],
            name=feed['name'],
            mode=feed['mode'],
            line=dict(width=1.3, dash='dot', color=color_code)
            ))


    layout = plotly.graph_objs.Layout(
        title={'text':'Live Corner HiLow Odds - {}'.format(
            source[:-4])},
        font={'color': font_color},
        height=540,
        xaxis={'title': 'Time Since Start of Game',
               'autorange': True,
               'gridcolor': grid_color},
        yaxis={'title': 'Odds',
               'autorange': True,
               'gridcolor': grid_color},
        paper_bgcolor=paper_bgcolor,
        plot_bgcolor=plot_bgcolor,
        template="plotly_dark"
    )
    return {'data': traces, 'layout': layout}


@app.callback(Output('total-corner-graph', 'figure'),
              [Input('interval-component', 'n_intervals'),
               Input('matches-dropdown', 'value')])

def update_graph(n, source):
    total_corner, _, _ = data_pipeline(game_date, source)
    traces = list()
    traces.append(plotly.graph_objs.Scatter(
        x=total_corner['minutes'],
        y=total_corner['total_corner'],
        name='Corners',
        mode='lines',
        line=dict(dash='solid', color=defaults[0])
        ))

    layout = plotly.graph_objs.Layout(
        title={'text': 'Total corner - {}'.format(source[:-4])},
        font={'color': font_color},
        height=300,
        xaxis={'title': 'Time Since Start of Game',
                'autorange': True,
                'gridcolor': grid_color},
        yaxis={'title': 'Number of Corners',
                'autorange': True,
                'gridcolor': grid_color},
        paper_bgcolor=paper_bgcolor,
        plot_bgcolor=plot_bgcolor,
        template="plotly_dark",
        showlegend=True
    )
    return {'data': traces, 'layout': layout}


# @app.callback(Output('poisson-prob', 'figure'),
#               [Input('interval-component', 'n_intervals'),
#               Input('matches-dropdown', 'value')])
#
# def update_graph(n, source):
#     feed_list = data_pipeline_poisson(game_date, source)
#     traces = list()
#     for (feed, color_code) in zip(feed_list, color_list):
#         traces.append(plotly.graph_objs.Scatter(
#             x=feed['x'],
#             y=feed['y'],
#             name=feed['name'],
#             mode=feed['mode'],
#             line=dict(width=1.3, dash='solid', color=color_code)
#             ))
#
#     layout = plotly.graph_objs.Layout(
#         title={'text': 'Live Poisson Probability'.format(
#             source[:-4])},
#         font={'color': font_color},
#         height=420,
#         xaxis={'title': 'Time Since Start of Game',
#                 'autorange': True,
#                 'gridcolor': grid_color},
#         yaxis={'title': 'Probability',
#                 'autorange': True,
#                 'gridcolor': grid_color},
#         paper_bgcolor=paper_bgcolor,
#         plot_bgcolor=plot_bgcolor,
#         template="plotly_dark"
#     )
#     return {'data': traces, 'layout': layout}


@app.callback(Output('chl-graph-inverse', 'figure'),
              [Input('interval-component', 'n_intervals'),
              Input('matches-dropdown', 'value')])

def update_graph(n, source):
    _, feed_list_hi, feed_list_low = data_pipeline(game_date, source)
    traces = list()
    for (feed, color_code) in zip(feed_list_hi, color_list):
        traces.append(plotly.graph_objs.Scatter(
            x=feed['x'],
            y=1/feed['y'],
            name=feed['name'],
            mode=feed['mode'],
            line=dict(width=1.3, dash='solid', color=color_code)
            ))
    for (feed, color_code) in zip(feed_list_low, color_list):
        traces.append(plotly.graph_objs.Scatter(
            x=feed['x'],
            y=1/feed['y'],
            name=feed['name'],
            mode=feed['mode'],
            line=dict(width=1.3, dash='dot', color=color_code)
            ))

    layout = plotly.graph_objs.Layout(
        title={'text': 'Live Corner HiLow - Implied Probability - {}'.format(
            source[:-4])},
        font={'color': font_color},
        height=540,
        xaxis={'title': 'Time Since Start of Game',
                'autorange': True,
                'gridcolor': grid_color},
        yaxis={'title': 'Probability',
                'autorange': True,
                'gridcolor': grid_color},
        paper_bgcolor=paper_bgcolor,
        plot_bgcolor=plot_bgcolor,
        template="plotly_dark"
    )
    return {'data': traces, 'layout': layout}


@app.callback(
    [Output('match-game-starting-time', 'children'),
     Output('match-league', 'children'),
     Output('match-home', 'children'),
     Output('match-away', 'children')],
    [Input('matches-dropdown', 'value')])

def update_match_info(source):
    match = match_data[match_data.event_id == source[:-4]] # minus '.csv'
    return match.game_starting_time, match.league, match.home, match.away


if __name__ == "__main__":
    app.run_server(debug=True, use_reloader=False)

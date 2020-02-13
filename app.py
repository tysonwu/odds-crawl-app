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
"""
import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly
from dash.dependencies import Input, Output

from game_info import game_data
# from crawler import get_event_id

def data_pipeline(data_path):
    data = pd.read_csv(data_path)

    # split data to data_dict by line
    lines = list(set(data.line))
    data_dict = {}
    time_list = sorted(list(set(data.minutes)))
    # time_range = [data['minutes'].values.min(), data['minutes'].values.max()]
    # odd_range = [data[['corner_hi','corner_low']].min().min(), 
    #              data[['corner_hi','corner_low']].max().max()]
    for line in lines:
        filtered_data = data[data.line==line][['minutes', 'corner_hi', 'corner_low']].sort_values(
            by=['minutes'])
        data_dict[line] = pd.DataFrame({'minutes': time_list})
        data_dict[line] = data_dict[line].merge(filtered_data, 
                                                how='outer', on='minutes')
    return data_dict, lines

def graph_data_dict(data_dict, lines):
    feed_list = []
    for line in lines:
        for hilow in ['hi','low']:
            feed_list.append({'x':data_dict[line]['minutes'], 
                              'y':data_dict[line]['corner_{}'.format(hilow)],
                              'mode':'lines+markers', 
                              'name':'{} - {}'.format(line, hilow)})
    return feed_list

#----------------------------------

external_stylesheets = ['https://codepen.io/chriddyp/pen/dZVMbK.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

app.layout = html.Div(children=[
    html.H1(children='Corner HiLow Visualisation'),
    
    html.Div(children='''
        A live plot for corner hilow odds trends.
    '''),

    dcc.Graph(id='chl-graph', animate=False),
    
    dcc.Interval(id='interval-component', 
                 interval=10*1000, 
                 n_intervals=0)
])

@app.callback(Output('chl-graph', 'figure'), 
              [Input('interval-component', 'n_intervals')])

def update_graph(n):
    data_dict, lines= data_pipeline(data_path)
    feed_dict = graph_data_dict(data_dict, lines)
    traces = list()
    for feed in feed_dict:
        traces.append(plotly.graph_objs.Scatter(
            x=feed['x'],
            y=feed['y'],
            name=feed['name'],
            mode=feed['mode'],
            line=dict(width=1.2),
            marker=dict(size=3),
            ))

    layout = plotly.graph_objs.Layout(
        title='Live Corner HiLow Odds',
        height=720,
        xaxis={'title': 'Time Since Start of Game', 
               'autorange': True},
        yaxis={'title': 'Odds', 
               'autorange': True}
    )
    return {'data': traces, 'layout': layout}
    
if __name__ == '__main__':
    game = game_data()
    data_path = 'data/'+game.event_id+'.csv'
    app.run_server(debug=True)

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
from datetime import datetime
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly
from dash.dependencies import Input, Output


def data_pipeline(data_path, game_date):
    data = pd.read_csv(data_path)

    # split data to data_dict by line
    lines = list(set(data.chl_line))
    data_dict = {}
    time_list = sorted(list(set(data.minutes)))

    for line in lines:
        filtered_data = data[data.chl_line==line][['minutes', 'chl_line', 'chl_hi', 'chl_low']].sort_values(
            by=['minutes'])
        data_dict[line] = pd.DataFrame({'minutes': time_list})
        data_dict[line] = data_dict[line].merge(filtered_data,
                                                how='outer', on='minutes')
        data_dict[line]['minutes'] = data_dict[line]['minutes'].apply(
            lambda x: datetime.strptime(str(game_date+x), "%Y%m%d%H:%M:%S")) # convert to date

    feed_list_hi = []
    feed_list_low = []
    for line in lines:
        feed_list_hi.append({'x':data_dict[line]['minutes'],
                             'y':data_dict[line]['chl_hi'],
                             'z':data_dict[line]['chl_line'],
                             'mode':'lines',
                             'name':'{} - hi'.format(line)})
        feed_list_low.append({'x':data_dict[line]['minutes'],
                              'y':data_dict[line]['chl_low'],
                              'z':data_dict[line]['chl_line'],
                              'mode':'lines',
                              'name':'{} - low'.format(line)})
    return feed_list_hi, feed_list_low

#----------------------------------

# external_stylesheets = ['https://codepen.io/chriddyp/pen/dZVMbK.css']
# external_stylesheets = ['https://unpkg.com/purecss@1.0.1/build/pure-min.css']

app = dash.Dash(__name__)
server = app.server

app.layout = html.Div(children=[
    # html.H1(children='Corner HiLow Visualisation'),

    # html.Div(children='''
    #     A live plot for corner hilow odds trends.
    # '''),
    html.Link(
        rel='stylesheet',
        href='/assets/stylesheet.css'
    ),
    
    dcc.Graph(id='chl-graph', animate=False),

    dcc.Graph(id='chl-graph-inverse', animate=False),

    dcc.Interval(id='interval-component',
                 interval=10*1000,
                 n_intervals=0)
])

# color_list = ['#a50026','#d73027',
#               '#f46d43','#fdae61',
#               '#fee090','#ffffbf',
#               '#e0f3f8','#abd9e9',
#               '#74add1','#4575b4',
#               '#313695']

color_list = [
    '#FFA65A',
    '#E86146',
    '#E8469A',
    '#B574FF',
    '#54C3C7',
    '#5D69E8',
    '#68FFF3',
    '#54E886',
    '#8DFF5C'
    ]

font_color = '#c5c5c5'
grid_color = '#2f373d'
paper_bgcolor = 'rgba(0,0,0,0)'
plot_bgcolor='rgba(0,0,0,0)'

@app.callback(Output('chl-graph', 'figure'),
              [Input('interval-component', 'n_intervals')])


def update_graph(n):
    # color_list = ['#1f77b4','#ff7f0e',
    #               '#2ca02c','#d62728',
    #               '#9467bd','#8c564b',
    #               '#e377c2','#7f7f7f',
    #               '#bcbd22','#17becf']
    feed_list_hi, feed_list_low = data_pipeline(data_path, game_date)
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
            current_job_event_id)},
        font={'color': font_color},
        height=300,
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


@app.callback(Output('chl-graph-inverse', 'figure'),
              [Input('interval-component', 'n_intervals')])

def update_graph(n):
    feed_list_hi, feed_list_low = data_pipeline(data_path, game_date)
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
            current_job_event_id)},
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

job_history = pd.read_csv('data/job_history.csv')
current_job = job_history.iloc[-1,]
current_job_id, current_job_event_id = current_job['job_id'], current_job['event_id']
game_date = current_job_event_id[:8] # a string YYYYmmdd
data_path = 'data/'+current_job_event_id+'.csv'
app.run_server(debug=True, use_reloader=False)

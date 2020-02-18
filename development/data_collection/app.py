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

os.chdir('/Users/TysonWu/dev/odds-crawl-app/odds-crawl-app/development/data_collection/')

match_data = pd.read_csv('data/match_data.csv')
current_match = match_data.iloc[-1,]
current_match_event_id = current_match['event_id']
game_date = current_match_event_id[:8] # a string YYYYmmdd
    

def data_pipeline(game_date, source): # source is 'YYYYmmdd.csv'
    data_path = 'data/'+source
    data = pd.read_csv(data_path)
    data = data[data.chl_low != '---']

    # split data to data_dict by line
    lines = list(set(data.chl_line))
    data_dict = {}
    time_list = sorted(list(set(data.minutes)))

    for line in lines:
        filtered_data = data[data.chl_line==line][['minutes', 'total_corner', 'chl_line', 'chl_hi', 'chl_low']].sort_values(
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
                             'total_corner':data_dict[line]['total_corner'],
                             'mode':'lines',
                             'name':'{} - hi'.format(line)})
        feed_list_low.append({'x':data_dict[line]['minutes'],
                              'y':data_dict[line]['chl_low'],
                              'total_corner':data_dict[line]['total_corner'],
                              'mode':'lines',
                              'name':'{} - low'.format(line)})
        
    total_corner = data[['minutes','total_corner']]
    total_corner['minutes'] = total_corner['minutes'].apply(
            lambda x: datetime.strptime(str(game_date+x), "%Y%m%d%H:%M:%S")) # convert to date
    total_corner = total_corner.drop_duplicates(keep='first')
    return total_corner, feed_list_hi, feed_list_low

#----------------------------------

# external_stylesheets = ['https://codepen.io/chriddyp/pen/dZVMbK.css']
# external_stylesheets = ['https://unpkg.com/purecss@1.0.1/build/pure-min.css']

app = dash.Dash(__name__)
server = app.server

matches = sorted([file for file in os.listdir('data/') if '202' in file], 
                 reverse=True)

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
                                                options=[{'label': i, 'value': i} for i in matches],
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
                                   dcc.Graph(id='chl-graph', animate=False),
                                   dcc.Graph(id='total-corner-graph', animate=False),
                                   dcc.Graph(id='chl-graph-inverse', animate=False),
                                   dcc.Interval(id='interval-component',
                                                interval=10*1000,
                                                n_intervals=0)
                                   ])
                      ])

color_list = [
    '#FFA65A',
    '#E86146',
    '#E8469A',
    '#B574FF',
    '#5D69E8',
    '#54C3C7',
    '#61FFB0',
    '#8DFF5C',
    '#edf05d',
    '#d43353',
    '#8a66ff',
    '#3e84ed',
    '#3eedc1',
    '#d4d4d4',
    ]

font_color = '#c5c5c5'
grid_color = '#2f373d'
paper_bgcolor = 'rgba(0,0,0,0)'
plot_bgcolor='rgba(0,0,0,0)'

@app.callback(Output('chl-graph', 'figure'),
              [Input('interval-component', 'n_intervals'),
               Input('matches-dropdown', 'value')])

def update_graph(n, source):
    # color_list = ['#1f77b4','#ff7f0e',
    #               '#2ca02c','#d62728',
    #               '#9467bd','#8c564b',
    #               '#e377c2','#7f7f7f',
    #               '#bcbd22','#17becf']
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
            source)},
        font={'color': font_color},
        height=420,
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
        mode='lines',
        line=dict(width=1.3, dash='solid', color=color_list[-2])
        ))
    
    layout = plotly.graph_objs.Layout(
        title={'text': 'Total corner'},
        font={'color': font_color},
        height=360,
        xaxis={'title': 'Time Since Start of Game',
                'autorange': True,
                'gridcolor': grid_color},
        yaxis={'title': 'Number of Corners',
                'autorange': True,
                'gridcolor': grid_color},
        paper_bgcolor=paper_bgcolor,
        plot_bgcolor=plot_bgcolor,
        template="plotly_dark"
    )
    return {'data': traces, 'layout': layout}


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
            source)},
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

# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import os
from datetime import datetime, time
import warnings
warnings.filterwarnings("ignore")
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px




def graph(x,y): # x -> list, y -> list, title -> string
    fig = px.line(x=x, y=y)
    fig.show()
#     sns.set()
#     fig=plt.figure(figsize=(18, 6))
#     plt.plot(x, y)
#     plt.title(title)
#     plt.show()


def remove_empty_rows(df):
    try:
        df = df[(~df.total_corner.isna()) & (df.total_corner!="---") & (df.total_corner!=" ---")]
    except:
        pass
    df = df[(~df.chl_line.isna()) & (df.chl_line!="---")]
    df = df[(~df.chl_hi.isna()) & (df.chl_hi!="---")]
    df = df[(~df.chl_low.isna()) & (df.chl_low!="---")]

    try:
        df['total_corner'] = df['total_corner'].apply(pd.to_numeric)
    except:
        pass
    df['chl_line'] = df['chl_line'].apply(pd.to_numeric)
    df['chl_hi'] = df['chl_hi'].apply(pd.to_numeric)
    df['chl_low'] = df['chl_low'].apply(pd.to_numeric)
    return df


def lowest_odd(x): # x is a 2D list [[a,b,c,d],[a,b,c,d],[a,b,c,d]] 4 elements
    odd = 99
    i = 0
    for pos, list in enumerate(x):
        if list[2] <= odd: # compare chl_low
            odd = list[2]
            i = pos
    return x[i]


def separate_by_lines(event_id): # read event_id -> reads data file in crawled format
    data = pd.read_csv('data/'+event_id+'.csv')
    data = remove_empty_rows(data)

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
            lambda x: datetime.strptime(str(event_id[:8]+x), "%Y%m%d%H:%M:%S")) # convert to date
    return data_dict, lines # return separated data by dict and list of lines

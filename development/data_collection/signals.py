# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import os
from datetime import datetime, time
import utils as u


def signal_rules(event_id, data, t, min_peak_change):
    # create peak df
    data['odd_change'] = data.chl_low/data.chl_low.shift(1)
    data['peak'] = np.where(data.odd_change > 1, 1, 0)
    peaks = data[data.peak == 1]
    peaks['peak_change'] = peaks.chl_low/peaks.chl_low.shift(1)
    peaks['peak_change'] = peaks.peak_change.apply(lambda x: round(x,4))

    # apply signal rules---------------------------------------
    peaks['signal'] = np.where(peaks.peak_change < min_peak_change, 1,
                              np.where(peaks.peak_change > 1.01,-1,0))
    # signal = 1 means that we predict results will be lower than chl_line, -1 vice versa
    peaks = peaks[peaks.minutes >= datetime.combine(datetime.strptime(event_id[:8],"%Y%m%d"), t)]
    #----------------------------------------------------------
    return peaks


def return_calc(signal_list):
    # merge current results
    result = pd.read_csv('/Users/TysonWu/dev/odds-crawl-app/odds-crawl-app/development/result_collection/match_corner_result.csv')
    signals = signal_list.merge(result[['event_id', 'result_corner']], how='inner', on='event_id')

    # exclude games without results
    signals = signals[~signals.result_corner.isna()]

    # calculate return
    signals['correct_prediction'] = np.where(signals.signal == 1,
                                             np.where(signals.line > signals.result_corner, 1, 0),
                                             np.where(signals.line < signals.result_corner, 1, 0))
    signals['return'] = np.where(signals.signal == 1,
                                 np.where(signals.correct_prediction == 1, signals.chl_low-1, -1),
                                 np.where(signals.signal == 0, 0,
                                         np.where(signals.correct_prediction == 1, signals.chl_hi-1, -1)))
    signals['return'] = signals['return'].apply(lambda x: round(x,2))
    signals.sort_values(by='event_id').reset_index(drop=True)
    return signals


def signal_analysis(t=time(1,30,0), min_peak_change=0.98): # returns a df
    signal_list = None
    for event_id in [file[:-4] for file in os.listdir('data/') if '2020' in file]:
        # data pipeline
        data = u.signal_data_pipeline(event_id)
        peaks = signal_rules(event_id, data, t, min_peak_change)

        if signal_list is None:
            if peaks.empty == False:
                signal_list = peaks.iloc[[0]]
        else:
            if peaks.empty == False:
                signal_list = pd.concat([signal_list, peaks.iloc[[0]]], ignore_index=True)

    signals = return_calc(signal_list)
    return signals


def graph_profit(signal):
    u.graph(signal.index, signal['return'].cumsum(), 'Profit over games')


def signal_check(event_id, t=time(1,30,0), min_peak_change=0.98): # input an event_id of live game and check if it is a bet signal_list
    signal_row = None
    live_data = u.signal_data_pipeline(event_id)
    peaks = signal_rules(event_id, live_data, t, min_peak_change)
    # if signal != 0 then there is a bet action to take
    peaks = peaks[peaks['signal'] != 0]
    if peaks.empty == False:
        signal_row = peaks.iloc[[0]]
        if os.path.isfile('data/signals.csv') == True:
            signals = pd.read_csv('data/signals.csv')
            signals_exist = signals[signals['event_id']==event_id]
            if signals_exist.empty == False:
                signals.update(signal_row)
                signals.to_csv('data/signals.csv', index=False, mode="w", header=True)
            else:
                signal_row.to_csv('data/signals.csv', index=False, mode="a", header=False)
        else:
            signal_row.to_csv('data/signals.csv', index=False, mode="w", header=True)

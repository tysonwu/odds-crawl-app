# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import os
from datetime import datetime, time
import utils as u
from tqdm import tqdm
import emoji
from sql_output import write_to_db
from telegram_notifier import notify


def signal_data_pipeline(event_id):
    data = pd.read_csv('data/'+event_id+'.csv')
    # data = data[['event_id','minutes','chl_line','chl_hi','chl_low']]
    data = u.remove_empty_rows(data)
    # if remove_empty_rows removes ALL rows, then there will be an empty df
    # to prevent raise of error, only process the pipeline when df is not empty
    # if df is empty, return None
    if data.empty == False:
        data['line_odds'] = data.apply(lambda x: [x.chl_line, x.chl_hi, x.chl_low], axis = 1)
        odd_list = data[['minutes', 'line_odds']].groupby('minutes')['line_odds'].apply(list).reset_index(name='line_odds')
        data = odd_list.merge(data[['event_id','minutes','total_corner']], how='inner', on='minutes')
        # data = data[['event_id', 'minutes', 'line_odds','total_corner']]

        data['min_odds_info'] = data.line_odds.apply(u.lowest_odd)
        data['line'] = data.min_odds_info.apply(lambda x: x[0])
        data['chl_low'] = data.min_odds_info.apply(lambda x: x[-1])
        data['chl_hi'] = data.min_odds_info.apply(lambda x: x[1])
        data = data[['event_id','minutes','total_corner','line','chl_hi','chl_low']]
        data['minutes'] = data['minutes'].apply(lambda x: datetime.strptime(event_id[:8]+x, "%Y%m%d%H:%M:%S"))
        return data
    else:
        return None


def signal_rules(event_id, data, t, min_peak_change):
    # create peak df
    data['odd_change'] = data.chl_low/data.chl_low.shift(1)
    # line change
    #data['line_change'] = data.line - data.line.shift(1)
    # is a peak
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
    signals = signals.sort_values(by='event_id').reset_index(drop=True)
    return signals


def signal_analysis(t=time(1,30,0), min_peak_change=0.98): # returns a df
    signal_list = None
    for event_id in tqdm([file[:-4] for file in os.listdir('data/') if '2020' in file]):
        # data pipeline
        data = signal_data_pipeline(event_id)
        # signal_data_pipeline returns none when the df is empty after undergo pipeline
        if data is not None:
            peaks = signal_rules(event_id, data, t, min_peak_change)
        else: # if df is empty then return an empty peaks df
            peaks = pd.DataFrame({})

        # if peaks df is empty then nothing will be concat
        if signal_list is None:
            if peaks.empty == False:
                signal_list = peaks.iloc[[0]]
        else:
            if peaks.empty == False:
                signal_list = pd.concat([signal_list, peaks.iloc[[0]]], ignore_index=True)

    signals = return_calc(signal_list)
    signals['date'] = signals.event_id.apply(lambda x: x[:8])
    signals['number'] = signals.event_id.apply(lambda x: int(x[11:]))
    signals = signals.sort_values(by=['date','number']).reset_index(drop=True)
    del signals['date']
    del signals['number']
    return signals


def graph_profit(signal):
    u.graph(signal.index, signal['return'].cumsum(), 'Profit over games')


def signal_check(event_id, t=time(1,30,0), min_peak_change=0.98): # input an event_id of live game and check if it is a bet signal_list
    signal_row = None
    SIGNAL_EMOJI = emoji.emojize(':triangular_flag_on_post:', use_aliases=True)*6
    
    live_data = signal_data_pipeline(event_id)
    if live_data is not None:
        peaks = signal_rules(event_id, live_data, t, min_peak_change)
        # if signal != 0 then there is a bet action to take
        peaks = peaks[peaks['signal'] != 0]
        if peaks.empty == False:
            # return the first row ie. the first signal row
            signal_row = peaks.iloc[[0]]
            # write to database
            # write_to_db(signal_row)
            # also a local file
            if os.path.isfile('data/signals.csv') == True:
                signals = pd.read_csv('data/signals.csv')
                signals_exist = signals[signals['event_id']==event_id]
                if signals_exist.empty == False:
                    signals.update(signal_row)
                    signals.to_csv('data/signals.csv', index=False, mode="w", header=True)
                else:
                    notify('{}\n{} SIGNAL FOUND: \n{}'.format(
                        SIGNAL_EMOJI, event_id, signal_row.T.to_string()))
                    signal_row.to_csv('data/signals.csv', index=False, mode="a", header=False)
            else:
                notify('{}\n{} SIGNAL FOUND: \n{}'.format(
                    SIGNAL_EMOJI, event_id, signal_row.T.to_string()))
                signal_row.to_csv('data/signals.csv', index=False, mode="w", header=True)
    else:
        pass

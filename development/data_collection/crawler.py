#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 10 04:18:23 2020

@author: TysonWu

About Chromedriver:
https://stackoverflow.com/questions/29858752/error-message-chromedriver-executable-needs-to-be-available-in-the-path
"""

# for annotations and workflow, see development.ipynb

import pandas as pd
import os
import re
import argparse
import time
import sys
import uuid
import logging
from datetime import datetime, timedelta
from selenium import webdriver
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
import emoji
from signals import signal_check
from telegram_notifier import notify


#--------------------------
path_dir = '/Users/TysonWu/dev/odds-crawl-app/odds-crawl-app/development/data_collection/'
os.chdir(path_dir)
#--------------------------


# for telegram notifications
SOCCER_EMOJI = emoji.emojize(':soccer:', use_aliases=True)*6
WARNING_EMOJI = emoji.emojize(':end:', use_aliases=True)


def check_odds_availability(driver, event_id):
    chl_path = "dCHLTable" + event_id

    try:
        driver.find_element_by_xpath("//div[@id='" + chl_path + "'" + "and @class='betTypeAllOdds']")
    except:
        driver.quit()
        notify('{}\n{}\nCrawling terminates due to unavailability of corner odds.'.format(
            WARNING_EMOJI, event_id))
        logging.error("Error finding corner hilow odds. Program will now terminate.")
        sys.exit()


def scrap_chl_odds(driver, event_id):  #  returns a dict
    entry = "1"
    chl_line_list = []
    chl_hi_list = []
    chl_low_list = []
    line_entry = []

    # skip suspended time "---" entry
    if (driver.find_element_by_id(event_id+'_CHL_H_'+entry).get_attribute('innerHTML') == "---"):
        return dict(chl_line=chl_line_list,
                    chl_hi=chl_hi_list,
                    chl_low=chl_low_list,
                    line_entry=line_entry)

    while (True):
        try:
            chl_line_list.append(
                driver.find_element_by_id(event_id+'_CHL_LINE_'+entry).get_attribute(
                    'innerHTML').strip("[]"))
            chl_hi_list.append(
                driver.find_element_by_id(event_id+'_CHL_H_'+entry).get_attribute(
                    'innerHTML'))
            chl_low_list.append(
                driver.find_element_by_id(event_id+'_CHL_L_'+entry).get_attribute(
                    'innerHTML'))
            line_entry.append(entry)
            entry = str(int(entry) + 1)
        except:
            # return things when error
            return dict(chl_line=chl_line_list,
                        chl_hi=chl_hi_list,
                        chl_low=chl_low_list,
                        line_entry=line_entry)


def scrap_had_odds(driver, event_id):  #  returns a dict
    # skip suspended time "---" entry
    if (driver.find_element_by_id(event_id+'_HAD_H').get_attribute('innerHTML') == "---"):
        return dict(home_odd=None, draw_odd=None, away_odd=None)

    home_odd = driver.find_element_by_id(event_id+'_HAD_H').get_attribute('innerHTML')
    draw_odd = driver.find_element_by_id(event_id+'_HAD_D').get_attribute('innerHTML')
    away_odd = driver.find_element_by_id(event_id+'_HAD_A').get_attribute('innerHTML')

    return dict(home_odd=home_odd, draw_odd=draw_odd, away_odd=away_odd)


def scrap_nts_odds(driver, event_id):  #  returns a dict
    # skip suspended time "---" entry
    if (driver.find_element_by_id(event_id+'_NTS_H').get_attribute('innerHTML') == "---"):
        return dict(nts_home=None, nts_no=None, nts_away=None)

    nts_home = driver.find_element_by_id(event_id+'_NTS_H').get_attribute('innerHTML')
    nts_no = driver.find_element_by_id(event_id+'_NTS_N').get_attribute('innerHTML')
    nts_away = driver.find_element_by_id(event_id+'_NTS_A').get_attribute('innerHTML')

    return dict(nts_home=nts_home, nts_no=nts_no, nts_away=nts_away)


def scrap_total_corner(driver): # return a number
    try:
        total_corner = BeautifulSoup(driver.find_element_by_class_name('spTotalCorner').get_attribute('innerHTML'),
                                     'html.parser').text.strip()
    except:
        driver.quit()
        logging.error("Error finding total corner. Program will now terminate.")
        sys.exit()

    return total_corner


def scrap_live_score(driver):  # return a dict eg. {home_score: 1, away_score: 2}
    try:
        live_score = driver.find_element_by_class_name('matchresult').get_attribute('innerHTML')
    except:
        logging.error("Error finding live score.")

    score_list = [score.strip() for score in live_score.split(':')]  # [home, away]
    # when score is not live yet (eg. before start of game), the attribute reutrns 'vs'
    # so the return dict would be {home_score: vs, away_score: vs}
    return dict(home_score=score_list[0], away_score=score_list[-1])


def scrap_status(driver):
    try:
        status = driver.find_element_by_id('headerEsst').get_attribute('innerHTML')
        status_content = BeautifulSoup(status, 'html.parser')
        status_list = [x.strip() for x in status_content.find_all(text=True) if 'react-text' not in x]
        status_string = ';'.join(status_list)
    except:
        status_string = None
        logging.error("Error finding status.")
    return status_string


def make_match_data(event_id, league, team_name_dict, game_starting_time):
    match_data = pd.DataFrame({'event_id': event_id,
                               'game_starting_time': game_starting_time,
                               'league': league,
                               'home': team_name_dict['home'],
                               'away': team_name_dict['away']}, index=[0])
    return match_data


def export_match_csv(match_data, path_dir):
    path_file = path_dir + "data/match_data.csv"

    match_data.set_index('event_id', inplace=True)

    # if file exists, if sentry also already exists then update it instead of append
    if os.path.exists(path_file) == True:
        match_history = pd.read_csv(path_file, index_col=['event_id'])
        # if need to update because event_id already existss
        if not match_history[match_history.index == match_data.index[0]].empty:
            match_history.update(match_data)
            match_history.to_csv(path_file, index=True, mode="w", header=True)
        else:
            # match_history = pd.concat([match_history, match_data], axis=0)
            match_data.to_csv(path_file, mode="a", header=False)
    else:
        match_data.to_csv(path_file, index=True, mode="w", header=True)

    logging.debug('Updated match data and exported to csv.')


def record_job_history_csv(path_dir):
    path_file = path_dir + "data/job_history.csv"
    job_id = uuid.uuid1().hex
    job_data = pd.DataFrame({'job_id': job_id,
                             'timestamp': datetime.strptime(
                                 datetime.strftime(datetime.now(),
                                                   "%Y-%m-%d %H:%M:%S"),
                                 "%Y-%m-%d %H:%M:%S")}, index=[0])

    if os.path.exists(path_file) == True:
        job_data.to_csv(path_file, index=False, mode="a", header=False)
    else:
        job_data.to_csv(path_file, index=False, mode="w", header=True)
    return job_id


# def get_match_status(s):
#     if 'Selling Time' in s:
#         return 'pre'
#     if '1st Half' in s:
#         return '1st half'
#     if 'Half Time' in s:
#         return 'half time'
#     if '2nd Half' in s:
#         return '2nd half'
#     else:
#         return None


# def adjust_minute(default_dict, status, timestamp):
#     # pre_stop = datetime.strptime(default_dict['pre'], "%Y-%m-%d %H:%M:%S")
#     # ht_stop = datetime.strptime(default_dict['half time'], "%Y-%m-%d %H:%M:%S")
#     pre_stop = default_dict['pre']
#     ht_stop = default_dict['half time']
#     # print(pre_stop)
#     # print(ht_stop)
#     if status == 'pre':
#         return timedelta(minutes=0)
#     if status == '1st half':
#         return min(timestamp-pre_stop, timedelta(minutes=45))
#     if status == 'half time':
#         return timedelta(minutes=45)
#     if status == '2nd half':
#         return min(timestamp-ht_stop, timedelta(minutes=45))+timedelta(minutes=45)


# def adjust_minute_compensate(default_dict, status, timestamp):
#     # pre_stop = datetime.strptime(default_dict['pre'], "%Y-%m-%d %H:%M:%S")
#     # ht_stop = datetime.strptime(default_dict['half time'], "%Y-%m-%d %H:%M:%S")
#     # print(default_dict['pre'])
#     # print(default_dict['half time'])
#     pre_stop = default_dict['pre']
#     ht_stop = default_dict['half time']
#     if status == 'pre':
#         return timedelta(minutes=0)
#     if status == '1st half':
#         current_dur = timestamp-pre_stop
#         if current_dur > timedelta(minutes=45):
#             return current_dur-timedelta(minutes=45)
#         else:
#             return timedelta(minutes=0)
#     if status == 'half time':
#         return timedelta(minutes=0)
#     if status == '2nd half':
#         current_dur = timestamp-ht_stop
#         if current_dur > timedelta(minutes=45):
#             return current_dur-timedelta(minutes=45)
#         else:
#             return timedelta(minutes=0)


# def update_status_change(default_dict, timestamp, match_status): # takes a dict
#     # status_df = df[['timestamp','match_status']].groupby('match_status').max()
#     # status_change.update(status_df)
#     default_dict[match_status] = timestamp
#     return default_dict


def make_odds_data(chl_odd_dict,
                   had_odd_dict,
                   nts_odd_dict,
                   total_corner,
                   live_score_dict,
                   status,
                   event_id,
                   game_starting_time,
                   timer):
    # add timestamp
    timestamp = datetime.strptime(datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"),
                                  "%Y-%m-%d %H:%M:%S")

    game_starting_time = datetime.strptime(game_starting_time, "%Y-%m-%d %H:%M:%S")
    minutes = str(max((timestamp - game_starting_time),
                      timedelta(seconds=0))) # truncate for time before game starts

    # # make adjusted time data
    # match_status = get_match_status(status)
    #
    # # update status_change
    # default_dict = update_status_change(default_dict, timestamp, match_status)
    #
    # minute_adjusted = str(adjust_minute(default_dict, match_status, timestamp))
    # minute_adjusted = re.sub('0 days ','',minute_adjusted)
    # minute_adjusted_compensate = str(adjust_minute_compensate(default_dict, match_status, timestamp))
    # minute_adjusted_compensate = re.sub('0 days ','',minute_adjusted_compensate)


    time_data = pd.DataFrame({"event_id": event_id,
                              "timestamp": timestamp,
                              "minutes": minutes,
                              "timer": timer,
                              #"minute_adjusted": minute_adjusted,
                              #"minute_adjusted_compensate": minute_adjusted_compensate,
                              "status": status,
                              #"match_status": match_status,
                              "total_corner": total_corner},index=[0])

    # append live_score data
    odds = pd.concat([time_data, pd.DataFrame(live_score_dict, index=[0])], axis=1)

    # append had odds data
    odds = pd.concat([odds, pd.DataFrame(had_odd_dict, index=[0])], axis=1)

    # append had odds data
    odds = pd.concat([odds, pd.DataFrame(nts_odd_dict, index=[0])], axis=1)

    # append corner hilow odds data
    odds = pd.concat([odds, pd.DataFrame(chl_odd_dict)], axis=1).fillna(method="ffill")
    return odds


def export_odds_csv(odds, event_id, path_dir):
    path_file = path_dir + "data/" + event_id + ".csv"

    # if file exists, write line; if file does not exist, create one and write line
    if os.path.exists(path_file) == True:
        odds.to_csv(path_file, index=False, mode="a", header=False)
    else:
        odds.to_csv(path_file, index=False, mode="w", header=True)


def initialize(url, load_sleep=15):
    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.get(url)
    time.sleep(load_sleep)  # to let the HTML load
    return driver


def scrap_sofascore(driver):
    timer = driver.find_element_by_class_name('js-details-component-startTime-container')
    time_text = timer.text.split("\n")[-1]
    return time_text


def main(crawl_interval=10):
    # record job history
    job_id = record_job_history_csv(path_dir)

    # read html from command line argument
    parser = argparse.ArgumentParser(description='Event ID as an argument')
    parser.add_argument("--event_id")
    args = parser.parse_args()
    event_id = args.event_id

    # initialize logger
    logging.basicConfig(filename='log/{}_{}.log'.format(event_id, job_id),level=logging.INFO)
    logging.info("Start running crawl script...")

    # # override
    # web_url = 'https://bet.hkjc.com/football/odds/odds_inplay_all.aspx?lang=EN&tmatchid=b763c364-80ce-43c4-b663-68c7de6ec9a2'
    logging.info(event_id)

    # read schedule
    schedule = pd.read_csv(path_dir+"data/schedule.csv")
    # returns latest row in case there are duplicates
    # if it is empty then something gone wrong
    try:
        game_info = schedule[schedule['event_id'] == event_id].iloc[-1,]
    except:
        logging.warning("Found no such Event ID in schedule.csv. Program will now terminate.")
        sys.exit()

    url = game_info['game_url']
    league = game_info['league']
    game_starting_time = game_info['time']
    team_name_dict = dict(home=game_info['home'], away=game_info['away'])

    # sofascore timer
    sofascore_url = game_info['sofascore_url']

    # initialize a dict of max time in each status
    # this is a dict to be continuously loop and update
    # if the data file existed already, then the crawl is a continued crawl from previous
    # gst_strip = datetime.strptime(game_starting_time, "%Y-%m-%d %H:%M:%S")
    # default_list = [gst_strip,gst_strip,gst_strip,gst_strip]

    # with the default_dict and without checking whether part of the data in the game already exists,
    # if the crawling re-runs on the same game, the adjusted time will not be accurate.

    # default_dict = pd.DataFrame({'match_status':['pre','1st half','half time','2nd half'],
    #                              'timestamp':datetime.strptime(game_starting_time, "%Y-%m-%d %H:%M:%S")}).set_index('match_status')
    # if os.path.exists(path_dir+"data/"+event_id+".csv") == True:
    #     initial_data = pd.read_csv(path_dir+"data/"+event_id+".csv")
    #     initial_data = initial_data[['timestamp','match_status']].groupby('match_status').max()
    #     # do an initial update
    #     default_dict.update(initial_data)
    # default_dict = default_dict.to_dict()['timestamp']

    logging.info('URL: '+url)
    logging.info('Event ID: '+event_id)
    logging.info('Game starting time: '+game_starting_time)

    notify('{} \nStart crawling for {}.\nGame starting time: {}\nLeauge: {}\n{} VS {}'.format(
        SOCCER_EMOJI, event_id, game_starting_time, league,
        team_name_dict['home'], team_name_dict['away']))

    # initialize hkjc driver
    driver = initialize(url)

    try:
        # initialize sofascore url
        driver_timer = initialize(sofascore_url)
    except:
        notify('Sofascore timer initialization error.')

    # first crawl
    # check odd content availability; if no corner hilow odds then terminate program
    check_odds_availability(driver=driver, event_id=event_id)

    # make and export match information
    match_data = make_match_data(event_id, league, team_name_dict, game_starting_time)
    export_match_csv(match_data, path_dir)

    # signal trigger
    SIGNAL_TRIGGER = True # when false, do not do signal check
    # sequantial loop
    while True:
        # check odd content availability; if no corner hilow odds then terminate program
        check_odds_availability(driver=driver, event_id=event_id)

        # get timer from sofascore
        try:
            timer = scrap_sofascore(driver_timer)
        except:
            timer = None
            logging.error('Sofascore driver error.')

        live_score_dict = scrap_live_score(driver)
        status = scrap_status(driver)
        total_corner = scrap_total_corner(driver)
        chl_odds_dict = scrap_chl_odds(driver, event_id)
        had_odds_dict = scrap_had_odds(driver, event_id)
        nts_odds_dict = scrap_nts_odds(driver, event_id)
        odds = make_odds_data(chl_odds_dict, # dict
                              had_odds_dict, # dict
                              nts_odds_dict, # dict
                              total_corner, # number
                              live_score_dict, # dict
                              status, # string
                              event_id, # string
                              game_starting_time,
                              timer) # string
                              #default_dict) # dict containing datetimes
        # logging.info(default_dict)

        # if not odds.total_corner.isnull().values.any():
        export_odds_csv(odds, event_id, path_dir)
        # if there is a bet signal, output the action row to signal.csv
        if SIGNAL_TRIGGER == True:
            SIGNAL_TRIGGER = signal_check(driver, event_id, team_name_dict, url, SIGNAL_TRIGGER)
        # telegram notify
        # notify(random_stuff)
        logging.info("Done crawling on {}. Wait {} seconds for another crawl...".format(
            datetime.now(), crawl_interval))
        time.sleep(crawl_interval)
        logging.info("Refresh, start crawling again...")


if __name__ == "__main__":
    main()

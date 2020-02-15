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
import time
import sys
import re
import uuid
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

# game_info.py
from game_info import game_data


def parse_scrap_event_id(driver, game_starting_time):
    try:
        game_info = driver.find_element_by_id("litMDay")

    except:
        driver.quit()
        print("Error finding weekday and game number. Program will now terminate.")
        sys.exit()

    print("Found weekday and game number.")
    game_info_content = game_info.get_attribute("innerHTML")

    # getting a content such as 12/02 18:30
    game_info_content = game_info_content.replace(" ", "")  # get eg. WED1, FRI30
    start_date, start_time = game_starting_time.split()[0], game_starting_time.split()[1]
    start_date = datetime.strptime(start_date, "%Y-%m-%d")  # str to datetime
    # str to datetime to str
    start_time = datetime.strptime(start_time, "%H:%M:%S").strftime("%H:%M") 
    if (start_time <= "12:00"):  
        # because of timezone diff, if before 12:00 then still count as yesterday's game
        start_date = start_date - timedelta(days=1)
    start_date = datetime.strftime(start_date, "%Y%m%d")  # datetime to str
    return start_date + game_info_content


def parse_scrap_team_names(driver):  # returns a dict {home: xxx, away: yyy}
    try:
        home_name = driver.find_element_by_xpath('//*[@id="litTeamsStr"]/span/span[1]')
        away_name = driver.find_element_by_xpath('//*[@id="litTeamsStr"]/span/span[3]')

    except:
        driver.quit()
        print("Error finding team names. Program will now terminate.")
        sys.exit()

    print("Found team names.")
    # home team
    home_name_content = BeautifulSoup(home_name.get_attribute('innerHTML'), 'html.parser').text
    home_name_content = re.search('(.*)\(Home\)',home_name_content).group(1).strip()
    
    # away team
    away_name_content = BeautifulSoup(away_name.get_attribute('innerHTML'), 'html.parser').text
    away_name_content = re.search('(.*)\(Away\)',away_name_content).group(1).strip()
    return dict(home=home_name_content, away=away_name_content)


def check_odds_availability(driver, odd_type, event_id):
    if odd_type == 'chl':
        path_id = "dCHLTable" + event_id
    else:
        path_id = None

    try:
        driver.find_element_by_xpath(
            "//div[@id='" + path_id + "'" + "and @class='betTypeAllOdds']")

    except:
        driver.quit()
        print("Error finding corner hilow odds. Program will now terminate.")
        sys.exit()


def scrap_odds(driver, event_id):  #  returns a dict
    entry = "1"
    chl_line_list = []
    chl_hi_list = []
    chl_low_list = []

    # skip suspended time "---" entry
    if (driver.find_element_by_id(event_id+'_CHL_H_'+entry).get_attribute('innerHTML') == "---"):
        return dict(chl_line=chl_line_list, chl_hi=chl_hi_list, chl_low=chl_low_list)

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
            entry = str(int(entry) + 1)
        except:
            # return things when error
            return dict(chl_line=chl_line_list, chl_hi=chl_hi_list, chl_low=chl_low_list)


def scrap_live_score(driver):  # return a dict eg. {home_score: 1, away_score: 2}
    try:
        live_score = driver.find_element_by_class_name('matchresult').get_attribute('innerHTML')
    except:
        driver.quit()
        print("Error finding live score. Program will now terminate.")
        sys.exit()
    
    score_list = [score.strip() for score in live_score.split(':')]  # [home, away]
    # when score is not live yet (eg. before start of game), the attribute reutrns 'vs'
    # so the return dict would be {home_score: vs, away_score: vs}
    return dict(home_score=score_list[0], away_score=score_list[-1])


def make_match_data(event_id, team_name_dict, game_starting_time):
    match_data = pd.DataFrame({'event_id': event_id,
                               'game_starting_time': game_starting_time,
                               'home': team_name_dict['home'],
                               'away': team_name_dict['away']}, index=[0])
    return match_data


def export_match_csv(match_data, path_dir):
    path_file = path_dir + "match_data.csv"
    
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
    
    print('Updated match data and exported to csv.')
    

def record_job_history_csv(event_id, path_dir):
    path_file = path_dir + "job_history.csv"
    job_data = pd.DataFrame({'job_id': uuid.uuid1().hex, 
                             'event_id': event_id,
                             'timestamp': datetime.strptime(
                                 datetime.strftime(datetime.now(), 
                                                   "%Y-%m-%d %H:%M:%S"), 
                                 "%Y-%m-%d %H:%M:%S")}, index=[0])
    
    if os.path.exists(path_file) == True:
        job_data.to_csv(path_file, index=False, mode="a", header=False)
    else:
        job_data.to_csv(path_file, index=False, mode="w", header=True)

    print('Created job_id: {}'.format(job_data['job_id']))


def make_odds_data(odd_dict, live_score_dict, event_id, game_starting_time):
    # add timestamp
    timestamp = datetime.strptime(datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"), 
                                  "%Y-%m-%d %H:%M:%S")

    game_starting_time = datetime.strptime(game_starting_time, "%Y-%m-%d %H:%M:%S")
    minutes = str(max((timestamp - game_starting_time), 
                      timedelta(seconds=0))) # truncate for time before game starts

    time_data = pd.DataFrame({"event_id": event_id,
                              "timestamp": timestamp,
                              "minutes": minutes},index=[0])

    # append live_score data
    odds = pd.concat([time_data, pd.DataFrame(live_score_dict, index=[0])], axis=1)

    # append corner hilow odds data
    odds = pd.concat([odds, pd.DataFrame(odd_dict)], axis=1).fillna(method="ffill")
    return odds


def export_odds_csv(odds, event_id, path_dir):
    path_file = path_dir + event_id + ".csv"

    # if file exists, write line; if file does not exist, create one and write line
    if os.path.exists(path_file) == True:
        odds.to_csv(path_file, index=False, mode="a", header=False)
    else:
        odds.to_csv(path_file, index=False, mode="w", header=True)


def initialize(url, load_sleep=7):
    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.get(url)
    time.sleep(load_sleep)  # to let the HTML load
    return driver


def main(crawl_interval=10):
    print("Start running crawl script...")

    game = game_data()
    driver = initialize(game.url)
    
    # get event_id
    event_id = parse_scrap_event_id(driver, game.game_starting_time)
    
    # record job history
    record_job_history_csv(event_id, game.path_dir)

    # get team info
    team_name_dict = parse_scrap_team_names(driver)
    
    # check odd content availability; if no corner hilow odds then terminate program
    check_odds_availability(driver=driver, odd_type='chl', event_id=event_id)
    
    # make and export match information
    match_data = make_match_data(event_id, team_name_dict, game.game_starting_time)
    export_match_csv(match_data, game.path_dir)

    while True:
        # check odd content availability; if no corner hilow odds then terminate program
        check_odds_availability(driver=driver, odd_type='chl', event_id=event_id)
        
        live_score_dict = scrap_live_score(driver)
        odds_dict = scrap_odds(driver, event_id)
        odds = make_odds_data(odds_dict, 
                              live_score_dict,
                              event_id, 
                              game.game_starting_time)
        if not odds.chl_line.isnull().values.any():
            export_odds_csv(odds, event_id, game.path_dir)

        print("Done crawling on {}. Wait {} seconds for another crawl...".format(
            datetime.now(), crawl_interval))
        time.sleep(crawl_interval)
        print("Refresh, start crawling again...")

    print("Crawling done. Termination of script.")


if __name__ == "__main__":
    main()

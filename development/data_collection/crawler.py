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
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
# game_info.py
from game_info import game_data

def parse_web(driver, event_id, game_starting_time):
    # odds table div id name
    chl_id = 'dCHLTable'+event_id
    
    try:
        chlodds = driver.find_element_by_xpath("//div[@id='"+chl_id+"'"+"and @class='betTypeAllOdds']")
        chlodds_content = chlodds.get_attribute('innerHTML')

    except:
        print('No Corner HiLow content found.')
        return None

    soup = BeautifulSoup(chlodds_content, 'html.parser')
    return soup


def parse_scrape_event_id(driver, game_starting_time):
    try:
        game_info = driver.find_element_by_id('litMDay')
    
    except:
        driver.quit()
        print('Error finding weekday and game number. Program will now terminate.')
        sys.exit()
    
    print('Found weekday and game number.')
    game_info_content = game_info.get_attribute('innerHTML')
    
    # getting a content such as 12/02 18:30    
    game_info_content = game_info_content.replace(' ','') # get eg. WED1, FRI30
    start_date, start_time = game_starting_time.split()[0], game_starting_time.split()[1]
    start_date = datetime.strptime(start_date, '%Y-%m-%d') # str to datetime
    start_time = datetime.strptime(start_time, '%H:%M:%S').strftime('%H:%M') # str to datetime to str
    if start_time <= '12:00': # because of timezone diff, if before 12:00 then still count as yesterday's game
        start_date = start_date - timedelta(days=1)
    start_date = datetime.strftime(start_date, '%Y%m%d') # datetime to str
    return (start_date+game_info_content)

def scrape_team_names():
    pass
    return None

def scrape_odds(soup, event_id):
    entry = '1'
    line_list = []
    chl_hi_list = []
    chl_low_list = []
    if soup.find('span', id = event_id+"_CHL_LINE_"+entry).text == '---': # suspend time
        return dict(line_list=line_list, 
                    chl_hi_list=chl_hi_list, 
                    chl_low_list=chl_low_list) 
    while (soup.find('span', id = event_id+"_CHL_LINE_"+entry)): # exit when return None
        # get text content from a specific span id
        line = soup.find('span', id = event_id+"_CHL_LINE_"+entry).text.strip('[]')
        chl_hi = soup.find('span', id = event_id+"_CHL_H_"+entry).text
        chl_low = soup.find('span', id = event_id+"_CHL_L_"+entry).text
        line_list.append(line)
        chl_hi_list.append(chl_hi)
        chl_low_list.append(chl_low)
        entry = str(int(entry)+1)
    return dict(line_list=line_list, 
                chl_hi_list=chl_hi_list, 
                chl_low_list=chl_low_list) # return a dict

def data_manipulation(odd_dict, game_starting_time):
    # add timestamp
    timestamp = datetime.now()
    timestamp = datetime.strptime(datetime.strftime(timestamp, '%Y-%m-%d %H:%M:%S'), 
                                  '%Y-%m-%d %H:%M:%S')

    odds = pd.DataFrame({'timestamp': timestamp,
                         'line': odd_dict['line_list'],
                         'corner_hi':odd_dict['chl_hi_list'],
                         'corner_low': odd_dict['chl_low_list']})
    
    odds['game_starting_time'] = game_starting_time
    odds['game_starting_time'] = odds['game_starting_time'].apply(
        lambda x: datetime.strptime(x, '%Y-%m-%d %H:%M:%S'))
    odds['minutes'] = odds.timestamp - odds.game_starting_time
    odds['minutes'] = odds['minutes'].apply(
        lambda x: datetime.strptime(str(x), '0 days %H:%M:%S').strftime('%H:%M:%S'))
    
    return odds

def store_data(odds, event_id, path_dir):
    path_file = path_dir+event_id+'.csv'
    
    # if file exists, write line; if file does not exist, create one and write line
    if os.path.exists(path_file) == True:
        odds.to_csv(path_file, index=False, mode='a', header=False)
    else:
        odds.to_csv(path_file, index=False, mode='w', header=True)

def main(load_sleep=15, crawl_interval=10):
    print('Start running crawl script...')
    
    game = game_data()
    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.get(game.url)
    
    time.sleep(load_sleep) # to let the HTML load
    
    # get event_id
    event_id = parse_scrape_event_id(driver, game.game_starting_time)
    
    while(True):
        soup = parse_web(driver, event_id, game.game_starting_time)
        if soup is not None:
            odds_dict = scrape_odds(soup, event_id)
            odds = data_manipulation(odds_dict, game.game_starting_time)
            store_data(odds, event_id, game.path_dir)
        
        print('Done crawling on {}. Wait {} seconds for another crawl...'.format(datetime.now(), crawl_interval))
        time.sleep(crawl_interval)
        print('Refresh, start crawling again...')

    print('Crawling done. Termination of script.')

if __name__ == '__main__':
    main()

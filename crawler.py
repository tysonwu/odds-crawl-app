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
import os.path
import os
import time
import sys
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

#---------input-url---
url = 'https://bet.hkjc.com/football/odds/odds_inplay_all.aspx?lang=EN&tmatchid=8f455de2-e486-4c17-945d-44c4bf942d01'
game_starting_time = '20200212 18:00' #YYYYmmdd HH:MM format
#--------------------

class game_info:
    def __init__(self, url, game_starting_time):
        self.url = url
        self.game_starting_time = game_starting_time
        # self.date = '20200211'
        # self.weekday = 'TUE'
        # self.number = '31'

def get_game_info(driver, url, game_starting_time):
    try:
        game_info = driver.find_element_by_id('litMDay')
    except:
        driver.quit()
        print('Error finding attribute of game info. Program will now exit.')
        sys.exit()
    finally:
        game_info_content = game_info.get_attribute('innerHTML')
    
    # getting a content such as 12/02 18:30    
    game_info_content = game_info_content.replace(' ','') # get eg. WED1, FRI30

    start_date, start_time = game_starting_time.split()[0], game_starting_time.split()[1]
    
    start_date = datetime.strptime(start_date, '%Y%m%d') # str to datetime
    start_time = datetime.strptime(start_time, '%H:%M').strftime('%H:%M') # str to datetime to str
    
    if start_time <= '12:00': # because of timezone diff, if before 12:00 then still count as yesterday's game
        start_date = start_date - timedelta(days=1)
    start_date = datetime.strftime(start_date, '%Y%m%d') # datetime to str

    return (start_date+game_info_content)

def get_odds(soup, event_id):
    entry = '1'
    line_list = []
    chl_hi_list = []
    chl_low_list = []
    if soup.find('span', id = event_id+"_CHL_LINE_"+entry).text == '---': # suspend time
        return [],[],[]
    while (soup.find('span', id = event_id+"_CHL_LINE_"+entry)): # exit when return None
        # get text content from a specific span id
        line = soup.find('span', id = event_id+"_CHL_LINE_"+entry).text.strip('[]')
        chl_hi = soup.find('span', id = event_id+"_CHL_H_"+entry).text
        chl_low = soup.find('span', id = event_id+"_CHL_L_"+entry).text
        line_list.append(line)
        chl_hi_list.append(chl_hi)
        chl_low_list.append(chl_low)
        entry = str(int(entry)+1)
    return line_list, chl_hi_list, chl_low_list

def crawl_data(driver, event_id, game_starting_time):
    div_id = 'dCHLTable'+event_id
    try:
        chlodds = driver.find_element_by_xpath("//div[@id='"+div_id+"'"+"and @class='betTypeAllOdds']")
        chlodds_content = chlodds.get_attribute('innerHTML')

    except:
        driver.quit()
        print('Error finding odd contents.')
        print('This is mostly caused by an end of game or incorrect game info.')
        print('Program will now exit.')
        sys.exit()

    soup = BeautifulSoup(chlodds_content, 'html.parser')

    line_list, chl_hi_list, chl_low_list = get_odds(soup, event_id)

    timestamp = datetime.now()
    timestamp = datetime.strftime(timestamp, '%Y-%m-%d %H:%M:%S')
    timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')

    odds = pd.DataFrame({'timestamp': timestamp,
                         'line':line_list,
                         'corner_hi':chl_hi_list,
                         'corner_low': chl_low_list})
    odds['game_starting_time'] = game_starting_time
    odds['game_starting_time'] = odds['game_starting_time'].apply(
        lambda x: datetime.strptime(x, '%Y%m%d %H:%M'))
    odds['minutes'] = odds.timestamp - odds.game_starting_time
    odds['minutes'] = odds['minutes'].apply(
        lambda x: datetime.strptime(str(x), '0 days %H:%M:%S').strftime('%H:%M:%S'))

    # if file exists, write line; if file does not exist, create one and write line
    # path_file = '/Users/TysonWu/dev/hkjc-crawl/development/data/'+event_id+'.csv'
    if not os.path.isdir('./data'):
        os.mkdir('./data')
    if os.path.isfile('./data/'+event_id+'.csv'):
        odds.to_csv('./data/'+event_id+'.csv', index=False, mode='a', header=False)
    else:
        odds.to_csv('./data/'+event_id+'.csv', index=False, mode='w', header=True)

    interval = 10
    print('Done crawling on {}. Wait {} seconds for another crawl...'.format(datetime.now(), interval))
    time.sleep(interval)
    print('Refresh, start crawling again...')

def main():
    print('Start running script...')
    game = game_info(url, game_starting_time)
    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.get(game.url)
    time.sleep(5)
    event_id = get_game_info(driver, game.url, game.game_starting_time)
    
    while(True):
        crawl_data(driver, event_id, game.game_starting_time)
    
    driver.quit()
    print('Crawling finished. Data are stored in csv.')

if __name__ == '__main__':
    main()

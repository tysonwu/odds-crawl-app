# -*- coding: utf-8 -*-

import pandas as pd
import os
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
import time
import warnings
warnings.filterwarnings("ignore")

def update_result():
    os.chdir('/Users/TysonWu/dev/odds-crawl-app/odds-crawl-app/development/')

    all_matches = pd.read_csv('data_collection/data/match_data.csv')
    current_result_data = pd.read_csv('result_collection/match_corner_result.csv')

    updated_result_data = all_matches.merge(
        current_result_data[['event_id','result_corner']], how='outer', on='event_id')

    updated_result_data.to_csv('result_collection/match_corner_result.csv', index=False)
    return updated_result_data

def get_search_list(data):
    df = data[data.result_corner.isna()]
    df['string'] = df['home']+' '+df['away']
    return df['string'].tolist()

if __name__ == "__main__":
    updated_result_data = update_result()
    search_list = get_search_list(updated_result_data)
    if search_list != []:
        driver = webdriver.Chrome(ChromeDriverManager().install())
        for string in search_list:
            driver.get('https://www.google.com.hk')
            search_box = driver.find_element_by_name('q')
            search_box.send_keys(string)
            search_box.submit()
            time.sleep(0.5)
            driver.execute_script('''window.open("https://www.google.com.hk","_blank");''')
            driver.switch_to.window(driver.window_handles[-1])
    else:
        print('No new corner results to be updated.')

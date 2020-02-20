# -*- coding: utf-8 -*-

import pandas as pd
import os

def update_result():
    os.chdir('/Users/TysonWu/dev/odds-crawl-app/odds-crawl-app/development/')

    all_matches = pd.read_csv('data_collection/data/match_data.csv')
    current_result_data = pd.read_csv('result_collection/match_corner_result.csv')

    updated_result_data = all_matches.merge(
        current_result_data[['event_id','result_corner']], how='outer', on='event_id')

    updated_result_data.to_csv('result_collection/match_corner_result.csv', index=False)

if __name__ == "__main__":
    update_result()
    

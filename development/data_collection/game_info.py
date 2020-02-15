# -*- coding: utf-8 -*-


url = 'https://bet.hkjc.com/football/odds/odds_inplay_all.aspx?lang=EN&tmatchid=2e60e9aa-b858-47d2-bba2-7dde1e17caef'

game_starting_time = '2020-02-15 08:10:00' #YYYY-mm-dd HH:MM:SS format
path_dir = '/Users/TysonWu/dev/odds-crawl-app/odds-crawl-app/development/data_collection/data/' #save dir

class game_data:
    def __init__(self):
        self.url = url
        self.game_starting_time = game_starting_time
        self.path_dir = path_dir

# -*- coding: utf-8 -*-


url = 'https://bet.hkjc.com/football/odds/odds_inplay_all.aspx?lang=EN&tmatchid=9fb21802-612e-4408-95d7-9f8fa031a9dd'
game_starting_time = '2020-02-13 18:00:00' #YYYYmmdd HH:MM format
path_dir = '/Users/TysonWu/dev/odds-crawl-app/odds-crawl-app/development/data_collection/data/'

class game_data:
    def __init__(self):
        self.url = url
        self.game_starting_time = game_starting_time
        self.path_dir = path_dir
# -*- coding: utf-8 -*-


url = 'https://bet.hkjc.com/football/odds/odds_inplay_all.aspx?lang=EN&tmatchid=506dc8bd-ea17-4934-a780-296c1663e26c'
game_starting_time = '2020-02-14 16:30:00' #YYYY-mm-dd HH:MM:SS format
path_dir = '/Users/TysonWu/dev/odds-crawl-app/odds-crawl-app/development/data_collection/data/' #save dir

class game_data:
    def __init__(self):
        self.url = url
        self.game_starting_time = game_starting_time
        self.path_dir = path_dir

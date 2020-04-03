import pandas as pd
import time
import re
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

class hkjc_info:
    def __init__(self):
        self.path_dir = '/Users/TysonWu/dev/odds-crawl-app/odds-crawl-app/development/data_collection/' #save dir
        self.url = 'https://bet.hkjc.com/football/odds/odds_inplay.aspx?lang=en'

def parse_web(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver.get(url)
    time.sleep(7) # let the potato rest for a while
    games_info = driver.find_element_by_id('ActiveMatchesOdds')
    soup = BeautifulSoup(games_info.get_attribute('innerHTML'), 'html.parser')
    driver.quit()
    return soup


def pipeline(soup, path_dir):
    event = [link.get("id")[2:] for link in soup.find_all("span", "nolnk span_vs")]
    league = [link.img.get("title") for link in soup.find_all("div","cflag")][1:]
    home = [link.text.strip() for link in soup.find_all("span", "teamname")][::2]
    away = [link.text.strip() for link in soup.find_all("span", "teamname")][1::2]
    time = [link.text.strip() for link in soup.find_all("div", "cesst")][1:]
    codes = [y.get("id")[3:] for y in [x.span for x in soup.find_all("div", "cesst")] if y is not None]
    game_url = ['https://bet.hkjc.com/football/odds/odds_inplay_all.aspx?lang=EN&tmatchid='+code for code in codes]

    games = pd.DataFrame({'event_id': event,
                          'league': league,
                          'home': home,
                          'away': away,
                          'time': time,
                          'game_url': game_url})

    # select only non-start games
    games = games[games['time'].str.contains("Expected In Play start selling time")]
    games['time'] = games['time'].apply(lambda x: re.sub('Expected In Play start selling time: ', '', x))

    current_year = str(datetime.now().year)
    games['time'] = games.time.apply(lambda x: datetime.strptime(
        current_year+'/'+x, '%Y/%d/%m %H:%M'))
    games['month'] = games['time'].apply(lambda x: str(x.month))
    games['day'] = games['time'].apply(lambda x: str(x.day))
    games['hour'] = games['time'].apply(lambda x: str(x.hour))
    games['minute'] = games['time'].apply(lambda x: str(x.minute))
    games['time'] = games.time.apply(lambda x: datetime.strftime(x, '%Y-%m-%d %H:%M:%S'))
    games['crontab_cmd'] = games['minute']+' '+games['hour']+' '+games['day']+' '+games['month']+' * cd '+path_dir+" && /opt/anaconda3/bin/python crawler.py --event_id "+games['event_id']+"\n"
    # games['sofascore_url'] = None
    return games, games['crontab_cmd']


def export_to_csv(games_data, path_dir):
    path_file = path_dir+"data/schedule.csv"
    if os.path.exists(path_file) == True:
        print('File exists. Update the file...')
        current_schedule = pd.read_csv(path_file)
        # separate urls
        sofascore_urls = current_schedule[['event_id', 'sofascore_url']]
        sofascore_urls = sofascore_urls[~sofascore_urls.sofascore_url.isna()]
        del current_schedule['sofascore_url']
        current_schedule = pd.concat([current_schedule,games_data])
        current_schedule = current_schedule.drop_duplicates(subset='event_id',keep='last')
        current_schedule = current_schedule.sort_values('time')
        current_schedule = current_schedule.merge(sofascore_urls, on='event_id', how='left')
        current_schedule.to_csv(path_dir+"data/schedule.csv", index=False, mode="w", header=True)
        return current_schedule
    else:
        games_data['sofascore_url'] = None
        games_data.to_csv(path_file, index=False, mode="w", header=True)
        return games_data


def export_to_txt(command, path_dir):
    with open(path_dir+'data/crontab_command.txt', 'w') as f:
        for item in command:
            f.write("%s\n" % item)


def remove_duplicated_entry(path_dir):
    path_file = path_dir+"data/schedule.csv"
    schedule = pd.read_csv(path_file)
    schedule = schedule.drop_duplicates(keep='last')
    schedule.to_csv(path_file, index=False, mode="w", header=True)
    print("Removed duplicated entry")


# def driver_search(data)


if __name__ == '__main__':
    hkjc = hkjc_info()
    web_content = parse_web(hkjc.url)
    games_data, command = pipeline(web_content, hkjc.path_dir)
    data = export_to_csv(games_data, hkjc.path_dir)
    export_to_txt(command, hkjc.path_dir)
    # remove_duplicated_entry(hkjc.path_dir)
    print('Schedule crawling done.')
    print('Results written to schedule.csv and crontab_command.txt')

    data = data[data.sofascore_url.isna()]
    df = data
    df['string'] = df['home']+' vs '+df['away']+' sofascore'
    search_list = df['string'].tolist()
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
        print('No sofascore URL needs to be updated.')

import pandas as pdimport timeimport reimport osfrom crontab import CronTabfrom bs4 import BeautifulSoupfrom selenium import webdriverfrom webdriver_manager.chrome import ChromeDriverManagerfrom datetime import datetimepath_dir = '/Users/TysonWu/dev/odds-crawl-app/odds-crawl-app/development/data_collection/data/' #save dirdef parse_web():    url = 'https://bet.hkjc.com/football/odds/odds_inplay.aspx?lang=en'        driver = webdriver.Chrome(ChromeDriverManager().install())    driver.get(url)    time.sleep(7) # let the potato rest for a while    games_info = driver.find_element_by_id('ActiveMatchesOdds')    soup = BeautifulSoup(games_info.get_attribute('innerHTML'), 'html.parser')    driver.quit()    return soupdef pipeline(soup):    event = [link.text.strip() for link in soup.find_all("div", "cday alloddsLink")]    home = [link.text.strip() for link in soup.find_all("span", "teamname")][::2]    away = [link.text.strip() for link in soup.find_all("span", "teamname")][1::2]    time = [re.sub('Expected In Play start selling time: ', '' ,link.text.strip())             for link in soup.find_all("div", "cesst")][1:]        games = pd.DataFrame({'event': event,                           'home': home,                           'away': away,                           'time': time})    games = games.iloc[1:,]    current_year = str(datetime.now().year)    games['time'] = games.time.apply(lambda x: datetime.strptime(        current_year+'/'+x, '%Y/%d/%m %H:%M'))    games['month'] = games['time'].apply(lambda x: x.month)    games['day'] = games['time'].apply(lambda x: x.day)    games['hour'] = games['time'].apply(lambda x: x.hour)    games['minute'] = games['time'].apply(lambda x: x.minute)    # games['crontab_time'] = ' '.join(games.minute, games.hour, games.day, games.month)    return gamesdef export_to_csv(games_data, path_dir):    path_file = path_dir+"schedule.csv"    if os.path.exists(path_file) == True:        games_data.to_csv(path_file, index=False, mode="a", header=False)    else:        games_data.to_csv(path_file, index=False, mode="w", header=True)def main():    web_content = parse_web()    games_data = pipeline(web_content)    export_to_csv(games_data, path_dir)if __name__ == '__main__':    main()
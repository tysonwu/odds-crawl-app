import pandas as pdimport timefrom datetime import datetime, timedeltafrom selenium import webdriverfrom webdriver_manager.chrome import ChromeDriverManagerdef initialize(url, load_sleep=10):    driver = webdriver.Chrome(ChromeDriverManager().install())    driver.get(url)    time.sleep(load_sleep)  # to let the HTML load    return driverdef main():    driver = initialize(url)    timer = driver.find_element_by_class_name('js-event-status-description js-event-widget-header-timer-container live ')    print(timer.text)if __name__ == '__main__':    url = 'https://www.sofascore.com/aston-villa-leicester-city/GP'    main()
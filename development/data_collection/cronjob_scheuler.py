from crontab import CronTabcommand = ["* * 17 2 * /opt/anaconda3/bin/python /Users/TysonWu/dev/odds-crawl-app/odds-crawl-app/development/data_collection/crawler.py"]def clear_write_cronjob(command): # a list on commands    cron = CronTab(tab="""* * 17 2 * /opt/anaconda3/bin/python /Users/TysonWu/dev/odds-crawl-app/odds-crawl-app/development/data_collection/crawler.py""")clear_write_cronjob(command)
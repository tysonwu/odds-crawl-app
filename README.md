# odds-crawl-app
## Introduction

 Crawling football odds with live data visualisation



## Data Collection

All data collection scripts are contained in the folder `development`.

### Data Crawling Procedures

1. Run `schedule_crawler.py`

- Specify the working directory under `self.path_dir`

- This script crawls the schedule of upcoming matches (excluding matches that has already started), and export several attributes (event_id, home, away, league, start time, url) to `data/schedule.csv`
- Also create `crontab_command.txt` which includes *crontab commands* that will be used to schedule runtime of `crawler.py` 



2. Copy the crontab commands to crontab in your computer to schedule job. Here is a brief note about crontab:

https://www.youtube.com/watch?v=QZJ1drMQz1A

##### Check Python version

- Can be done by typing `which python` in Terminal

1. Type `crontab -e` in terminal to enter vim edit cron jobs
2. Press `I` to go to insert mode in Vim
3. Specify the time for job, then insert Python path got from `which python`, then insert crawler.py path
4. Press `Esc` after finishing input
5. Type `:wq` to save and quit

##### Time Format

```
# ┌───────────── minute (0 - 59)
# │ ┌───────────── hour (0 - 23)
# │ │ ┌───────────── day of month (1 - 31)
# │ │ │ ┌───────────── month (1 - 12)
# │ │ │ │ ┌───────────── day of week (0 - 6) (Sunday to Saturday;
# │ │ │ │ │                                       7 is also Sunday on some systems)
# │ │ │ │ │
# │ │ │ │ │
# * * * * *  command_to_execute
```

##### Cron job utilities
`crontab -l` shows a list of cronjobs
`crontab -r` removes cronjobs



3. Your computer should evoke `crawler.py` according to the cronjobs.

- Specify the directory to store data. The directory should be under the `data/` folder of the main working directory that stores the script.
- For each time the script runs, a log will be written on `data/job_history.csv`
- Match data will be appended to `data/match_data.csv`
- The script will create the odds in `data/` with `event_id` as filename. **Do not open the csv file in Excel when the script is running** as Excel may automatically convert datetime strings to other formats (crazy Excel). 
- The script runs whenever the odds are still available. Script terminates when the match ends and no more odds are available for crawling.
- Crawler currently crawls live score and corner hilow odds every 10 seconds. 



> game_info.py is not under use now.



### Remarks

#### Future development

- Will store data in a mySQL database instead of local file `schedule.csv`, `match_data.csv`, `job_history.csv` and odds files. Storing data in local machine is crazy.



## Match Result Collection

> **Under construction**

- The corner results of all matches will be collected by finding third-party data sources online (Football APIs).



## Signal

> **Under construction**



## Deployment

### Off-line live graph![sceenshot](/Users/TysonWu/dev/odds-crawl-app/odds-crawl-app/sceenshot.png)

An off-line live graph of odds visualisation is made with *Dash* in Python.

See `app.py` and assets folder under `data_collection`.

#### How to use the live graph

- Run `app.py`. Make sure css file is present under the asset folder in the same directory.
- The script reads the event_id from the latest job under `job_history.csv`. 
- As long as `crawler.py` is running and updating the odds csv, the graph will update in live.



### Deployment with node.js

> **Under construction**
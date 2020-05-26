# coding: utf-8
import time
import os
import pandas as pd
import numpy as np
from datetime import datetime as dt
import botometer
import json

class RotatingFileOpener():
    def __init__(self, path, mode='a+', prepend="", append=""):
        if not os.path.isdir(path):
            raise FileNotFoundError("Can't open directory '{}' for data output.".format(path))
        self._path = path
        self._prepend = prepend
        self._append = append
        self._mode = mode
        self._day = time.localtime().tm_mday
    def __enter__(self):
        self._filename = self._format_filename()
        self._file = open(self._filename, self._mode)
        return self
    def __exit__(self, *args):
        return getattr(self._file, '__exit__')(*args)
    def _day_changed(self):
        return self._day != time.localtime().tm_mday
    def _format_filename(self):
        return os.path.join(self._path, "{}{}{}".format(self._prepend, time.strftime("%Y%m%d"), self._append))
    def write(self, *args):
        if self._day_changed():
            self._file.close()
            self._file = open(self._format_filename(), self._mode)
        return getattr(self._file, 'write')(*args)
    def __getattr__(self, attr):
        return getattr(self._file, attr)
    def __iter__(self):
        return iter(self._file)



class RetrieveBotscore():

    def loadJson(self, filename):
        init = dt.now()
        with open(filename) as tw_file:
            data=[]
            for line in tw_file:
                try:
                    tw = json.loads(line)
                    data.append(tw)
                except Exception as e:
                    print(filename,e)
            botscore_measurements = pd.io.json.json_normalize(
                data, 
                sep="_"
            )
            botscore_measurements.info()
            print(dt.now()-init)
            return botscore_measurements


    def __init__(self, tw_keys):
        self._bom = botometer.Botometer(
              wait_on_ratelimit=True,
              **tw_keys)

    def check_botometer_scores(self, users_to_check_botscore):
        error_ids=[]
        botometer_output=[]
        with RotatingFileOpener(
            '.', 
            prepend='botscores_errors-', 
            append='.json'
        ) as error_logger:
            with RotatingFileOpener(
                '.', 
                prepend='botscores-', 
                append='.json'
            ) as logger:
                for i, (screen_name, bot_score_json) in enumerate(self._bom.check_accounts_in(users_to_check_botscore)):
                    try:
                        botometer_output.append(bot_score_json)
                        logger.write('%s\n' % json.dumps(bot_score_json))
                        if i%100==0:
                            print(i,str(dt.now()),screen_name,)
                    except Exception as error:
                        error_ids.append(screen_name)
                        error_logger.write('%s\n' % {"screen_name":screen_name, "error":str(error)})
                        print("{} - Error getting botscore of {}. {}".format(str(dt.now()), screen_name, str(error)))


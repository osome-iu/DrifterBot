from bot import Bot
from config_stat import activation_time
from datetime import datetime
from datetime import timedelta
import debug
import numpy as np
import os
import time
import random
import subprocess
import sys

def RandomizeTime(g=0.1, mmin=0, mmax=420, noise=True):
  """Sampled from a distribution."""
  mins = None
  secs = 0
  r = np.random.random(1)[0]
  ag, bg = mmin**g, mmax**g
  mins = (ag + (bg - ag)*r)**(1./g)
  if noise:
    secs = int(60 * (mins - int(mins)))
  mins = int(mins)

  current_time = datetime.now()

  if activation_time[1] == 24:
    if current_time.hour < activation_time[0]:
      end_time = current_time
    else:
      end_time = current_time + timedelta(days=1)
    end_time = datetime(end_time.year, end_time.month, end_time.day, 0,0,0)
  else:
    if current_time.hour < activation_time[0]:
      end_time = current_time - timedelta(days=1)
    else:
      end_time = current_time
    end_time = datetime(end_time.year, end_time.month, end_time.day, activation_time[1],0,0)
  
  next_activated_time = current_time + timedelta(minutes=mins)
  if next_activated_time > end_time:
    # if the next activated time is passed the end_time
    # we wake the bot on the next.
    # the extra time is added into the next day schedule.
    sleep_hour = 24 - activation_time[1] + activation_time[0]
    mins = (timedelta(minutes=mins) + timedelta(hours=sleep_hour)).total_seconds()
    mins /= 60.0
  return int(mins), secs

def main(username, keep_alive=True):

  user = Bot(username)
  action, source, result_code = user.action()
  print('m1')
  print(action)
  print(source)
  print(result_code)
  user.db_manager.SaveCurrentAction(source, action, result_code)
  print('m2')

  if not keep_alive:
    return 0

  plural = 's'
  minutes, seconds = RandomizeTime()
  
  if minutes <= 1:
    plural = ''
  if minutes == 0:
    cmd = 'echo "sleep %s ; python drifter_main.py %s > /dev/null" | at -M now &' % (seconds, username)
  else:
    cmd = 'echo "sleep %s ; python drifter_main.py %s > /dev/null" | at -M now + %s minute%s &' %(seconds, username, minutes, plural)
  os.system(cmd)



if __name__ == "__main__":
  argvs = sys.argv
  main(argvs[1], keep_alive=False)
  """
  if len(argvs) > 2:
    if argvs[2] in ['True','true', '1', 't', 'y', 'yes', 'T']:
      main(argvs[1], keep_alive=True)
    else:
      main(argvs[1], keep_alive=False)
  elif len(argvs) > 1:
    main(argvs[1], keep_alive=True)
  else:
    debug.LogToDebug('The bot username is not defined.')
  """








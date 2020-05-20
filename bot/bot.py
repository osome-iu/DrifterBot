"""Bot class."""
import action
import config_stat
import debug
from drifter_db import DataManager
import numpy as np


class Bot(object):
  def __init__(self, username, bot_id=None):
    self.username = username
    self.db_manager = DataManager(username, bot_id=bot_id)
    self.db_manager.SaveBackground()

  def action(self):
    keys = list(config_stat.prob_event)
    prob_lst =  [config_stat.prob_event[k] for k in keys]
    selected_action = np.random.choice(keys, 1, p=prob_lst)[0]
    if selected_action == 'like':
      # event like
      current_action = action.Like(self.username)
    elif selected_action == 'retweet':
      # event retweet
      current_action = action.Retweet(self.username)
    elif selected_action == 'follow':
      # event follow
      current_action = action.Follow(self.username)
    elif selected_action == 'unfollow':
      current_action = action.Unfollow(self.username, config_stat.unfollow_method)
    elif selected_action == 'replymention':
      current_action = action.ReplyMention(self.username)
    elif selected_action == 'tweet':
      current_action = action.PostTweet(self.username, True)
    result = current_action.act()
    source = current_action.select_source
    return selected_action, source, result




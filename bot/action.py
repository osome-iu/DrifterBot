"""Bot Action class."""

import cal_helper
from config_stat import like_prob, follow_prob, unfollow_method, mention_tl_num
from config_stat import mamximum_follow_ignore_ratio_bound, follow_ratio, minimum_friends
from config_stat import num_tweets_in_each_topic, num_topics_in_trends
from config_stat import num_friends_to_lookat_inFoF, tweet_prob
from config_stat import num_latest_tweets_to_look_likes
# A chatbot to reply and post tweets. It's ok to disable the libraries.
# https://chatterbot.readthedocs.io/en/stable/
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer
import datetime
import debug
from drifter_db import DataManager
import numpy as np
import source
import subprocess
import os
import re


# bot -> list of twitter user ids
# For each bot, its initial friends won't be unfollowed.
initial_friends = {
  'bot_screen_name':[000000000], # faux case
}

def randomizeATweetIDFromTrends(usr_name):
  trend_topic_obj = source.Trends(usr_name)
  trend_topic_lst = trend_topic_obj.getSourceData()
  if not trend_topic_lst:
    return False
  candidate_topics = np.random.choice(trend_topic_lst, num_topics_in_trends)
  tweet_id = []
  search_obj = source.SearchTweet(usr_name)
  for topic in candidate_topics:
    current_tweet_id_lst = search_obj.getSourceData(topic, num_tweets_in_each_topic)
    if current_tweet_id_lst:
      tweet_id += current_tweet_id_lst

  if not tweet_id:
    return False
  return np.random.choice(tweet_id, 1)[0]


def randomizeATweetFromLikes(usr_name, return_key=None):
  """Randomize a tweet from friends' likes.

  The friends are fetched from the latest num_timeline_tweets tweets in the
  home timeline. Then we randomly return a tweet that is the latest
  M liked tweets liked num_latest_likes by each friends.

  Args:
    return_key: if return_key is none, it returns the tweet object.
  """
  source_obj = source.HomeTimeLine(usr_name)
  if not source_obj:
    return False
  source_data = source_obj.getSourceData()
  if not source_data:
    return False
  user_obj_lst = cal_helper.randomizeObjs(
    source_data, return_key='user',
    num_returns=num_latest_tweets_to_look_likes)
  user_ids = set()
  for user in user_obj_lst:
    if user['screen_name'] == usr_name:
      continue
    user_ids.add(user['id'])

  source_obj = source.LikedTweets(None)
  tweets = []
  for user_id in user_ids:
    source_obj.username = user_id
    tmp_tweets = source_obj.getSourceData()
    if tmp_tweets:
      tweets += tmp_tweets

  if not tweets:
    return False
  target_tweet = np.random.choice(tweets, 1)[0]
  if return_key:
    return target_tweet[return_key]
  else:
    return target_tweet


class Action(object):
  """A base class for actions."""

  def __init__(self, username):
    self.username = username
    self.select_source = None

  def composeCmd(self, id):
    return ''

  def apiAct(self, id, cmd=None):
    
    if not id and not cmd:
      debug.LogToDebug('id and cmd is not defined (apiAct)')
      return False
    
    try:
      if not cmd:
        cmd = self.composeCmd(id)
      rst = subprocess.check_output(cmd)
    except Exception as e:
      debug.LogToDebug('func apiAct\n %s'% str(e))
      return False
    else:
      try:
        rst = json.loads(rst.decode('utf8'))
      except:
        return True
      else:
        if 'errors' in rst or 'error' in rst:
          if 'errors' in rst:
            msg = rst['errors']
          else:
            msg = rst['error']
          debug.LogToDebug('func apiAct. Twitter API failure.\n %s'% str(msg))
          return False
      return True

  def act(self):
    pass


class Like(Action):

  def __init__(self, username):
    super().__init__(username)

  def composeCmd(self, tweet_id):
    cmd = [
      'twurl', '-X', 'POST',
      '/1.1/favorites/create.json?id=%s' % tweet_id,
      '-u', self.username
    ]
    return cmd

  def act(self):
    current_source = cal_helper.randomizeSource(like_prob)
    self.select_source = current_source
    if current_source == 'trend':
      tweet_id = randomizeATweetIDFromTrends(self.username)
      if not tweet_id:
        return False
    elif current_source == 'like':
      tweet_id = randomizeATweetFromLikes(self.username, return_key='id')
    else:  # timeline
      source_obj = source.HomeTimeLine(self.username)
      if not source_obj:
        return False
      source_data = source_obj.getSourceData()
      if not source_data:
        return False
      tweet_id = cal_helper.randomizeObjs(source_data, return_key='id')
    if_suc = self.apiAct(tweet_id)
    if not if_suc:
      return False
    return tweet_id


class Retweet(Like):

  def __init__(self, username):
    super().__init__(username)

  def composeCmd(self, tweet_id):
    cmd = [
      'twurl', '-X', 'POST',
      '/1.1/statuses/retweet/%s.json' % tweet_id,
      '-u', self.username]
    return cmd


class Unfollow(Action):
  def __init__(self, username, unfollow_method='weighted'):
    super().__init__(username)
    self.unfollow_method = unfollow_method

  def composeCmd(self, user_id):
    cmd = [
      'twurl', '-X', 'POST',
      '/1.1/friendships/destroy.json?user_id=%s' % user_id,
      '-u', self.username]
    return cmd

  def act(self, friend_id_lst=None):
    """Unfollow an user weighted randomized.

    The weight is weighted by its time order. The older one has a higher
    probability to be unfollowed.

    This function may need to be modified if its Twitter API changed.
    At this time, results from  '/1.1/followers/ids.json' are ordered with the
    most recent following first, but Twitter may change it without announcement.
    Check it if we still want to select the id based on its time data.
    https://developer.twitter.com/en/docs/accounts-and-users/follow-search-get-users/api-reference/get-followers-ids
    """

    if not friend_id_lst:
      friend_obj = source.Friends(self.username, whether_user_entity=False)
      friend_id_lst = friend_obj.getSourceData()
    if not friend_id_lst:
      return False
    if len(friend_id_lst) <= minimum_friends:
      current_action = Follow(self.username)
      if_suc = current_action.act()
      self.select_source = current_action.select_source
      if not if_suc:
        return if_suc
      else:
        return -if_suc
        
    # never unfollow the seeds
    try:
      friend_id_lst.remove(initial_friends[self.username][0])
    except:
      debug.LogToDebug('failed to remove seed for user %s' % self.username)
      if len(friend_id_lst) < 4999:
        return False
    selected_id = None
    if self.unfollow_method == 'weighted':
      selected_id = cal_helper.randomizeObjs(
        friend_id_lst,
        whether_weighted=True,
        weighted_order=True)
    elif self.unfollow_method == 'uniform':
      selected_id = cal_helper.randomizeObjs(friend_id_lst)
    if_suc = self.apiAct(selected_id)
    if not if_suc:
      return False
    return selected_id


class Follow(Action):

  def __init__(self, username):
    super().__init__(username)
    self.twitter_id = None

  def composeCmd(self, user_id):
    cmd = [
      'twurl', '-X', 'POST',
      '/1.1/friendships/create.json?user_id=%s&follow=true' % user_id,
      '-u', self.username]
    return cmd

  def WhetherFollow(self):
    """Check whether the bot has reached the following count limit."""
    source_obj = source.UserObj(self.username)
    current_bot = source_obj.getSourceData()
    if not current_bot:
      return False
    num_friends = current_bot['friends_count']
    num_followers = current_bot['followers_count']
    self.twitter_id = current_bot['id']
    if num_friends < mamximum_follow_ignore_ratio_bound:
      return True
    # if (num_friends / float(num_followers)) < follow_ratio:
    if num_friends - num_followers <= mamximum_follow_ignore_ratio_bound:
      return True
    return False

  def act(self):
    # check whether to follow or switch to unfollow
    whether_to_follow = self.WhetherFollow()
    if not whether_to_follow:
      current_action = Unfollow(self.username, unfollow_method)
      if_suc = current_action.act()
      if not if_suc:
        return if_suc
      else:
        return -if_suc

    current_source = cal_helper.randomizeSource(follow_prob)
    if_suc = False

    if not self.twitter_id:
      source_obj = source.UserObj(self.username)
      current_bot = source_obj.getSourceData()
      if not current_bot:
        return False
      self.twitter_id = current_bot['id']

    self.select_source = current_source
    if current_source == 'FoF':
      # 1. friend list
      source_obj = source.Friends(self.username)
      friend_id_lst = source_obj.getSourceData()
      if not friend_id_lst:
        return False
      # 2. Randomize N friends and get their friend lists(allow duplicate)
      sub_friends = cal_helper.randomizeObjs(
        friend_id_lst,
        num_friends_to_lookat_inFoF)
      sub_friends = list(set(sub_friends))
      candidate_friend_lst = []
      for ff in sub_friends:
        source_obj.user_id = ff
        f_lst = source_obj.getSourceData()
        if not f_lst:
          continue
        candidate_friend_lst += f_lst
      if not candidate_friend_lst:
        return False
    elif current_source == 'timeline': # == retweet based on Twitter API return
      source_obj = source.HomeTimeLine(self.username)
      if not source_obj:
        return False
      source_data = source_obj.getSourceData()
      if source_data:
        candidate_friend_lst = cal_helper.RetriveUserIds(source_data)
    elif current_source == 'follower': # follower
      source_obj = source.Followers(self.username)
      candidate_friend_lst = source_obj.getSourceData()
      if not candidate_friend_lst:
        return False
    else: #liked
      usr_obj = randomizeATweetFromLikes(self.username, return_key='user')
      if not usr_obj:
        return False
      selected_id = usr_obj['id']

    if current_source != 'liked':
      # Get the list of friend ids and my id.
      friend_obj = source.Friends(self.username, whether_user_entity=False)
      removing_id_lst = friend_obj.getSourceData()
      candidate_lst = []
      if removing_id_lst:
        removing_id_lst.append(self.twitter_id)
        for iid in candidate_friend_lst:
          if iid not in removing_id_lst:
            candidate_lst.append(iid)

      if not candidate_lst:
        return False
      selected_id = np.random.choice(candidate_lst, 1)[0]

    if_suc = self.apiAct(selected_id)
    if not if_suc:
      return if_suc
    return selected_id


class PostTweet(Action):

  def __init__(self, username, whether_quote):
    super().__init__(username)
    self.whether_quote = whether_quote

  def composeCmd(self, text_msg, reply_id=None):
    if not reply_id:
      cmd = [
        "twurl", "-d",
        "'status=%s'" % text_msg,
        "-u", self.username,
        "/1.1/statuses/update.json"]
    else:
      cmd = [
        "twurl", "-d",
        "'status=%s'" % text_msg,
        "-u", self.username,
        "/1.1/statuses/update.json?in_reply_to_status_id=%s" % (reply_id)]
    return cmd

  def _filter(self, tweets, contain_urls=True):
    """Remove tweets tweeted by the user itself and/or without urls (except link to other tweets)."""
    new_tweets = []
    for tweet in tweets:
      if contain_urls and not tweet['entities']['urls']:
        continue
      elif contain_urls and tweet['entities']['urls']:
        if len(tweet['entities']['urls']) == 0:
          continue
        url_obj = tweet['entities']['urls'][0]['expanded_url']
        if 'twitter.com' in url_obj and 'status' in url_obj:
          continue
      if tweet['user']['screen_name'] == self.username:
        continue
      new_tweets.append(tweet)
    return new_tweets

  def cleanhtml(self, raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

  def act(self):
    current_source = cal_helper.randomizeSource(tweet_prob)
    self.select_source = current_source
    text_msg = ''
    attachment_url = ''
    if current_source == 'timeline':
      source_obj = source.HomeTimeLine(self.username)
      if not source_obj:
        return False
      source_data = source_obj.getSourceData()
      if not source_data:
        return False

      source_data = self._filter(source_data, (not self.whether_quote))
      if not source_data:
        return False

      tweet = cal_helper.randomizeObjs(source_data)
      tweet_id = tweet['id']
      tweet_owner_name = tweet['user']['screen_name']
      text_msg = '%s ' % (cal_helper.RandomizeAnTweetFromFile()) # get a randomly reply
      attachment_url = 'https://twitter.com/%s/status/%s' % (tweet_owner_name, tweet_id)
    elif current_source == 'trend':
      tweet_id = randomizeATweetIDFromTrends(self.username)
      if not tweet_id:
        return False
      source_obj = source.TweetObj(self.username, tweet_id)
      tweet = source_obj.getSourceData()
      if tweet:
        try:
          text_msg = tweet['full_text']
        except:
          text_msg = tweet['text']
    else:  #random_quotes
      source_obj = source.RandomQuotes()
      text_msg = source_obj.getSourceData()
      text_msg = self.cleanhtml(text_msg)

    if not text_msg:
      return False

    final_txt_msg = '%s%s' %(text_msg, attachment_url)
    cmd = self.composeCmd(final_txt_msg)
    # TODO: fix subprocess problem?
    os_cmd = ""
    for c in cmd:
      os_cmd += "%s " % c
    try:
      os.system(os_cmd)
    except:
      return False
    return True



class ReplyMention(PostTweet):

  def __init__(self, username):
    super().__init__(username, True)
    self.select_source='NA'

  def CheckTime(self, tweet, valid_time):
    t_time = datetime.strptime(tweet['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
    if t >= valid_time:
      return True
    else:
      return False

  def GenerateReply(self, text):
    if not text:
      text = 'hello'
    chatbot = None
    trainer = None
    response = None
    try:
      chatbot = ChatBot('drifter')
      trainer = ChatterBotCorpusTrainer(chatbot)
      trainer.train("chatterbot.corpus.english")
      response = str(chatbot.get_response(text))
    except:
      pass
    finally:
      if trainer:
        del trainer
      if chatbot:
        del chatbot

    return response

  def act(self):
    # 1. take the latest mention action from the database,
    # and its quoted tweet id (in urls ->[{expanded_url:<url>}]) and its ts
    # the expanded_url is something like
    db = DataManager(self.username)
    since_id = db.TheLastMentionResult()
    del db
    # 2. select all tweets published after last replied tweet and randomize one to reply.
    source_obj = source.MentionTimeLine(self.username, since_id=since_id, count=mention_tl_num)
    if not source_obj:
      return False
    source_data = source_obj.getSourceData() # a list of tweets
    if not source_data:
      return False

    tweet = cal_helper.randomizeObjs(source_data)
    tweet_id = tweet['id']
    if 'full_text' in tweet:
      tweet_text = tweet['full_text']
    else:
      tweet_text = tweet['text']
    response = self.GenerateReply(tweet_text)
    if not response:
      debug.LogToDebug('chattbot not working.')
      response = cal_helper.RandomizeAnTweetFromFile()
    response = '@%s %s' % (tweet['user']['screen_name'], response)
    cmd = self.composeCmd(response, reply_id=tweet_id)
    # TODO: fix subprocess problem?
    os_cmd = ""
    for c in cmd:
      os_cmd += "%s " % c
    try:
      os.system(os_cmd)
    except:
      return False
    return True

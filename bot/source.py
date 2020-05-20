"""The information source such as home timeline and following list.

The twitter GET commands.
"""

import debug
import drifter_db
from config_stat import num_timeline_tweets, trend_loc_code, num_liked_tweets
import json
import subprocess
import requests
import html


class RandomQuotes(object):

  def getSourceData(self):
    try:
      result = requests.get(
        "https://api.quotable.io/random", auth=('user', 'pass'))
    except Exception as e:
      print(e)
      return False
    if result.status_code != 200:
      return False
    content = json.loads(result.content.decode('utf8'))
    sentence = content['content']
    sentence = sentence.replace('<p>', '').replace('</p>', '')
    return sentence

class Source(object):
  """The base Class for all Twitter sources."""
  def __init__(self, username):
    self.username = username

  def composeCmd(self):
    return None

  def getRawResult(self, cmd=None):
    if not cmd:
      cmd = self.composeCmd()
    try:
      rst = subprocess.check_output(cmd)
    except Exception as e:
      debug.LogToDebug('func getRawResult\n %s'% str(e))
      rst = False
    if rst and cmd:
      rst = json.loads(rst.decode('utf8'))
      if 'errors' in rst or 'error' in rst:
        if 'errors' in rst:
          msg = rst['errors']
        else:
          msg = rst['error']
        debug.LogToDebug('func getRawResult. Twitter API failure.\n %s'% str(msg))
        return False
    return rst

  def getSourceData(self):
    raw_rst = self.getRawResult()
    return raw_rst


class UserObj(Source):
  def __init__(self, username, user_id=None):
    super().__init__(username)
    self.user_id = user_id

  def composeCmd(self):
    if self.user_id:
      cmd = [
        'twurl',
        '/1.1/users/show.json?user_id=%s&include_entities=True' % self.user_id]
    else:
      cmd = [
        'twurl',
        '/1.1/users/show.json?screen_name=%s&include_entities=True' % self.username]
    return cmd


class TweetObj(Source):
  def __init__(self, username, tweet_id):
    super().__init__(username)
    self.tweet_id = tweet_id

  def composeCmd(self):
    cmd = [
      'twurl',
      '/1.1/statuses/show.json?id=%s&include_entities=True&tweet_mode=extended' % self.tweet_id
      ]
    return cmd

class HomeTimeLine(Source):

  def __init__(self, username, num_tweets=None):
    super().__init__(username)
    self.num_tweets = num_tweets

  def composeCmd(self):
    if not self.num_tweets:
      cmd = [
        'twurl',
        '/1.1/statuses/home_timeline.json?count=%s&include_entities=true&tweet_mode=extended' % num_timeline_tweets,
        '-u', self.username]
    else:
      cmd = [
        'twurl',
        '/1.1/statuses/home_timeline.json?count=%s&include_entities=true&tweet_mode=extended' % self.num_tweets,
        '-u', self.username]
    return cmd

  def getSourceData(self, only_english=True):
    raw_rst = None
    raw_rst = self.getRawResult()
    if not raw_rst:
      return False
    final_result = []
    for tweet in raw_rst:
      if tweet['lang'] and tweet['lang'] != 'en':
        continue
      final_result.append(tweet)
    return final_result

class UserTimeLine(Source):

  def __init__(self, username, count=10):
    super().__init__(username)
    self.count = count

  def composeCmd(self):
    # enable include_rts in the future when necessary
    cmd = [
      'twurl',
      '/1.1/statuses/user_timeline.json?screen_name=%s&count=%s&include_rts=false&tweet_mode=extended' % (self.username, self.count),
      '-u', self.username]
    return cmd

class MentionTimeLine(Source):

  def __init__(self, username, count=10, since_id=None):
    super().__init__(username)
    self.count = count
    self.since_id = since_id

  def composeCmd(self):
    # enable include_rts in the future when necessary
    if self.since_id:
      cmd = [
        'twurl',
        '/1.1/statuses/mentions_timeline.json?count=%s&since_id=%s&tweet_mode=extended' % (self.count, self.since_id),
        '-u', self.username]
    else:
      cmd = [
        'twurl',
        '/1.1/statuses/mentions_timeline.json?count=%s&tweet_mode=extended' % (self.count),
        '-u', self.username]      
    return cmd


class Trends(Source):

  def __init__(self, username):
    super().__init__(username)

  def composeCmd(self):
    cmd = [
    'twurl',
    '/1.1/trends/place.json?id=%s' % trend_loc_code
    ]
    return cmd

  def getSourceData(self, query_only=True):
    raw_rst = self.getRawResult()
    if not raw_rst:
      return False
    raw_rst = raw_rst[0]['trends']
    cleaned_data = []
    for r in raw_rst:
      # remove promoted content
      # though twitter api doesn't return promoted content at this moment.
      if not r['promoted_content']:
        if query_only:
          cleaned_data.append(r['query'])
        else:
          cleaned_data.append(r)
    return cleaned_data

class SearchTweet(Source):

  def __init__(self, username):
    super().__init__(username)
    self.keyword = None
    self.count = None

  def composeCmd(self):
    # it uses the default ranking method (mix) by Twitter
    cmd = [
    'twurl',
    '/1.1/search/tweets.json?q=%s&count=%s&lang=en&tweet_mode=extended' % (self.keyword, self.count)
    ]
    return cmd

  def getSourceData(self, keyword, count, tweetid_only=True):
    self.keyword = keyword
    self.count = count
    raw_rst = self.getRawResult()
    if not raw_rst:
      return False
    tweets = raw_rst['statuses']
    if not tweetid_only:
      return tweets

    t_id_lst = []  
    for tweet in tweets:
      t_id_lst.append(tweet['id'])
    return t_id_lst


class Friends(Source):
  def __init__(self, username, user_id=None, whether_user_entity=False):
    super().__init__(username)
    self.whether_user_entity = whether_user_entity
    self.user_id = user_id

  def composeCmd(self):
    # from most recent following to the oldest ones.
    if not self.whether_user_entity:
      if self.user_id:
        cmd = [
          'twurl',
          '/1.1/friends/ids.json?user_id=%s&count=5000' % self.user_id]
      else:
        cmd = [
          'twurl',
          '/1.1/friends/ids.json?screen_name=%s&count=5000' % self.username]
    else:
      if self.user_id:
        cmd = [
          'twurl',
          '/1.1/friends/list.json?user_id=%s&count=200' % self.user_id]
      else:
        cmd = [
          'twurl',
          '/1.1/friends/list.json?screen_name=%s&count=200' % self.username
        ]
    return cmd

  def getSourceData(self):
    raw_rst = self.getRawResult()
    if not raw_rst:
      return False
    if not self.whether_user_entity:
      return raw_rst['ids']
    else:
      return raw_rst['users']


class Followers(Friends):

  def __init__(self, username, whether_user_entity=False):
    super().__init__(username, whether_user_entity=whether_user_entity)

  def composeCmd(self):
    if not self.whether_user_entity:
      cmd = [
        'twurl',
        '/1.1/followers/ids.json?screen_name=%s&count=5000' % self.username]
    else:
      cmd = [
        'twurl',
        '/1.1/followers/list.json?screen_name=%s&count=200' % self.username
      ]
    
    return cmd

class LikedTweets(Source):

  def __init__(self, user_id, user_name=None, num_tweets=None):
    super().__init__(user_id)
    self.real_user_name = user_name
    if num_tweets:
      self.num_liked_tweet = num_tweets
    else:
      self.num_liked_tweet = num_liked_tweets


  def composeCmd(self):
    if not self.real_user_name:
      cmd = [
        'twurl',
        '/1.1/favorites/list.json?count=%s&user_id=%s&include_entities=True&tweet_mode=extended' % (self.num_liked_tweet, self.username)
      ]
    else:
      cmd = [
        'twurl',
        '/1.1/favorites/list.json?count=%s&screen_name=%s&include_entities=True&tweet_mode=extended' % (self.num_liked_tweet, self.real_user_name)
      ]
    
    return cmd

  def getSourceData(self, return_key=None):
    raw_rst = self.getRawResult()
    if not raw_rst:
      return False

    tmp_rst = []
    for rst in raw_rst:
      if rst['lang'] and rst['lang'] != 'en':
        continue
      tmp_rst.append(rst)
    if not return_key:
      return tmp_rst

    final_rst = []
    for rst in tmp_rst:
      final_rst.append(rst[return_key])
    return final_rst



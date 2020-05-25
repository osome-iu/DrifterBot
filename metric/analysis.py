from config_stat import twitter_app_auth  # config file

from metric.const_config import NUM_FRIENDS_TO_SAVE, NUM_FOLLOWERS_TO_SAVE 
from metric.db_for_analysis import SaveTweetstoDB, GetAllConns,UpdateConn
from metric.db_for_analysis import GetTweetsWithoutLowCredScore, UpdateLowCredScore
from metric.db_for_analysis import GetTweetsWithoutHashtagScore, GetTweetsWithoutURLScore
from metric.metrics import URLBased, HashtagBased, process_low_cred_urls
import numpy as np
import tweepy
import random
import networkx as nx
import pandas as pd
import time
import tldextract
from tweepy.error import TweepError

class Analyzer(object):

  def __init__(self, init_tweepy=False):
    self.tweepy_api = None
    self.auth = None
    self.low_credibility_df = pd.read_csv("../data/fake_source_list.csv").drop_duplicates()
    self.low_credibility_df.site = low_credibility_df.site.str.lower()
    self.known_shorterners = pd.read_csv("../data/known_shorterners.csv",index_col=0).domain.to_dict()
    if init_tweepy:
      self._initTweepy()

  def _initTweepy(self):
    self.auth = tweepy.OAuthHandler(
      twitter_app_auth['consumer_key'],
      twitter_app_auth['consumer_secret'])
    self.auth.set_access_token(
      twitter_app_auth['access_token'],
      twitter_app_auth['access_token_secret'])
    self.tweepy_api = tweepy.API(self.auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

  def calc_url_low_cred_score(self, url):
    """Method to compute the low credibility score of a link. Returns 1 if the link if classified as low credidibility for
    any source in the low_credibility_df, and 0 otherwise. The method also uses an additional source of known shorterners 
    to translate domains before looking up for low credibility reference.
    """
    pre,dom,suf = tldextract.extract(url.lower())
    domain = "{}{}.{}".format(
        "" if (pre=="") or (pre=="www") else pre+".",
        dom,
        suf
    )
    return sum(self.low_credibility_df.site==self.known_shorterners.get(domain,domain))

  def ComputeLowCredTweetScore(self, num_limit=3000):
    """Compute low credibility scores for tweets with resolved URLs that haven't had been computed in our db."""
    if_stop=False
    first_tweet_id = None
    last_tweet_id = None
    last_time = '2019-06-01'
    while True:
      if if_stop:
        break
      # batch process
      tweet_url_list, timestamp = GetTweetsWithoutLowCredScore(num_limit=num_limit, timestamp=last_time)
      print('len of tweets %s' % len(tweet_url_list))
      print(timestamp)
      if tweet_url_list and len(tweet_url_list) > 0:
        tw_examples = pd.DataFrame(tweet_url_list, columns=['tweet_id', 'resolved_urls'])
        tw_examples.resolved_urls = tw_examples.resolved_urls.str.lower()

        tw_examples["low_cred_score"] = tw_examples.resolved_urls.apply(self.calc_url_low_cred_score)
        tw_examples = tw_examples.groupby("tweet_id").agg({
            "low_cred_score": "max"
        })
                
        tw_examples.apply(UpdateLowCredScore, axis=1)
      else:
        break
      if len(tweet_url_list) < num_limit:
        if_stop = True
      tmp_tweet_id_1 = tweet_url_list[0][0]
      tmp_tweet_id_2 = tweet_url_list[-1][0]
      if first_tweet_id:
        if first_tweet_id == tmp_tweet_id_1 and last_tweet_id == tmp_tweet_id_2:
          if timestamp != last_time:
            last_time = timestamp
          else:
            break
        else:
          first_tweet_id = tmp_tweet_id_1
          last_tweet_id = tmp_tweet_id_2
      else:
        fist_tweet_id = tmp_tweet_id_1
        last_tweet_id = tmp_tweet_id_2
      print(tmp_tweet_id_1[0][0])

  def ComputeHashTagTweetScore(self, num_limit=3000):
    """Compute hashtag scores for tweets that haven't had hashtag scores in our db."""
    if_stop_signal = 0
    first_tweet_id = None
    last_tweet_id = None
    last_time = '2019-06-01'
    while True:
      if if_stop_signal == 1:
        break
      tweets, timestamp = GetTweetsWithoutHashtagScore(num_limit=num_limit, timestamp=last_time)
      if tweets and len(tweets) > 0:
        HashtagBased(tweets)
      else:
        break
      if len(tweets) < num_limit:
        if_stop_signal = 1
      tmp_tweet_id_1 = tweets[0]['id']
      tmp_tweet_id_2 = tweets[-1]['id']
      if first_tweet_id:
        if first_tweet_id == tmp_tweet_id_1 and last_tweet_id == tmp_tweet_id_2:
          if timestamp != last_time:
            last_time = timestamp
          else:
            break
        else:
          first_tweet_id = tmp_tweet_id_1
          last_tweet_id = tmp_tweet_id_2
      else:
        fist_tweet_id = tmp_tweet_id_1
        last_tweet_id = tmp_tweet_id_2
      print(tweets[0]['id'])

  def ComputeURLTweetScore(self,num_limit=3000):
    """Compute url scores for tweets that haven't had url scores in our db."""
    if_stop=False
    first_tweet_id = None
    last_tweet_id = None
    last_time = '2019-06-01'
    while True:
      if if_stop:
        break
      # batch process
      tweet_url_list, timestamp = GetTweetsWithoutURLScore(num_limit=num_limit, timestamp=last_time)
      print('len of tweets %s' % len(tweet_url_list))
      print(timestamp)
      if tweet_url_list and len(tweet_url_list) > 0:
        URLBased(tweet_url_list)
      else:
        break
      if len(tweet_url_list) < num_limit:
        if_stop = True
      tmp_tweet_id_1 = tweet_url_list[0][0]
      tmp_tweet_id_2 = tweet_url_list[-1][0]
      if first_tweet_id:
        if first_tweet_id == tmp_tweet_id_1 and last_tweet_id == tmp_tweet_id_2:
          if timestamp != last_time:
            last_time = timestamp
          else:
            break
        else:
          first_tweet_id = tmp_tweet_id_1
          last_tweet_id = tmp_tweet_id_2
      else:
        fist_tweet_id = tmp_tweet_id_1
        last_tweet_id = tmp_tweet_id_2
      print(tmp_tweet_id_1[0][0])


  def FetchConnTweets(self, usernames):
    """Randomize Friends/Followers and stores their Tweets."""
    if not self.tweepy_api:
      self._initTweepy()

    for usr in usernames:
      print('current usr:%s' % usr)
      user_id = None
      user_obj = self.tweepy_api.get_user(usr)
      if not user_obj:
        continue
      user_id = user_obj.id_str
      # saves friends
      friends_ids = GetAllConns(False, ego_usr_twitter_id=user_id, hourdelta=24) # Get today's friends
      if friends_ids:
        if NUM_FRIENDS_TO_SAVE > len(friends_ids):
          target_friends_ids = friends_ids
        else:
          target_friends_ids = random.sample(friends_ids, NUM_FRIENDS_TO_SAVE)
        for f_idx in range(len(target_friends_ids)):
          f_id = target_friends_ids[f_idx]
          try:
            tweets = self.tweepy_api.user_timeline(
                id=f_id, count=200, tweet_mode='extended')
          except TweepError as e:
            print('%s is blocked. Continue...')
            f_id = random.choice(list(set(friends_ids) - set(target_friends_ids)))
            target_friends_ids[f_idx] = f_id
            f_idx -= 1
            continue
          SaveTweetstoDB(tweets)
        UpdateConn(target_friends_ids, user_id, hourdelta=24)

      # saves followers
      followers_ids = GetAllConns(True, ego_usr_twitter_id=user_id, hourdelta=24) # Get today's friends
      if followers_ids:
        if NUM_FOLLOWERS_TO_SAVE > len(followers_ids):
          target_followers_ids = followers_ids
        else:
          target_followers_ids = random.sample(followers_ids, NUM_FOLLOWERS_TO_SAVE)
        for f_idx in range(len(target_followers_ids)):
          f_id = target_followers_ids[f_idx]
          try:
            tweets = self.tweepy_api.user_timeline(
                id=f_id, count=200, tweet_mode='extended')
          except TweepError as e:
            print('%s is blocked. Continue...' % f_id)
            f_id = random.choice(list(set(followers_ids) - set(target_followers_ids)))
            target_friends_ids[f_idx] = f_id
            f_idx -= 1
            continue
          SaveTweetstoDB(tweets)
        UpdateConn(target_followers_ids, user_id, hourdelta=24)
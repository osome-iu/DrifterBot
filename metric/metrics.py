from metric.const_config import MIN_VALID_MEDIA_SOURCES
from metric import db_for_analysis

import numpy as np
import pandas as pd
import requests
import tldextract

def _LoadMediaSource(file='../data/top500_domain_score_revised.csv'):
  source_df = pd.read_csv(file, usecols=['domain','avg_align'])
  return source_df


def _LoadHashtagScore(file='../data/all_hashtag_political_alignment.csv'):
  source_df = pd.read_csv(file, usecols=['hashtag', 'alignment'])
  return source_df


def UrlScoreForATweet(source_df, domains, urls):
  url_to_domain_lst_map = {}

  ex_urls = set()
  for url in urls:
    ex_url = url.lower()
    if ex_url in ex_urls:
      continue
    dd = [domain for domain in domains if domain in ex_url]
    if dd:
      ex_urls.add(ex_url)
      url_to_domain_lst_map[ex_url] = dd

  tmp_scores = []
  for url in ex_urls:
    if url not in url_to_domain_lst_map:
      continue
    matched_domains = url_to_domain_lst_map[url]
    matched_domain = max(matched_domains, key=len)
    valid_rows = source_df.loc[source_df['domain'] == matched_domain]
    score = valid_rows['avg_align'].mean()
    tmp_scores.append(float(score))
  if tmp_scores:
    return np.mean(tmp_scores)
  return None

def OpUrlScoreForATweet(source_df, domains, tweet_id_url):
  tweet_id = tweet_id_url[0]
  cached_scores = db_for_analysis.GetTweetScores(tweet_id)
  if cached_scores:
    if cached_scores[0][1]:
      return cached_scores[0][1]
  rst = UrlScoreForATweet(source_df, domains, urls=tweet_id_url[1])
  if rst:
    if cached_scores:
      db_for_analysis.SaveTweetURLScore(tweet_id, rst, True)
    else:
      db_for_analysis.SaveTweetURLScore(tweet_id, rst, False)
  return rst


def URLBased(tweet_url_list):
  """Compute URL based tweet score for a list of tweets.

  Args:
    tweet_lst: a list of tweet objs in tweepy format
  """
  source_df = _LoadMediaSource()

  domains = list(source_df['domain'])

  scores = []
  for tweet_id_url in tweet_url_list:
    tmp_score = OpUrlScoreForATweet(source_df, domains, tweet_id_url)
    if tmp_score is not None:
      scores.append(tmp_score)
  if len(scores) < MIN_VALID_MEDIA_SOURCES:
    return None

  return np.mean(scores), np.std(scores)


def HashtagScoreForATweet(source_df, hashtags_in_df, tweet=None, hashtags=None):
  if hashtags is None:
    try:
      hashtags = tweet.entities['hashtags']
    except:
      hashtags = tweet['entities']['hashtags']
  if not hashtags:
    return None

  ex_hashtag_scores = []
  for hashtag in hashtags:
    ex_hashtag = hashtag['text'].lower()
    if ex_hashtag in hashtags_in_df:
      ex_hashtag_scores.append(float(source_df[source_df.hashtag == ex_hashtag]['alignment']))
  if ex_hashtag_scores:
    return np.mean(ex_hashtag_scores)
  return None


def OpHashtagScoreForATweet(source_df, hashtags_in_df, tweet):
  try:
    tweet_id = tweet.id
  except Exception as e:
    #print(tweet)
    tweet_id = tweet['id']
  cached_scores = db_for_analysis.GetTweetScores(tweet_id)
  if cached_scores:
    if cached_scores[0][0]:
      return cached_scores[0][0]
  rst = HashtagScoreForATweet(source_df, hashtags_in_df, tweet=tweet)
  if rst:
    if cached_scores:
      db_for_analysis.SaveTweetHashtagScore(tweet_id, rst, True)
    else:
      db_for_analysis.SaveTweetHashtagScore(tweet_id, rst, False)
  return rst


def HashtagBased(tweet_lst):
  """Compute hashtag based tweet score for a list of tweets.

  Args:
    tweet_lst: a list of tweet objs in tweepy format

  """

  source_df = _LoadHashtagScore()

  hashtags_in_df = list(source_df['hashtag'])
  scores = []
  for tweet in tweet_lst:
    hashtag_score = OpHashtagScoreForATweet(
        source_df, hashtags_in_df, tweet)
    if hashtag_score is not None:
      scores.append(hashtag_score)
  if len(scores) < MIN_VALID_MEDIA_SOURCES:
    return None

  return np.mean(scores), np.std(scores)


def process_low_cred_urls(resolved_urls, low_credibility_df):
  domains = [
      "{}{}.{}".format(
          "" if (pre=="") or (pre=="www") else pre+".",
          dom,
          suf
      ) for pre,dom,suf in [tldextract.extract(url) for url in resolved_urls if url]
  ]
  low_cred_matches = low_credibility_df[low_credibility_df.site.isin(domains)]
  num_matches = len(low_cred_matches)
  consensus_score = 0
  if num_matches:
    consensus_score = low_cred_matches.consensus_count.sum()
  return pd.Series({
      "low_cred_urls": np.nan if len(domains)==0 else num_matches,
  })

"""lib to parse a list of tweets(json) into table TWEET_FOR_REBUTTAL2_2019.

Its input is a file, in which each line is a tweet in the format of json.

It also generates the url-based and hashtag-based valence score for
each tweet.
"""
import json
from pprint import pprint
import psycopg2
from psycopg2.extensions import AsIs
import pandas as pd
import numpy as np

# The data is in data folder
def _LoadMediaSource(file='../../data/url_bias_score.csv'):
  source_df = pd.read_csv(file,
                          usecols=['domain','score'])
  source_df.rename(columns={"score": "avg_align"}, inplace=True)
  return source_df


def _LoadHashtagScore(file='../../data/all_hashtag_political_alignment.csv'):
  source_df = pd.read_csv(file, usecols=['hashtag', 'alignment'])
  return source_df

def DBExecute(
  conn, command, method,
  param_lst=None, need_commit=False,
  return_id=False):
  """operate psql."""
  result = True
  try:
    if not conn:
      return False
    cur = conn.cursor()
    if param_lst:
      cur.execute(command, param_lst)
    else:
      cur.execute(command)
    if not need_commit:
      if return_id:
        result = cur.fetchone()[0]
      else:
        result = cur.fetchall()
    else:
      if return_id:
        result = cur.fetchone()[0]
      conn.commit()
  except (Exception, psycopg2.DatabaseError) as error:
    result = False
    conn.rollback()
    print(method)
    print(error)
  finally:
    if cur:
      cur.close()
  return result

def HashtagScoreForATweet(source_df, hashtags_in_df, tweet=None, hashtags=None):
  if hashtags is None:
    try:
      hashtags = tweet.entities['hashtags']
    except:
      hashtags = tweet['entities']['hashtags']
  if not hashtags:
    return None

  ex_hashtag_scores = []
  for ex_hashtag in hashtags:
    if ex_hashtag in hashtags_in_df:
      ex_hashtag_scores.append(float(source_df[source_df.hashtag == ex_hashtag]['alignment']))
  if ex_hashtag_scores:
    return np.mean(ex_hashtag_scores)
  return None

def UrlScoreForATweet(source_df, domains, urls):
  url_to_domain_lst_map = {}

  ex_urls = set()
  for ex_url in urls:
    if ex_url in ex_urls:
      continue
    if 'twitter.com' in ex_url:
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

def resolved_url(url):
  try:
    final_url = requests.head(url, allow_redirects=True, timeout=30)
    if final_url:
      return final_url.url
  except Exception as e:
      return None

def expanded_urls(url_lst):
  final_urls = []
  for url in url_lst:
    expanded_url = resolved_url(url)
    if expanded_url:
      final_urls.append(expanded_url)
    else:
      final_urls.append(url)
  return final_urls

def tweet_handler(t):
  hashtags = []
  urls = []
  url_objs = []
  hashtag_objs = []
  if u'entities' in t:
    url_objs += t[u'entities'][u'urls']
    hashtag_objs += t[u'entities'][u'hashtags']
  if u'retweet_status' in t:
    url_obj += t[u'retweet_status'][u'entities'][u'urls']
    hashtag_objs += t[u'retweet_status'][u'entities'][u'hashtags']
  for url_obj in url_objs:
    urls.append(url_obj[u'expanded_url'].lower())
  for hashtag_obj in hashtag_objs:
    hashtags.append(hashtag_obj[u'text'].lower())
  exp_urls = expanded_urls(urls)
  return (hashtags,
          exp_urls,
          t[u'user'][u'id_str'],
          t[u'id_str'],
          t[u'created_at'])


# Main function. Starting from here
def file_handler(filename):
  tweets = []
  with open(filename, 'rb') as f:
    content = f.readlines()
  content = [x.strip() for x in content]
  for c in content:
    try:
      tweets.append(json.loads(c))
    except Exception as e:
      print(c)
      print(e)
  
  url_df = _LoadMediaSource()
  hashtag_df = _LoadHashtagScore()
  urls_in_df = list(url_df['domain'])
  hashtags_in_df = list(hashtag_df['hashtag'])
  idx = 0
  sql_comm = """
  insert into TWEET_FOR_REBUTTAL2_2019(
  tweet_id, user_id,
  tweet_obj, created_at, hashtag_score,
  resolved_urls, url_score) values (%s, %s, %s, %s, %s, %s, %s)
  ON CONFLICT ON CONSTRAINT tweet_for_rebuttal2_2019_pkey 
  DO NOTHING;
  """
  db_conn = psycopg2.connect('dbname=drifter')
  for t in tweets:
    if idx % 100 == 0:
      print('processing tweet %s' % idx)
    idx += 1
    hashtags, urls, user_id, tweet_id, tweet_created_at = tweet_handler(t)
    # get hashtag score
    h_score = HashtagScoreForATweet(hashtag_df, hashtags_in_df, hashtags=hashtags)
    # get url score
    url_score = UrlScoreForATweet(url_df, urls_in_df, urls)
    # insert into db
    rst = DBExecute(
        db_conn, sql_comm, "update tweet for tweet %s" % tweet_id,
        param_lst=(tweet_id, user_id,
                   json.dumps(t), tweet_created_at,
                   h_score, urls, url_score),
        need_commit=True, return_id=False)


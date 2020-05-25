from datetime import datetime
from datetime import timedelta
import debug
import time

import json
import psycopg2
from psycopg2.extensions import AsIs

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


def GetTweetsWithoutHashtagScore(num_limit=100, timestamp='2019-01-01'):
  comm = """
    select tweet_id, tweet_obj, created_at from tweet
    where hashtag_score is null and created_at >= timestamp '%s' limit %s;
    """ % (timestamp, num_limit)
  db_conn = psycopg2.connect('dbname=drifter')
  rst = DBExecute(
            db_conn, comm, "get tweet_id without hashtag score",
            need_commit=False, return_id=False)
  if db_conn:
    db_conn.close()
  if rst:
    final_rst = [rr[1] for rr in rst]
    return final_rst, rst[-1][2]
  return rst, None

def GetTweetsWithoutURLScore(num_limit=100, timestamp='2019-01-01'):
  comm = """
    select tweet_id, resolved_urls, created_at from tweet
    where url_score is null and created_at >= timestamp '%s'
          and resolved_urls is not null limit %s;
    """ % (timestamp, num_limit)
  db_conn = psycopg2.connect('dbname=drifter')
  rst = DBExecute(
            db_conn, comm, "get tweet_id without url score",
            need_commit=False, return_id=False)
  if db_conn:
    db_conn.close()
  if rst:
    final_rst = [(rr[0], rr[1]) for rr in rst]
    return final_rst, rst[-1][2]
  return rst, None

def GetTweetsWithoutLowCredScore(num_limit=100, timestamp='2019-01-01'):
  comm = """
    select * from (
        SELECT
        tweet_id,
        unnest(resolved_urls) as resolved_urls,
        created_at
        from tweet 
        WHERE
        cardinality(resolved_urls)>0
        and low_cred_score is null 
        and created_at >= timestamp '%s'
        limit %s
    ) as t
    where 
    t.resolved_urls !~ \'twitter.com/\'
    """ % (timestamp, num_limit)

  db_conn = psycopg2.connect('dbname=drifter')
  rst = DBExecute(
            db_conn, comm, "get tweet_id without low-credibility score",
            need_commit=False, return_id=False)
  if db_conn:
    db_conn.close()
  if rst:
    final_rst = [(rr[0], rr[1]) for rr in rst]
    return final_rst, rst[-1][2]
  return rst, None


def GetTweetScores(tweet_id): # keep
  comm_check_in_tweet_score_table = """
    select hashtag_score, url_score from tweet where tweet_id=%s;
  """
  db_conn = psycopg2.connect('dbname=drifter')
  cache_rst = DBExecute(
            db_conn, comm_check_in_tweet_score_table, "get cache scores for tweet %s." % tweet_id,
            param_lst=(str(tweet_id), ),
            need_commit=False, return_id=False)
  if db_conn:
    db_conn.close()
  return cache_rst

def SaveTweetURLScore(tweet_id, score, tweet_id_exist):
  comm_update_url_score = """
    update tweet set url_score=%s where tweet_id=%s;
  """
  comm_insert_url_score = """
    INSERT INTO tweet(tweet_id, url_score)
    VALUES (%s, %s);
  """
  db_conn = psycopg2.connect('dbname=drifter')
  if tweet_id_exist:
    rst = DBExecute(
        db_conn, comm_update_url_score, "update url score for tweet %s" % tweet_id,
        param_lst=(score, str(tweet_id)),
        need_commit=True, return_id=False)
  else:
    rst = DBExecute(
        db_conn, comm_insert_url_score, "insert url score for tweet %s" % tweet_id,
        param_lst=(str(tweet_id), score),
        need_commit=True, return_id=False)
  if db_conn:
    db_conn.close()
  print('save result %s' % str(rst))

def UpdateLowCredScore(df_row):
  db_conn = psycopg2.connect('dbname=drifter')
  comm = """
    update tweet set low_cred_score=%s where tweet_id=%s;
  """
  if not db_conn:
    return False
  tweet_id = df_row['tweet_id']
  score = df_row['low_cred_score']
  rst = DBExecute(
        db_conn, comm, "update low credibility score for tweet %s" % tweet_id,
        param_lst=(score, str(tweet_id)),
        need_commit=True, return_id=False)
  if db_conn:
    db_conn.close()

def SaveTweetHashtagScore(tweet_id, score, tweet_id_exist): # keep
  comm_update_hashtag_score = """
    update tweet set hashtag_score=%s where tweet_id=%s;
  """
  comm_insert_hashtag_score = """
    INSERT INTO tweet(tweet_id, hashtag_score)
    VALUES (%s, %s);
  """
  db_conn = psycopg2.connect('dbname=drifter')
  if tweet_id_exist:
    rst = DBExecute(
        db_conn, comm_update_hashtag_score, "update hashtag score for tweet %s" % tweet_id,
        param_lst=(score, str(tweet_id)),
        need_commit=True, return_id=False)
  else:
    rst = DBExecute(
        db_conn, comm_insert_hashtag_score, "insert hashtag score for tweet %s" % tweet_id,
        param_lst=(str(tweet_id), score),
        need_commit=True, return_id=False)
  if db_conn:
    db_conn.close()
  print('save result %s' % str(rst))


def SaveTweetstoDB(tweets):
  """Save tweets to table Tweets."""
  db_conn = psycopg2.connect('dbname=drifter')
  if not db_conn:
    debug.LogToDebug('psql connection failed in save tweets to db in analysis.')
    return False
  comm = """
    INSERT INTO Tweet(tweet_obj, user_id, tweet_id, created_at) 
    VALUES(%s, %s, %s, %s);
  """
  flag = True
  for tw in tweets:
    tw_id = tw.id_str
    rst = DBExecute(
      db_conn, comm, 'save a Tweet to db',
      (json.dumps(tw._json), tw.user.id_str,
       tw_id, tw.created_at), True)

    if not rst:
      flag = False

  if db_conn:
      db_conn.close()

  return flag


def GetAllConns(whether_follower, ego_usr_screen_name=None, ego_usr_twitter_id=None, hourdelta=24):
  """Get all connections of a twitter user.
  Args:
    whether_follower(bool): false to get friends, and true to get followers.
    ego_usr_screen_name: screen_name of the ego usr.
    ego_usr_twitter_id: twitter id of the ego usr.
    One of ego_usr_screen_name and ego_usr_twitter_id must be given.
    ego_usr_screen_name is only supported for bots.
  Returns:
    a list of connections.
  """
  if not (ego_usr_screen_name or ego_usr_twitter_id):
    return False
  db_conn = psycopg2.connect('dbname=drifter')
  if not db_conn:
    debug.LogToDebug('psql connection failed in GetAllConns in analysis.')
    return False
  if not ego_usr_twitter_id:
    comm = """
      select twitter_user_id from bot
      where screen_name=%s;"""
    ego_usr_twitter_id = DBExecute(
      db_conn, comm, "search_twitter_id_of_a_bot",
      param_lst=(ego_usr_screen_name, ), need_commit=False, return_id=True)

  if not ego_usr_twitter_id:
    if db_conn:
      db_conn.close()
    return False


  comm = """
    SELECT t_usr_id_conn FROM connections 
    WHERE t_usr_id_ego=%s and no_connctions is false 
    and time between %s and %s and conn_type is %s;
  """
  current_time = datetime.now()
  previous_day_time = current_time - timedelta(hours = hourdelta)
  t_usr_ids = DBExecute(
    db_conn, comm, "search_conn_of_a_twitter_id",
    param_lst=(ego_usr_twitter_id, previous_day_time,
               current_time, whether_follower),
    need_commit=False, return_id=False)

  if db_conn:
    db_conn.close()
  if not t_usr_ids:
    return False
  final_usr_ids = []
  for iid in t_usr_ids:
    final_usr_ids.append(iid[0])
  return list(set(final_usr_ids))


def UpdateConn(target_friends_ids, user_id, hourdelta=24):
  comm = """
  UPDATE Connections
    SET conn_tweet_update_time = %s
    WHERE
      t_usr_id_conn = %s and t_usr_id_ego = %s
      and time between %s and %s;
  """
  current_time = datetime.now()
  previous_day_time = current_time - timedelta(hours=hourdelta)
  db_conn = psycopg2.connect('dbname=drifter')
  if not db_conn:
    debug.LogToDebug('psql connection failed in UpdateConn in analysis.')
    return False
  for f_id in target_friends_ids:
    t_usr_ids = DBExecute(
      db_conn, comm, "update connections table with conn_tweet_update_time",
      param_lst=(current_time, f_id, user_id, previous_day_time,
                 current_time),
      need_commit=True, return_id=False)

def getURLsPerTweet():
  get_urls_per_tweet_cmd = """
    With tbl AS (
      select tweet_id,
             json_array_elements(tweet_obj->'entities'->'urls')->>'expanded_url' as url
             from tweet
             where tweet_obj->'entities'->'urls' is not null
                   and resolved_urls is null
      UNION
      select tweet_id,
             json_array_elements(tweet_obj->'retweeted_status'->'entities'->'urls')->>'expanded_url' as url
             from tweet
             where tweet_obj->'retweeted_status'->'entities'->'urls' is not null
                   and resolved_urls is null
    )
    select tweet_id, array_agg(url) as urls from tbl group by tweet_id;
  """
  db_conn = psycopg2.connect('dbname=drifter')
  if not db_conn:
    debug.LogToDebug('psql connection failed in UpdateConn in analysis.')
    return False

  rst = DBExecute(
      db_conn, get_urls_per_tweet_cmd, "get urls per tweet",
      need_commit=False, return_id=False)
  if not rst:
    return False
  return rst

def saveURLStoTweetTbl(tweet_id, urls):
  comm = """
    UPDATE Tweet
      SET resolved_urls = %s
      WHERE
        tweet_id = %s;
  """
  db_conn = psycopg2.connect('dbname=drifter')
  if not db_conn:
    debug.LogToDebug('psql connection failed in UpdateConn in analysis.')
    return False

  rst = DBExecute(
      db_conn, comm, "save resolved urls to db.",
      param_lst=(urls, tweet_id),
      need_commit=True, return_id=False)
  if not rst:
    return False
  return rst

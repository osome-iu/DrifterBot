"""Checks friendships from sampled twitter users to news sources.
"""
import json
from pprint import pprint
import psycopg2
from psycopg2.extensions import AsIs
import pandas as pd
import numpy as np
import tweepy
from tweepy.error import TweepError

customer_API_key = '<sth>'
customer_API_secret_key = '<sth>'

access_token = '<sth>'
access_token_secret = '<sth>'
twitter_app_auth = {
  'consumer_key': customer_API_key,
  'consumer_secret': customer_API_secret_key,
  'access_token': access_token,
  'access_token_secret': access_token_secret
}

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


def _initTweepy():
  auth = tweepy.OAuthHandler(
    twitter_app_auth['consumer_key'],
    twitter_app_auth['consumer_secret'])
  auth.set_access_token(
    twitter_app_auth['access_token'],
    twitter_app_auth['access_token_secret'])
  tweepy_api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
  return tweepy_api

def check_friendship():
  tweepy_api = _initTweepy()
  comm_users = """
    select user_id from SAMPLED_T_ACCOUNTS2 where url_valence is not null
     and user_id not in (select twitter_user_id from CONN_REB2)
     OFFSET floor(random()*26304)
  """
  comms_sources = """
    select twitter_id from news_source;
  """
  comm_conn = """
  INSERT INTO CONN_REB22(twitter_user_id, new_source_twitter_id)
  VALUES (%s, %s);
  """
  db_conn = psycopg2.connect('dbname=drifter')
  users = DBExecute(
        db_conn, comm_users, "get twitter id",
        need_commit=False, return_id=False)
  sources = DBExecute(
        db_conn, comms_sources, "get source id",
        need_commit=False, return_id=False)
  if not users or not sources:
    print("No source or user found", flush=True)
    return
  sources = set([int(s[0]) for s in sources])
  users = [u[0] for u in users]
  for user in users:
    print('current user: %s' % user, flush=True)
    ids = []
    idx = 0
    try:
      for page in tweepy.Cursor(tweepy_api.friends_ids, user_id=user, count=5000).pages():
        ids.extend(page)
      ids = set([int(iid) for iid in ids])
      inter_ids = ids & sources
      if inter_ids:
        print('found inter. %s' % len(inter_ids), flush=True)
      for iid in inter_ids:
        DBExecute(
          db_conn, comm_conn, "update conn",
          param_lst=(user, str(iid)),
          need_commit=True, return_id=False)
    except TweepError:
      tweepy_api = _initTweepy()
  if db_conn:
    db_conn.close()
check_friendship()

import psycopg2
from psycopg2.extensions import AsIs

import numpy as np
import pandas as pd
import os

INIT_SEEDS = [
  'USATODAY',
  'thenation',
  'washingtonpost',
  'WSJ',
  'BreitbartNews',
]  # get their twitter user ids later.

INIT_SEED_MAP = {
  'thenation': [<'drifter_scren_name'>,...],
  'washingtonpost': [],
  'USATODAY': [],
  'WSJ': [],
  'BreitbartNews': []
}


BOT_NAME_MASK = {
  '<you_drifter_screen_name>':'bot<id>', 
}


HASHTAG_USER_TL_SLIDING_WIN_FOR_EACH_BOT = """
SELECT
       distinct tw_score.day, 
       AVG(tw_score.hashtag_score)
         over (order by tw_score.day ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS hashtag_mean,
       VARIANCE(tw_score.hashtag_score)
         over (order by tw_score.day ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS hashtag_var,
       count(*)
         over (order by tw_score.day ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS tw_count
   FROM
   (
       SELECT
           DISTINCT usr_timeline.tweet_id,
           bot.screen_name,
           usr_timeline.hashtag_score,
           date_trunc('day', usr_timeline.created_at) AS day -- date
       FROM
           tweet usr_timeline, bot
       WHERE
           usr_timeline.user_id = bot.twitter_user_id
           AND usr_timeline.created_at < DATE '2019-12-02'
           AND bot.screen_name = '{}'
           AND usr_timeline.hashtag_score is not NULL
   ) AS tw_score
order by tw_score.day;
"""


URL_USER_TL_SLIDING_WIN_FOR_EACH_BOT = """
SELECT
       distinct tw_score.day, 
       AVG(tw_score.url_score)
         over (order by tw_score.day ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS url_mean,
       VARIANCE(tw_score.url_score)
         over (order by tw_score.day ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS url_var,
       count(*)
         over (order by tw_score.day ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS tw_count
   FROM
   (
       SELECT
           DISTINCT usr_timeline.tweet_id,
           bot.screen_name,
           usr_timeline.url_score,
           date_trunc('day', usr_timeline.created_at) AS day
       FROM
           tweet usr_timeline, bot
       WHERE
           usr_timeline.user_id = bot.twitter_user_id
           AND usr_timeline.created_at < DATE '2019-12-02'
           AND bot.screen_name = '{}'
           AND usr_timeline.url_score is not null
   ) AS tw_score
order by tw_score.day;
"""


HASHTAG_HOME_TL_SLIDING_WIN_FOR_EACH_BOT = """
SELECT
       distinct tw_score.day, 
       AVG(tw_score.hashtag_score)
         over (order by tw_score.day ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS hashtag_mean,
       VARIANCE(tw_score.hashtag_score)
         over (order by tw_score.day ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS hashtag_var,
       count(*)
         over (order by tw_score.day ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS tw_count
   FROM
   (
       SELECT
           DISTINCT tw.tweet_id,
           tw.hashtag_score,
           date_trunc('day', checked_at) AS day
       FROM
           home_timeline ht, home_timeline_tweets ht_tw, tweet tw, bot
       WHERE
           ht.bot_id = bot.bot_id
           AND checked_at < DATE '2019-12-02'
           AND ht.id = ht_tw.htl_id
           AND ht_tw.tw_id = tw.tweet_id
           AND bot.screen_name = '{}'
           AND tw.hashtag_score is not null
   ) AS tw_score
ORDER BY tw_score.day;
"""

URL_HOME_TL_SLIDING_WIN_FOR_EACH_BOT = """
SELECT
       distinct tw_score.day, 
       AVG(tw_score.url_score)
         over (order by tw_score.day ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS url_mean,
       VARIANCE(tw_score.url_score)
         over (order by tw_score.day ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS url_var,
       count(*)
         over (order by tw_score.day ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS tw_count
   FROM
   (
       SELECT
           DISTINCT tw.tweet_id,
           tw.url_score,
           date_trunc('day', checked_at) AS day
       FROM
           home_timeline ht, home_timeline_tweets ht_tw, tweet tw, bot
       WHERE
           ht.bot_id = bot.bot_id
           AND checked_at < DATE '2019-12-02'
           AND ht.id = ht_tw.htl_id
           AND ht_tw.tw_id = tw.tweet_id
           AND bot.screen_name = '{}'
           AND tw.url_score is not null
   ) AS tw_score
ORDER BY tw_score.day;
"""

URL_FRIEND_USR_TIMELINE = """
SELECT
       distinct friend_tw_scores.day, 
       AVG(friend_tw_scores.url_score)
         over (order by friend_tw_scores.day ROWS BETWEEN 499 PRECEDING AND CURRENT ROW) AS url_mean,
       VARIANCE(friend_tw_scores.url_score)
         over (order by friend_tw_scores.day ROWS BETWEEN 499 PRECEDING AND CURRENT ROW) AS url_var,
       count(friend_tw_scores.url_score) 
         over (order by friend_tw_scores.day ROWS BETWEEN 499 PRECEDING AND CURRENT ROW) AS url_tw_count
   FROM (
       SELECT
           DISTINCT usr_timeline.tweet_id,
           conn2.t_usr_id_conn,
           usr_timeline.url_score,
           date_trunc('day', conn2.time) AS day
       FROM
           (SELECT conn.t_usr_id_conn, conn.time
            FROM bot, connections conn
            WHERE bot.twitter_user_id = conn.t_usr_id_ego
                  AND conn.time < DATE '2019-12-02'           
                  AND conn.conn_type is false
                  AND conn.conn_tweet_update_time is not null
                  AND bot.screen_name = '{}'
                  AND conn.no_connctions is false) as conn2,
           tweet as usr_timeline
       WHERE
           usr_timeline.user_id = conn2.t_usr_id_conn
           AND usr_timeline.url_score is not null
   ) AS friend_tw_scores
order by friend_tw_scores.day;
"""


HASHTAG_FRIEND_USR_TIMELINE = """
SELECT
       distinct friend_tw_scores.day, 
       AVG(friend_tw_scores.hashtag_score)
         over (order by friend_tw_scores.day ROWS BETWEEN 499 PRECEDING AND CURRENT ROW) AS hashtag_mean,
       VARIANCE(friend_tw_scores.hashtag_score)
         over (order by friend_tw_scores.day ROWS BETWEEN 499 PRECEDING AND CURRENT ROW) AS hashtag_var,
       count(friend_tw_scores.hashtag_score) 
         over (order by friend_tw_scores.day ROWS BETWEEN 499 PRECEDING AND CURRENT ROW) AS hashtag_tw_count
   FROM (
       SELECT
           DISTINCT usr_timeline.tweet_id,
           conn2.t_usr_id_conn,
           usr_timeline.hashtag_score,
           date_trunc('day', conn2.time) AS day
       FROM
           (SELECT conn.t_usr_id_conn, conn.time
            FROM bot, connections conn
            WHERE bot.twitter_user_id = conn.t_usr_id_ego
                  AND conn.time < DATE '2019-12-02'           
                  AND conn.conn_type is false
                  AND conn.conn_tweet_update_time is not null
                  AND bot.screen_name = '{}'
                  AND conn.no_connctions is false) as conn2,
           tweet as usr_timeline
       WHERE
           usr_timeline.user_id = conn2.t_usr_id_conn
           AND usr_timeline.hashtag_score is not null
   ) AS friend_tw_scores
order by friend_tw_scores.day;
"""



def DBExecute(
  conn, command,
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
    print(error)
    conn.rollback()
  finally:
    if cur:
      cur.close()
  return result


def GetTimeSerisMetricForOneSeed(seeds, feature, comm, column_names, filename_prefix, bots_mask, db_conn=None):
  if not db_conn:
    return False
  rst_bot_to_df = {}
  for seed in seeds:
    print(feature,bots_mask.get(seed, seed),filename_prefix)
    result = DBExecute(
      db_conn, comm.format(seed), need_commit=False,
      return_id=False)
    result_df = pd.DataFrame(np.array(result), columns=column_names)
    result_df = result_df.drop_duplicates(subset=['date'], keep='last')
    result_df.to_csv('data/time_series/%s_%s.csv' % (filename_prefix, bots_mask.get(seed,seed)), index=False)
    rst_bot_to_df[seed] = result_df


def generate_all_time_series(db_conn=None, INIT_SEED_MAP={}, bots_mask={}):
    if not db_conn:
      db_conn = psycopg2.connect('dbname=drifter')
  
    for seed, bot_accounts in INIT_SEED_MAP.items():
      print(seed)
      # get bots in seed group
#       bot_accounts = INIT_SEED_MAP[seed]
      # url

      GetTimeSerisMetricForOneSeed(
        bot_accounts, 'url', URL_HOME_TL_SLIDING_WIN_FOR_EACH_BOT,
        ['date', 'url_mean', 'url_var', 'url_count'],
        'url_%s_sliced_home_tl' % seed, 
          db_conn=db_conn,
          bots_mask=bots_mask
      )


      GetTimeSerisMetricForOneSeed(
        bot_accounts, 'url', URL_USER_TL_SLIDING_WIN_FOR_EACH_BOT,
        ['date', 'url_mean', 'url_var', 'url_count'],
        'url_%s_sliced_usr_tl' % seed,
          db_conn=db_conn,
          bots_mask=bots_mask
      )
    
      GetTimeSerisMetricForOneSeed(
        bot_accounts, 'url', URL_FRIEND_USR_TIMELINE,
        ['date', 'url_mean', 'url_var','url_count'],
        'url_%s_sliced_friend_usr_tl' % seed,
          db_conn=db_conn,
          bots_mask=bots_mask
      )

      # hashtag

      GetTimeSerisMetricForOneSeed(
        bot_accounts, 'hashtag', HASHTAG_HOME_TL_SLIDING_WIN_FOR_EACH_BOT,
        ['date', 'hashtag_mean', 'hashtag_var', 'hashtag_count'],
        'hashtag_%s_sliced_home_tl' % seed,
          db_conn=db_conn,
          bots_mask=bots_mask
      )

      GetTimeSerisMetricForOneSeed(
        bot_accounts, 'hashtag', HASHTAG_USER_TL_SLIDING_WIN_FOR_EACH_BOT,
        ['date', 'hashtag_mean', 'hashtag_var', 'hashtag_count'],
        'hashtag_%s_sliced_usr_tl' % seed,
          db_conn=db_conn,
          bots_mask=bots_mask
      )

      GetTimeSerisMetricForOneSeed(
        bot_accounts, 'hashtag', HASHTAG_FRIEND_USR_TIMELINE,
        ['date', 'hashtag_mean', 'hashtag_var', 'hashtag_count'],
        'hashtag_%s_sliced_friend_usr_tl' % seed,
          db_conn=db_conn,
          bots_mask=bots_mask
      )

    if db_conn:
      db_conn.close()
    
            
            
def main():
    generate_all_time_series(None, INIT_SEED_MAP, BOT_NAME_MASK)

if __name__ == "__main__":
    main()

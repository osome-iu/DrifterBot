"""Manage all commands related to the database, psql."""
import time
from config_stat import conn_save_freq, mashape_key, twitter_app_auth, unfollow_method
from datetime import datetime
from datetime import timedelta
import debug
import json
import source
import sys
import psycopg2
from psycopg2.extensions import AsIs


class DataManager(object):

  def __init__(self, username, bot_id=None, init_bot_id=True):
    self.username = username
    self.twitter_usr_id = None
    self.tl_id = None
    self.conn = psycopg2.connect('dbname=drifter')
    if not self.conn:
      raise Exception('psql connection failed.')

    # get the bot_id of the current user.
    self.bot_id = None
    if init_bot_id:
      if bot_id:
        self.bot_id = bot_id
      else:
        tmp = self.getBotID()
        self.bot_id, self.twitter_usr_id = tmp[0]
      if not self.bot_id:
        raise Exception('cannot get bot id.')
  
  def __del__(self):
    if self.conn:
      self.conn.close()

  def SaveBackground(self):
    rst = self.SaveCurrentConnection()
    self.SaveCurrentHomeTimeline()

  def _execute(self, command, method, param_lst=None, need_commit=False, return_id=False):
    """save data to psql."""
    result = True
    try:
      if not self.conn:
        self.conn = psycopg2.connect('dbname=drifter')
      cur = self.conn.cursor()
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
        self.conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
      print('SQL error:')
      print(error)
      print(command)
      result = False
      self.conn.rollback()
    finally:
      if cur:
        cur.close()
    return result

  def getBotID(self):
    comm = u"""
      SELECT bot_id, twitter_user_id from Bot where screen_name = %s
      ORDER BY init_timestamp DESC NULLS LAST;
    """
    return self._execute(comm, 'getBotID', ('%s' % (self.username),), False)

  def SaveCurrentHomeTimeline(self):
    try:
      print(self.username)
      source_obj = source.HomeTimeLine(self.username)
      source_data = source_obj.getSourceData()
      if not source_data:
        raise ValueError('cannot obtain hometimeline')
    except ValueError as e:
      debug.LogToDebug('=======\nfailed to save hometimeline for bot %s at %s\n' %(self.username, datetime.now()))
      debug.LogToDebug(str(e))
    print('save htl 1')
    if source_data:

      dt = datetime.now()
      comm_htl = """
      INSERT INTO home_timeline(bot_id, checked_at) 
      VALUES(%s, %s) RETURNING id;
      """
      self.tl_id = self._execute(
        comm_htl, 'home_timeline created',
        (self.bot_id, dt), True, True)
      print('save htl 2')
      print('self.tl_id is %s' % self.tl_id)
      comm_htl_tw = """
        INSERT INTO home_timeline_tweets(htl_id, tw_id) 
         VALUES(%s, %s);
      """

      comm_tweets = """
        insert into tweet(tweet_obj, tweet_id, created_at)
                    values(%s, %s, %s);
      """
      
      for tweet in source_data:
        self._execute(
          comm_tweets, 'tweet table update',
          (json.dumps(tweet), tweet['id'],
           time.strftime(
             '%Y-%m-%d %H:%M:%S',
             time.strptime(tweet['created_at'],'%a %b %d %H:%M:%S +0000 %Y'))), True)

        self._execute(
          comm_htl_tw, 'tweet table update in home_timeline_tweets',
          (self.tl_id, tweet['id']), True)

  
  def SaveConnections(
    self, connection_lst, special_conn_lst, ego_id, conn_type):
    """ Update Connection table.

    Args:
      ego_id: the twitter user id of the current user.
      connection_lst: a list of the friend/follower user ids of the ego_id.
      special_conn_lst: the list of the friend/follower user ids whose tweets are
                        saved this time. special_conn_lst is a subset of connection_lst.
      conn_type: friend (False) or follower (True)

    Returns:
      All connections are saved or not (bool)

    """
    current_ts = datetime.now()

    comm11 = """
      INSERT INTO Connections(t_usr_id_ego, t_usr_id_conn, conn_type, conn_tweet_update_time) 
      VALUES(%s, %s, %s, %s);
    """

    comm12 = """
      INSERT INTO Connections(t_usr_id_ego, t_usr_id_conn, conn_type) 
      VALUES(%s, %s, %s);
    """

    comm21 = """
      SELECT conn_tweet_update_time from Connections 
      WHERE t_usr_id_conn=%s AND conn_tweet_update_time IS NOT NULL 
        AND no_connctions is false 
      ORDER BY conn_tweet_update_time DESC NULLS LAST 
      LIMIT 1;
    """

    flag = True
    for usr in connection_lst:
      # 1. check whether usr in special_conn_lst
      if usr in special_conn_lst: # 2. if 1. yes
        rst = self._execute(
          comm11, 'save connections1 to db',
          (str(ego_id), str(usr), conn_type, current_ts), need_commit=True)
        if not rst:
          flag = False
      else: # 3. if 1. no
        # 3.1 check the last time that usr's tweets are saved
        rst = self._execute(
          comm21, 'find the latest conn tweet save time',
          (str(usr), ), return_id=True)
        if not rst:
          param_lst = (str(ego_id), str(usr), conn_type)
          rst2 = self._execute(
            comm12, 'save connections2 to db',
            param_lst, need_commit=True)
        else:
          param_lst = (str(ego_id), str(usr), conn_type, rst)
          rst2 = self._execute(
            comm11, 'save connections2 to db',
            param_lst, need_commit=True)
        if not rst2:
          flag = False

    return flag

  def SaveCurrentConnection(self):
    """save friends and followers"""
    def DealConnectionInfo(
      twitter_usr_id, connection_type, # friends or followers
      class_object):
      #   1. check what's the last time this info is saved
      check_last_timestamp = """
      SELECT time from Connections WHERE t_usr_id_ego=%s
      ORDER BY time DESC NULLS LAST LIMIT 1;
      """
      param_lst = (twitter_usr_id, )
      rst = self._execute(
        check_last_timestamp, 'get last time from connections for bot %s' % twitter_usr_id,
        param_lst, False)
      print('latest time is :%s' % rst)
      if rst and rst[0][0] <= datetime.now() - timedelta(hours = conn_save_freq):
        print('pass save connection...')
        return rst[0][1]
      #   2. if it's longer than the config_state.conn_save_freq hours, update the table
      try:
        source_data = class_object.getSourceData()
        if not source_data:
          raise ValueError('cannot obtain %s twitter api data' % connection_type)
      except ValueError as e:
        debug.LogToDebug(
          '=======\nfailed to save %s for'
          ' bot %s at %s\n' %(connection_type, self.username, datetime.now()))
        debug.LogToDebug(str(e))
        source_data = None
      if source_data:
        connection_type = False if connection_type == 'Friends' else True
        flag = self.SaveConnections(
          source_data, [], twitter_usr_id, connection_type)
      return rst

    source_obj = source.Friends(self.username, whether_user_entity=False)
    self.fr_id = DealConnectionInfo(self.twitter_usr_id, 'Friends',  source_obj)
    source_obj = source.Followers(self.username, whether_user_entity=False)
    self.fo_id = DealConnectionInfo(self.twitter_usr_id, 'Followers', source_obj)


  def SaveCurrentAction(self, source_name, action, result_code):
    try:
      content = {}

      if action == 'follow' and result_code and result_code < 0:
        action = 'unfollow'
        if result_code:
          result_code = -result_code

      if action == 'unfollow' and result_code and result_code < 0 :
        action = 'follow'
        result_code = -result_code

      if action == 'unfollow':
        source_name = unfollow_method

      if action == 'like' or action == 'retweet':
        if result_code:
          source_obj = source.TweetObj(self.username, result_code)
          content = source_obj.getSourceData()
          if not content:
            raise Exception('ahh0.')
      elif action == 'follow' or action == 'unfollow':
        if result_code:
          source_obj = source.UserObj("", user_id=result_code)
          content = source_obj.getSourceData()
          if not content:
            raise Exception('ahh1.')
      elif action == 'replymention':
        if result_code:
          source_obj = source.UserTimeLine(self.username, 1)
          content = source_obj.getSourceData()
          if content:
            content = content[0]
          else:
            raise Exception('ahh2.')
      else: # tweet
        if result_code:
          source_obj = source.UserTimeLine(self.username, 1)
          content = source_obj.getSourceData()
          if content:
            content = content[0]
          else:
            raise Exception('ahh3.')
    except Exception as e:
      content = {
        "error":"restore result object failed via using Twitter API.",
        "result_code": result_code
      }
      debug.HandleException(sys.exc_info())
      debug.LogToDebug('savecurrentaction failure:\n %s' % str(e))


    insert_conn = """
          INSERT INTO Action(bot_id, source, action, result, tl_id) 
          VALUES(%s, %s, %s, %s, %s);
        """
    try:
      content_json = json.dumps(content)
      param_lst = (
        self.bot_id, source_name, action,
        content_json, self.tl_id)

      rst = self._execute(
        insert_conn, 'insert_action_table',
        param_lst, True, return_id=False
      )
    except Exception as e:
      debug.HandleException(sys.exc_info())
      debug.LogToDebug(str(content))
    return rst

  def TheLastMentionResult(self):
    """Get the last tweet the bot replied."""
    comm = """ 
      select result->>'in_reply_to_status_id' from action
      where result::text like '%%in_reply_to_status_id%%'
      AND action='replymention' AND bot_id = %s order by timestamp desc limit 1;
    """
    rst = self._execute(comm, 'select the latest reply_mention action', (self.bot_id,))
    
    if rst:
      return rst[0][0]
    else:
      return None

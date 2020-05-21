"""Used before an experiment starts. For insert the bot information."""
from bot import action
import json
import psycopg2
from bot import source
from datetime import datetime
from bot.config_stat import *
from bot import source
import numpy as np

NUM_FRIENDS = 5
NUM_FOLLOWERS = 5

def buildParamJSON():
  result = {}
  result['conn_save_freq'] = conn_save_freq
  result['prob_event'] = prob_event
  result['activation_time'] = [activation_time[0], activation_time[1]]
  result['num_timeline_tweets'] = num_timeline_tweets
  result['trend_loc_code'] = trend_loc_code
  result['num_liked_tweets'] = num_liked_tweets

  result['mention_tl_num'] = mention_tl_num
  result['like_prob'] = like_prob
  result['follow_ratio'] = follow_ratio
  result['mamximum_follow_ignore_ratio_bound'] = mamximum_follow_ignore_ratio_bound
  result['follow_prob'] = follow_prob

  result['num_friends_to_lookat_inFoF'] = num_friends_to_lookat_inFoF
  result['unfollow_method'] = unfollow_method
  result['num_topics_in_trends'] = num_topics_in_trends
  result['num_tweets_in_each_topic'] = num_tweets_in_each_topic
  result['num_latest_tweets_to_look_likes'] = num_latest_tweets_to_look_likes
  result['tweet_prob'] = tweet_prob

  return json.dumps(result)


def InsertBot(
  name, screen_name, password,
  twitter_id, init_friend_screen_name): 
  source_obj = source.UserObj(init_friend_screen_name)
  friend_obj = source_obj.getSourceData()
  param_json = buildParamJSON()
  if not friend_obj:
    raise Exeception('cannot this friend')

  bot_create_command = u"""
    INSERT INTO Bot(screen_name, twitter_banner_name, password, twitter_user_id,
                    init_friend, init_timestamp, param)
    VALUES(%s, %s, %s, %s, %s, %s, %s);
    """
  try:
    conn = psycopg2.connect('dbname=drifter')
  except:
    raise Exception('psql conn failed')

  try:
    cur = conn.cursor()
    cur.execute(
      bot_create_command,
      (screen_name, name, password, twitter_id, json.dumps(friend_obj), datetime.now(), param_json))
    conn.commit()
  except (Exception, psycopg2.DatabaseError) as error:
    print(error)
  finally:
    if conn is not None:
      conn.close()



class FriendShip(action.Action):

  def __init__(self, username):
    super().__init__(username)
    self.twitter_id = None

  def composeCmd(self, user_id):
    cmd = [
      'twurl', '-X', 'POST',
      '/1.1/friendships/create.json?screen_name=%s&follow=true' % user_id,
      '-u', self.username]
    return cmd

  def act(self, friend_lst):
    count = 0
    for f in friend_lst:
      if_suc = self.apiAct(f)
      if if_suc:
        count += 1

    print('%s friends built' % count)



def _RandomizeFriendsnFollowers(
  official_account, bot_screen_name,
  follow_friends, follow_followers):
  ff = FriendShip(bot_screen_name)
  ff.act([official_account])
  if follow_friends:
    friend_lst = []
    weight_lst = []
    friend_objs = source.Friends(official_account, whether_user_entity=True)
    friend_obj_lst =friend_objs.getSourceData()
    if not friend_obj_lst:
      print('friend failed')
    for f in friend_obj_lst:
      friend_lst.append(f['screen_name'])
      weight_lst.append(f['followers_count'])
    sum_followers = float(sum(weight_lst))
    weight_lst = [w/sum_followers for w in weight_lst]
    selected_friend = np.random.choice(friend_lst, size=5, replace=False, p=weight_lst)
    ff.act(selected_friend)

  if follow_followers:
    follower_lst = []
    weight_lst = []
    follower_objs = source.Followers(official_account, whether_user_entity=True)
    follower_obj_lst = follower_objs.getSourceData()
    if not follower_obj_lst:
      print('follower failed')
    
    for f in follower_obj_lst:
      follower_lst.append(f['screen_name'])
      weight_lst.append(f['followers_count'])
    sum_followers = float(sum(weight_lst))
    weight_lst = [w/sum_followers for w in weight_lst]
    selected_friend = np.random.choice(follower_lst, size=5, replace=False, p=weight_lst)

    ff.act(selected_friend)

    

def InitTwitter(profiles, update_db=False):
  for profile in profiles:
    print('profile:%s' % str(profile))
    _RandomizeFriendsnFollowers(
      profile[4], profile[1],
      True, True)
    
    if update_db:
      InsertBot(
        profile[0], profile[1], profile[2],
        profile[3], profile[4])


profiles = [ ('<banner name>', '<screen name>', '<password>', '<twitter user id>', '<initial seed>')]

InitTwitter(profiles)

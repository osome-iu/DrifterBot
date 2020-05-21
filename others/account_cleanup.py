"""clean up an account after an experiment.

Using command line 
python account_cleanup.py <DRIFTER_SCREEN_NAME>

Delete:
  1. friend list
  2. follower list  ## block and then unblock them
  3. tweet
  4. like

"""

import source
from action import Action
import sys


class UserTimeLine(source.Source):

  def __init__(self, username):
    super().__init__(username)

  def composeCmd(self):
    cmd = [
      'twurl',
      '/1.1/statuses/user_timeline.json?screen_name=%s&include_rts=true&count=200' % self.username]
    return cmd

  def getSourceData(self):
    raw_rst = self.getRawResult()
    if not raw_rst:
      return False
    tweet_ids = []
    for r in raw_rst:
      tweet_ids.append(r['id'])
    return tweet_ids


class UnfollowAFriend(Action):

  def __init__(self, username):
    super().__init__(username)

  def composeCmd(self, user_id):
    cmd = [
      'twurl', '-X', 'POST',
      '/1.1/friendships/destroy.json?user_id=%s' % user_id,
      '-u', self.username
    ]
    return cmd

  def act(self, user_id):
    if_suc = self.apiAct(user_id)
    return if_suc


class DeleteTweet(Action):

  def __init__(self, username):
    super().__init__(username)

  def composeCmd(self, tweet_id):
    cmd = [
      'twurl', '-X', 'POST',
      '/1.1/statuses/destroy/%s.json' % tweet_id,
      '-u', self.username
    ]
    return cmd

  def act(self, t_id):
    if_suc = self.apiAct(t_id)
    return if_suc


class UnlikeTweet(Action):

  def __init__(self, username):
    super().__init__(username)

  def composeCmd(self, tweet_id):
    cmd = [
      'twurl', '-X', 'POST',
      '/1.1/favorites/destroy.json?id=%s' % tweet_id,
      '-u', self.username
    ]
    print(cmd)
    return cmd

  def act(self, t_id):
    if_suc = self.apiAct(t_id)
    return if_suc


class BlockUser(Action):

  def __init__(self, username):
    super().__init__(username)

  def composeCmd(self, user_id):
    cmd = [
      'twurl', '-X', 'POST',
      '/1.1/blocks/create.json?user_id=%s&skip_status=1' % user_id,
      '-u', self.username
    ]
    return cmd

  def act(self, user_id):
    if_suc = self.apiAct(user_id)
    return if_suc

class UnBlockUser(Action):

  def __init__(self, username):
    super().__init__(username)

  def composeCmd(self, user_id):
    cmd = [
      'twurl', '-X', 'POST',
      '/1.1/blocks/destroy.json?user_id=%s&skip_status=1' % user_id,
      '-u', self.username
    ]
    return cmd

  def act(self, user_id):
    if_suc = self.apiAct(user_id)
    return if_suc


def cleanup(username):
  
  friend_obj = source.Friends(username, whether_user_entity=False)
  friend_id_lst = friend_obj.getSourceData()
  if friend_id_lst:
    unfollow_obj = UnfollowAFriend(username)
    for f in friend_id_lst:
      flag = unfollow_obj.act(f)
      if not flag:
        print('friend:%s failed to delete' % f)
  else:
    print('fail to delete friends')

  user_timeline = UserTimeLine(username)
  tweet_ids = user_timeline.getSourceData()
  print(tweet_ids)
  if not tweet_ids:
    print('fail to delete timeline')
  else:
    tweet_deleter = DeleteTweet(username)
    for t in tweet_ids:
      flag = tweet_deleter.act(t)
      if not flag:
        print('tweet:%s failed to delete' % t)



  liked_tweet_obj = source.LikedTweets(None, user_name=username, num_tweets=200)
  liked_tweet_ids = liked_tweet_obj.getSourceData(return_key='id')
  if not liked_tweet_ids:
    print('fail to unlike tweet...')
  else:
    unlike_obj = UnlikeTweet(username)
    for t in liked_tweet_ids:
      flag = unlike_obj.act(t)
      if not flag:
        print('like fails (%s)' % t)
  

  follower_obj = source.Followers(username)
  followers = follower_obj.getSourceData()
  if not followers:
    print('follower cleanup fails')
  else:
    block_obj = BlockUser(username)
    suc_f_ids = []
    for f_id in followers:
      flag = block_obj.act(f_id)
      if not flag:
        print('%s is not blocked' % f_id)
      else:
        suc_f_ids.append(f_id)

    unblock_obj = UnBlockUser(username)
    for f_id in suc_f_ids:
      flag = unblock_obj.act(f_id)
      if not flag:
        print('%s is not unblocked' % f_id)


if __name__ == "__main__":
  argvs = sys.argv
  if len(argvs) > 1:
    print(argvs[1:])
    for username in argvs[1:]:
      cleanup(username)
  else:
    print('CLEANUP!The bot username is not defined.')










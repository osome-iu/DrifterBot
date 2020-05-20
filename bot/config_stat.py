# For the drifters to work, you need to fill in your Twitter APP key. 
# The probability values are hidden here. You can decide the values by youself.
# The values used in our paper can be found in the manuscript.

################# Access Keys #######################
mashape_key = ''
customer_API_key = ''
customer_API_secret_key = ''

access_token = ''
access_token_secret = ''
twitter_app_auth = {
  'consumer_key': customer_API_key,
  'consumer_secret': customer_API_secret_key,
  'access_token': access_token,
  'access_token_secret': access_token_secret
}

conn_save_freq = 12
##### Probability of each action for bot #####

prob_event = {
  'like': 1.0,
  'retweet': 0.,
  'follow': 0.,
  'unfollow': 0.,
  'tweet': 0.,
  'replymention':0.
}
activation_time = (12, 13)  # during the time, the bot can be activated



##### Source Configuration #####
num_timeline_tweets = 1
trend_loc_code = 23424977  # 1 is the global trends. US:23424977
num_liked_tweets = 1
mention_tl_num = 1



##### Action #####

## Like ##
# In action Like, the probability distribution of its sources.

like_prob = {
  'trend': 0.,
  'timeline': 0.,
  'like': 0.
}
## Follow ##
follow_ratio = 1
mamximum_follow_ignore_ratio_bound = 1
# In action Follow, the probability distribution of its sources.

follow_prob = {
  'FoF': 0., # friends of friends
  'timeline': 1.,
  'liked': 0.,
  'follower': 0.
}
num_friends_to_lookat_inFoF = 3

## Unfollow ##
unfollow_method = 'weighted'  # weighted or uniform
minimum_friends = 1
## Randomization ###
# Randomization related to Trends
num_topics_in_trends = 1
num_tweets_in_each_topic = 1
# Randomization related to Likes
num_latest_tweets_to_look_likes = 1

## Tweet ##

tweet_prob = {
  'timeline':0.,
  'trend':0.,
  'random_quotes':1
}

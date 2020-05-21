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

##### The frequency (hour) to save hometimeline, friends and followers for drifters into the database
conn_save_freq = 12

##### Number of friends/followers when the drifter account is initialized along with the initial friends
##### The parameters are used in others/init_bot_info.py
NUM_FRIENDS = 1
NUM_FOLLOWERS = 1

##### Probability of each action for bot #####
prob_event = {
  'like': 1.0,
  'retweet': 0.,
  'follow': 0.,
  'unfollow': 0.,
  'tweet': 0.,
  'replymention':0.
}

# Defines the time window that drifers can be active each day.
# The first number is the start hour, and the second number is the end hour.
# E.g., (7,13) means drifters can be activated from 7am to 1pm.
activation_time = (7, 13)

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
#### The maximum difference between friends and followers
#### Once number of friends - number of followers > mamximum_delta_between_friends_and_followers
#### the drifter cannot follow new accounts.
mamximum_delta_between_friends_and_followers = 33
# In action Follow, the probability distribution of its sources.
follow_prob = {
  'FoF': 0., # friends of friends
  'timeline': 1.,
  'liked': 0.,
  'follower': 0.
}
## When FoF is selected as the source of following new accounts,
## the drifter randomizes num_friends_to_lookat_inFoF friends and then look at their friends.
num_friends_to_lookat_inFoF = 3

## Unfollow ##
unfollow_method = 'weighted'  # weighted or uniform
## If number of friends are less than minimum_friends, the drifter doesn't unfollow anyone.
## Instead it follow one account.
minimum_friends = 1

## Randomization ###
# Randomization related to Trends
num_topics_in_trends = 1
num_tweets_in_each_topic = 1

## It's used in the source Tweets Liked by Friends.
## A drifter selects num_latest_tweets_to_look_likes friends
## that have Tweets shown in the drifter's home timeline, and then
## look at the Tweets liked by these friends.
num_latest_tweets_to_look_likes = 1

## Tweet ##
### The source probabilities used in Tweet action
tweet_prob = {
  'timeline':0.,
  'trend':0.,
  'random_quotes':1
}

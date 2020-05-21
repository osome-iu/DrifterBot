"""A daily cron job to collect tweets of friends and followers.
"""
from metric.analysis import Analyzer

### Daily Cron Job ###
### Fetches Tweets from connections of bots
### Please set the activation time out of the bot activation time range
### to avoid Twitter API rate limit.
DRIFTERS = ['your_bot_screen_name']
analyzer = Analyzer()
analyzer.FetchConnTweets(DRIFTERS)
### End Daily Cron Job ###

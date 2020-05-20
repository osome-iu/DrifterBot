"""This script runs jobs in metric folder.
Please call the following functions as instruction below before executing codes
in exps folder.
"""
from metric.analysis import Analyzer
from metric import resolve_url

### Daily Cron Job ###
### Fetches Tweets from connections of bots
### Please set the activation time out of the bot activation time range
### to avoid Twitter API rate limit.
# BOTS = ['your_bot_screen_name']
#analyzer = Analyzer()
#analyzer.FetchConnTweets(BOTS)
### End Daily Cron Job ###

### Compute Metric scores for each Tweet ###
## 1. Build resolved_urls in Tweet table.
##    It must be called before computing url-based scores.
#resolve_url.get_expanded_url()
## 2. Computes url-based score for each tweet
# analyzer = Analyzer()
# analyzer.ComputeURLTweetScore()
## 3. Computes hashtag-based score for each tweet
# analyzer = Analyzer()
# analyzer.ComputeHashTagTweetScore()
## 4. Computes low credibility score for each tweet
# analyzer = Analyzer()
# analyzer.ComputeLowCredTweetScore()
###End Computing Metric scores for each Tweet ###

"""A daily cron job to collect tweets of friends and followers. 
Run this as a daily cron job. 
Be sure to run this when the drifters are inactive to avoid running into the Twitter API limit.
"""

from metric.analysis import Analyzer

DRIFTERS = ['drifter_screen_name', ...]
analyzer = Analyzer()
analyzer.FetchConnTweets(DRIFTERS)

from metric.analysis import Analyzer
from metric import resolve_url

### Compute Metric scores for each Tweet ###
## 1. Build resolved_urls in Tweet table.
##    It must be called before computing url-based scores.
resolve_url.get_expanded_url()
## 2. Computes url-based score for each tweet
analyzer = Analyzer()
analyzer.ComputeURLTweetScore()
## 3. Computes hashtag-based score for each tweet
analyzer = Analyzer()
analyzer.ComputeHashTagTweetScore()
## 4. Computes low credibility score for each tweet
analyzer = Analyzer()
analyzer.ComputeLowCredTweetScore()
###End Computing Metric scores for each Tweet ###

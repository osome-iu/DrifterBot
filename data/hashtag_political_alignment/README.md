# Introduction

This folder contains the scripts to generate the political alignment scores for the hashtags.

# Hashtag embedding

First, we need to generate the embedding for the hashtags.
The input should be the 'sentences' of hashtags.
For every tweet, we extract the hashtags in it and treat them as a sentence.
Here is an example:

```
["stayinline", "mytexasvotes", "teambeto"]
```
Note that we remove the # and convert everything to lower-case.

Tweets with only one hashtag are ignored.
The file `hashtag_sentences.json.gz` contains an illustrative example of the input file used for training the hashtag embedding. The actual file is omitted to comply with Twitter API guidelines about resharing content. 
The input file should have the following format:

```
[
    ["stayinline", "mytexasvotes", "teambeto"],
    ["breaking","protecting","public"]
    ...
]
```

To generate the embedding with 100 dimensions, run the following command in the unix shell:

```
python hashtag_embedding.py hashtag_sentences.json.gz 100 hashtag_embedding.csv.gz
```

This will generate a CSV file containing the embedding of each hashtag.

# Political alignment score

With the embedding of the hashtags, we can analyze their political alignment.
This can be achieved with the following command:

```
python generate_hashtag_alignment.py hashtag_embedding.csv.gz 100 hashtag_alignment.csv.gz
```

where `hashtag_alignment.csv.gz` contains the alignment scores for the hashtags.
The results need further calibration to ensure the center is corresponding to the neutral point in the political spectrum. This is explained in the paper and done by the `load_data()` function in the `exps/plot_helper.py` script.

When using the code in other contexts, the anchor hashtags in the script need to be changed.

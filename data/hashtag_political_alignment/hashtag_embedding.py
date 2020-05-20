"""
This script takes a file of hashtag sentences and generate the embedding
We provide hashtag_sentences.json.gz as an example.

Input:
    argv[1]: path to the sentences
    argv[2]: embedding dimensions
    argv[-1]: output path

In shell, run:
    python hashtag_embedding.py hashtag_sentences.json.gz 100 hashtag_embedding.csv.gz
"""
import sys
import gzip
import json
import pandas as pd
from gensim.models import Word2Vec

sentence_path = sys.argv[1]
embedding_size = int(sys.argv[2])
out_path = sys.argv[-1]

with gzip.open(sentence_path) as f:
    sentences = json.load(f)
    #sentences = list(map(lambda x: x[1], temp_sentences))

print("Construct the w2v model")
w2v_model = Word2Vec(
    min_count=5,
    window=10,
    size=embedding_size,
    sample=6e-5,
    alpha=0.03,
    min_alpha=0.0007,
    negative=20,
    workers=6,
)

w2v_model.build_vocab(sentences)

print("Start to train the model")
w2v_model.train(
    sentences,
    total_examples=w2v_model.corpus_count,
    epochs=10
)


print("Start to extract the word vectors...")
hashtag_labels = []
hashtag_vecs = []
for word, value in w2v_model.wv.vocab.items():
    hashtag_labels.append([word, value.count])
    hashtag_vecs.append(w2v_model.wv[word])

hashtag_vecs_df = pd.DataFrame(hashtag_vecs)
hashtag_labels_df = pd.DataFrame(
    hashtag_labels, columns=['hashtag', 'num']
)

hashtag_vecs_df['hashtag'] = hashtag_labels_df['hashtag']
hashtag_vecs_df['num'] = hashtag_labels_df['num']

print("Start to dump the word vectors...")
hashtag_vecs_df.to_csv(out_path, compression='gzip', index=None)
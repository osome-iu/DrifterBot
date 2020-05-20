"""
This script takes the hashtag embedding and generate the alginment of the hashtags
using the given anchors

Input:
    argv[1]: path to hashtag embedding
    argv[2]: embedding dimension
    argv[-1]: output path
    
In shell, run:
    python generate_hashtag_alignment.py hashtag_embedding.csv.gz 100 hashtag_alignment.csv.gz
"""
import sys
import pandas as pd
import scipy.spatial
import gzip
import json
from tqdm import tqdm


class FullEmbedding:
    def __init__(
        self,
        embedding_path,
        anchor_nodes,
        embedding_dim
    ):
        self.embedding_dim = embedding_dim
        self.left_anchor, self.right_anchor = anchor_nodes
        self.embedding_path = embedding_path
        self.embedding_df = pd.read_csv(self.embedding_path)
        self.range_cols = list(map(str, range(100)))
        self.embedding_vec_df = self.embedding_df[self.range_cols]
        self.word_index = dict(self.embedding_df.hashtag.reset_index()[['hashtag', 'index']].values)
        
        self.left_anchor_vec = self.get_vec(self.left_anchor)
        self.right_anchor_vec = self.get_vec(self.right_anchor)
        
        self.u = self.right_anchor_vec - self.left_anchor_vec
    
    def get_vec(self, index):
        if isinstance(index, int):
            return self.embedding_vec_df.loc[index].values
        elif isinstance(index, str):
            word_index = self.word_index.get(index)
            if word_index is not None:
                return self.embedding_vec_df.loc[word_index].values
            else:
                return None
        else:
            return None
    
    def get_relative_vec(self, co_words):
        vecs = []
        for word in co_words:
            co_vec = self.get_vec(word)
            if co_vec is not None:
                vecs.append(co_vec)
        vecs = np.asarray(vecs)
        mean_vec = vecs.mean(axis=0)
        temp_sub = vecs - mean_vec
        deviations = np.sqrt((temp_sub**2).sum(axis=1))
        return mean_vec, deviations.mean(), deviations.std() / len(deviations)
    
    def get_self_vec(self, index):
        vec = self.get_vec(index)
        if vec is None:
            return None
        else:
            return self.get_projected_vec(vec)
    
    def get_projected_vec(self, vec):
        vec = ((vec - self.left_anchor_vec).dot(self.u) / self.u.dot(self.u)) * self.u + self.left_anchor_vec
        dis_l = scipy.spatial.distance.euclidean(vec, self.left_anchor_vec)
        dis_r = scipy.spatial.distance.euclidean(vec, self.right_anchor_vec)
        return vec, dis_l, dis_r
    

    def good(self):
        pass
    

    
if __name__ == "__main__":
    embedding_path = sys.argv[1]
    embedding_dimension = int(sys.argv[2])
    output_path = sys.argv[-1]
    fe = FullEmbedding(embedding_path, ['voteblue', 'votered'], embedding_dimension)
    
    hashtag_pos_list = []
    for i in tqdm(fe.embedding_df[fe.embedding_df.num > 5].index):
        _, l_dis, r_dis = fe.get_projected_vec(fe.get_vec(i))
        hashtag_pos_list.append([fe.embedding_df.hashtag[i], l_dis, r_dis])
        
    hashtag_pos_df = pd.DataFrame(hashtag_pos_list, columns=['hashtag', 'l_dis', 'r_dis'])
    
    hashtag_pos_df['alignment'] = (hashtag_pos_df.l_dis / (hashtag_pos_df.l_dis + hashtag_pos_df.r_dis)) * 2 - 1
    
    hashtag_pos_df[['hashtag', 'alignment']].to_csv(output_path, index=None, compression='gzip')
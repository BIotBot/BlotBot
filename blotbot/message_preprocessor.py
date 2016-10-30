from nltk.corpus import stopwords
from nltk.tokenize import TweetTokenizer
from nltk.stem import WordNetLemmatizer
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
import string
import os.path
import re

toxic_list = [
    'gay', 'homo', 'jerk', 'dick', 'whore', 'bitch', 'tits', 'boobs', 'nips',
    'fag', 'faggot', 'cock', 'cunt', 'nigger', 'chink', 'pussy', 'retard',
    'rape'
]
pattern_toxic = re.compile('|'.join(toxic_list))

class NltkPreprocessor(BaseEstimator, TransformerMixin):
    def __init__(self):
        self.tokenizer = TweetTokenizer(preserve_case=False, reduce_len=True)
        self.lemmatizer = WordNetLemmatizer()
        self.stopwords = stopwords.words('english')
        self.punctuation = set(string.punctuation)

        self.y = []

    def transform(self, X):
        ret = []

        for message in X:
            message = str(message) # in case pandas acts weird
            tokens = list(self.tokenize(message))
            ret.append(tokens)

            toxic = self.is_toxic(tokens)
            self.y.append(toxic)

        return ret

    def tokenize(self, msg):
        tokens = self.tokenizer.tokenize(msg)

        for token in tokens:
            token = self.lemmatizer.lemmatize(token)

            if token in self.stopwords or token in self.punctuation:
                continue

            yield token

    def is_toxic(self, token_list):
        for token in token_list:
            if pattern_toxic.search(token):
                return True
        return False

def identity(x): return x

def create_vectorizer(partial=False):
    return TfidfVectorizer(tokenizer=identity,
                           preprocessor=None,
                           lowercase=False,
                           ngram_range=(1,1))

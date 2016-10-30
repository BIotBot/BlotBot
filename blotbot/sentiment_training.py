from nltk.corpus import stopwords
from nltk.tokenize import TweetTokenizer
from nltk.stem import WordNetLemmatizer
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
from sklearn.naive_bayes import BernoulliNB
from sklearn.metrics import classification_report as clsr
from sklearn.model_selection import cross_val_predict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cross_validation import train_test_split as tts
import pickle
import string
import os.path
import re

toxic_list = [
    'gay', 'homo', 'jerk', 'dick', 'whore', 'bitch', 'tits', 'boobs', 'nips',
    'fag', 'faggot', 'cock', 'cunt', 'nigger', 'chink', 'pussy', 'retard',
    'rape'
]
pattern_toxic = re.compile('|'.join(toxic_list))

def identity(x): return x

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

def load_corpus(chat_log_file):
    if os.path.isfile(chat_log_file + '.pkl'):
        with open(chat_log_file + '.pkl', 'rb') as cache_file:
            print("loaded data from cache")
            return pickle.load(cache_file)

    preprocessor = NltkPreprocessor()
    df_chat = pd.read_csv(chat_log_file)

    docs = [row['key'] for index, row in df_chat.iterrows()]
    X = preprocessor.transform(docs)
    y = preprocessor.y

    with open(chat_log_file + '.pkl', 'wb') as cache_file:
        print("wrote cache file")
        pickle.dump((X, y), cache_file)

    return (X, y)

def get_model(classifier):
    return Pipeline([
        ('vectorizer', TfidfVectorizer(
            tokenizer=identity, preprocessor=None, lowercase=False
        )),
        ('classifier', classifier)
    ])


def build_model(X, y, classifier):
    model = get_model(classifier)
    model.fit(X, y)
    return model

def build_and_eval(chat_log_file, model_path, classifier=None):
    if classifier is None:
        classifier = BernoulliNB()

    print("preprocessing corpus")
    X, y = load_corpus(chat_log_file)

    labels = LabelEncoder()
    y = labels.fit_transform(y)

    print("training test model")
    y_pred = cross_val_predict(get_model(classifier), X, y, cv=5)
    with open('data/y_pred.pkl', 'wb') as pred_file:
        pickle.dump(y_pred, pred_file)

    print(clsr(y, y_pred))

    print("training final model")
    model = build_model(X, y, classifier)
    model.labels_ = labels

    with open(model_path, 'wb') as model_file:
        pickle.dump(model, model_file)

    return model

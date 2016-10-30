import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import classification_report as clsr
from sklearn.model_selection import cross_val_predict
from sklearn.cross_validation import train_test_split as tts
import pickle
import os.path
from blotbot.message_preprocessor import NltkPreprocessor, create_vectorizer

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

def build(X, y, vectorizer, model):
    vectorizer.fit(X)
    X = vectorizer.transform(X, copy=True)
    return model.fit(X, y)

def build_and_eval(chat_log_file, model_path, classifier=None):
    if classifier is None:
        classifier = SGDClassifier()

    print("preprocessing corpus")
    X, y = load_corpus(chat_log_file)

    vectorizer = create_vectorizer()
    vectorizer.fit(X)
    X = vectorizer.transform(X, copy=False)

    labels = LabelEncoder()
    y = labels.fit_transform(y)

    print("training test model")
    y_pred = cross_val_predict(classifier, X, y, cv=5)
    with open('data/y_pred.pkl', 'wb') as pred_file:
        pickle.dump(y_pred, pred_file)

    print(clsr(y, y_pred))

    print("training final model")
    model = classifier.fit(X, y)
    model.labels_ = labels

    with open(model_path, 'wb') as model_file:
        pickle.dump(model, model_file)

    return model

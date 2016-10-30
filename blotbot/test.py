from blotbot.twitch_client import TwitchClient
import yaml
import pickle

def main():
    with open('config.yaml', 'r') as config_stream:
        config = yaml.load(config_stream)

    with open('data/model.pkl', 'rb') as classifier_file:
        classifier = pickle.load(classifier_file)

    client = TwitchClient(config, classifier)
    client.connect()
    client.start()

if __name__ == "__main__":
    main()

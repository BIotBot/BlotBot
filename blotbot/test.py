from twitch_client import TwitchClient
import yaml

def main():
    with open('config.yaml', 'r') as config_stream:
        config = yaml.load(config_stream)

    client = TwitchClient(config)
    client.connect()
    client.start()

if __name__ == "__main__":
    main()

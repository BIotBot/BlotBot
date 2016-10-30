import socket
import time
import re
import pickle
from blotbot.message_preprocessor import NltkPreprocessor, create_vectorizer
from blotbot.sentiment_training import build, load_corpus

pattern_chat = re.compile(r"^:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :")

prefix_notice = "@msg-id"
pattern_ban = re.compile(r"^@msg-id=ban_success :tmi\.twitch\.tv NOTICE #\w+ :([^ ]+) is now banned from this room")
pattern_timeout = re.compile(r"^@msg-id=ban_success :tmi\.twitch\.tv NOTICE #\w+ :([^ ]+) has been timed out for \d+ seconds.")

class TwitchClient:
    def __init__(self, config, classifier):
        self.config = config
        self.classifier = classifier
        self.preprocessor = NltkPreprocessor()
        with open('data/dota2_chat_log.csv.pkl', 'rb') as corpus_file:
            self.X, self.y = pickle.load(corpus_file)
        self.vectorizer = create_vectorizer(partial=True)
        self.vectorizer.fit(self.X)
        self.last_rebuild = time.time()
        self.dirty_corpus = True
        self.user_msg_buffer = {}
        self.flagged_users = set()

    def get_user_msgs(self, user):
        msgs = self.user_msg_buffer.get(user)

        if msgs is None:
            msgs = []
            self.user_msg_buffer[user] = msgs
        return msgs

    def add_user_msg(self, user, msg):
        msgs = self.get_user_msgs(user)
        if len(msgs) > self.user_msg_history_len:
            msgs.remove(msgs[0])
        msgs.append(msg)

    @property
    def user_msg_history_len(self):
        return self.config.get('user_msg_history_len', 3)

    @property
    def host(self):
        return self.config.get('host')

    @property
    def port(self):
        return self.config.get('port')

    @property
    def oauth(self):
        return self.config.get('oauth')

    @property
    def nick(self):
        return self.config.get('nick')

    @property
    def channel(self):
        return self.config.get('channel')

    @property
    def msg_rate(self):
        return self.config.get('msg_rate', 30.0/19.0)

    @property
    def timeout(self):
        return self.config.get('timeout', 120)

    def connect(self):
        self.socket = socket.socket()
        self.socket.connect((self.host, self.port))
        self.send("PASS oauth:{}\r\n".format(self.oauth).encode("utf-8"))
        self.send("NICK {}\r\n".format(self.nick).encode("utf-8"))
        self.send("JOIN #{}\r\n".format(self.channel).encode("utf-8"))
        self.send("CAP REQ :twitch.tv/commands".encode("utf-8"))

    def start(self):
        self.alive = True

        while self.alive:
            response = self.socket.recv(1024).decode("utf-8")
            responses = response.split('\n')
            for res in responses:
                self.handle_response(res)
            if self.dirty_corpus and (time.time() - self.last_rebuild > 15):
                self.rebuild_model()
            time.sleep(1.0 / self.msg_rate)

    def handle_response(self, response):
        print(response)
        # answer server pings
        if response == "PING :tmi.twitch.tv\r\n":
            self.socket.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
        elif response.startswith(prefix_notice):
            match = pattern_ban.search(response)
            if match is None:
                match = pattern_timeout.search(response)
            if match is not None:
                print("user " + username + " was banned")
                username = response.group(1)
                if username not in self.flagged_users:
                    user_msgs = self.get_user_msgs(username)
                    user_msgs = self.preprocessor.transform(user_msgs)
                    self.X.extend(user_msgs)
                    self.y.extend([True for _ in user_msgs])
                    self.flagged_users.discard(username)
                    self.dirty_corpus = True
        else:
            username = re.search(r"\w+", response)
            if username is not None:
                username = username.group(0) # return the entire match
                msg = pattern_chat.sub("", response)
                msg_cls = self.classify_message(msg)
                if msg_cls == 1:
                    print(username + " | " + msg)
                    self.flagged_users.add(username)
                    self.send_timeout(username)
                self.add_user_msg(username, msg)

    def classify_message(self, msg):
        msg_data = self.preprocessor.transform([msg])
        msg_data = self.vectorizer.transform(msg_data)
        msg_cls = self.classifier.predict(msg_data)[0]
        return msg_cls

    def rebuild_model(self):
        print("rebuilding model")
        self.classifier = build(self.X, self.y, self.vectorizer, self.classifier)
        self.last_rebuild = time.time()
        self.dirty_corpus = False

    def send(self, msg):
        print(msg)
        self.socket.send(msg)

    def send_chat(self, msg):
       self.send("PRIVMSG #{} :{}".format(self.channel, msg).encode("utf-8"))

    def send_ban(self, user):
        self.send_chat("/ban {}".format(user))

    def send_timeout(self, user, secs=-1):
        if secs == -1:
            secs = self.timeout

        self.send_chat("/timeout {} {}".format(user, secs))

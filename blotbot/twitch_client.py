import socket
import time
import re

pattern_chat = re.compile(r"^:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :")

class TwitchClient:
    def __init__(self, config):
        self.config = config

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

    def connect(self):
        self.socket = socket.socket()
        self.socket.connect((self.host, self.port))
        self.send("PASS oauth:{}\r\n".format(self.oauth).encode("utf-8"))
        self.send("NICK {}\r\n".format(self.nick).encode("utf-8"))
        self.send("JOIN #{}\r\n".format(self.channel).encode("utf-8"))

    def start(self):
        self.alive = True

        while self.alive:
            response = self.socket.recv(1024).decode("utf-8")
            responses = response.split('\n')
            for res in responses:
                self.handle_response(res)
            time.sleep(1.0 / self.msg_rate)

    def handle_response(self, response):
        # print(response) # TODO(coalman): replace or configure echo

        # answer server pings
        if response == "PING :tmi.twitch.tv\r\n":
            self.socket.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
        else:
            username = re.search(r"\w+", response)
            if username is not None:
                username = username.group(0) # return the entire match
                message = pattern_chat.sub("", response)
                print(username + ": " + message)

    def send(self, msg):
        self.socket.send(msg)

    def send_chat(self, msg):
       self.send("PRIVMSG #{}: {}".format(self.channel, msg))

    def send_ban(self, user):
        self.send_chat(".ban {}".format(user))

    def send_timeout(self, user, secs=-1):
        if secs == -1:
            secs = self.config["timeout"]

        self.send_chat(".timeout {}".format(user, secs))

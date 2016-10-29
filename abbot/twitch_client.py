class TwitchClient:
    def send_chat(self, msg):
        channel = self.config["channel"]
        self.socket.send("PRIVMSG #{} :{}".format(channel, msg))

    def send_ban(self, user):
        self.send_chat(".ban {}".format(user))

    def send_timeout(self, user, secs=-1):
        if secs == -1:
            secs = self.config["timeout"]

        self.send_chat(".timeout {}".format(user, secs))

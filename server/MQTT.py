from Message import *
import queue
import logging


class MQTT:
    """Class containing methods for MQTT processes"""

    topics = []
    subscribers = {}
    sub_list = []
    publishers = {}
    pub_list = []

    send_q = None

    def __init__(self, send_q):
        self.send_q = send_q

    def process_msg(self, msg):
        """Process received message"""
        fr = Frame(msg)
        hd = fr.header.lower()
        frame = None

        if hd == "error" or hd == "base":
            return 0
        if hd == "connect":
            frame = ConnectFrame(msg)
        elif hd == "pub":
            frame = PublishFrame(msg)
        elif hd == "sub":
            frame = SubscribeFrame(msg)
        elif hd == "unsub":
            frame = UnsubscribeFrame(msg)
        elif hd == "disconnect":
            frame = DisconnectFrame(msg)
        else:
            return 0

        return 0 if frame.header == "error" else frame

    def process_connect(self, sock):
        """Respond to a connection"""

        self.send_q.put((sock, AckFrame().compose("connack").encode()))

    def process_data(self, sock, frame):
        """Process a publish frame"""

        self.add_topic(frame.topic)
        self.add_pub(sock, frame.topic)

        self.broadcast_data(frame)

    def process_sub(self, sock, frame):
        """Process a Subscribe frame"""
        resp = []
        for topic in frame.topics:
            self.add_topic(topic)
            if self.add_sub(sock, topic):
                resp.append(1)
            else:
                resp.append(0)

        self.send_q.put((sock, AckFrame().compose("suback", resp).encode()))

    def process_unsub(self, sock, frame):
        """Process an Unsubscribe frame"""
        for topic in frame.topics:
            self.rem_sub(sock, topic)
            self.rem_topic(topic)
            self.update_pub_sub()

        self.send_q.put((sock, AckFrame().compose("unsuback").encode()))

    def process_disc(self, sock):
        """Process a Disconnect frame"""
        for topic in self.topics:
            self.rem_pub(sock, topic)
            self.rem_sub(sock, topic)

        topics_bk = self.topics.copy()

        for topic in topics_bk:
            self.rem_topic(topic)

        self.update_pub_sub()

    def broadcast_data(self, frame):
        """Broadcast data to subscribers"""
        for sock in self.subscribers[frame.topic]:
            self.send_q.put((sock, frame.encode()))

    def add_topic(self, topic):
        """Handle adding a topic"""
        if not topic in self.topics:
            self.topics.append(topic)
            self.publishers[topic] = []
            self.subscribers[topic] = []

    def rem_topic(self, topic):
        """Handle removing a topic"""
        if (
            topic in self.topics
            and not self.publishers[topic]
            and not self.subscribers[topic]
        ):
            self.topics.remove(topic)
            del self.publishers[topic]
            del self.subscribers[topic]

    def add_sub(self, sock, topic):
        """Add subscriber to given topic"""
        if sock in self.subscribers[topic]:
            # logging.info("Already Subscribed")
            return 0

        self.subscribers[topic].append(sock)
        fr_info = sock.getpeername()
        self.sub_list.append(f"{fr_info[0]}, {fr_info[1]}, {topic}")

        return 1
        # logging.info("Subscribing")

    def rem_sub(self, sock, topic=None):
        """Remove subscriber from given topic"""
        if not topic is None:
            if topic in self.subscribers:
                if sock in self.subscribers[topic]:
                    self.subscribers[topic].remove(sock)

    def add_pub(self, sock, topic):
        """Add publisher to given topic"""
        if sock in self.publishers[topic]:
            # logging.info("Publisher already known")
            return

        self.publishers[topic].append(sock)
        fr_info = sock.getpeername()
        self.pub_list.append(f"{fr_info[0]}, {fr_info[1]}, {topic}")

    def rem_pub(self, sock, topic=None):
        """Remove publisher from given topic"""
        if not sock is None:
            if topic in self.publishers:
                if sock in self.publishers[topic]:
                    self.publishers[topic].remove(sock)

    def update_pub_sub(self):
        pubs = []
        subs = []
        for topic in self.topics:
            pubs += [self.update_helper(x, topic) for x in self.publishers[topic]]
            subs += [self.update_helper(x, topic) for x in self.subscribers[topic]]

        pub_list = self.pub_list.copy()
        for sock in pub_list:
            if not sock in pubs:
                self.pub_list.remove(sock)

        sub_list = self.sub_list.copy()
        for sock in sub_list:
            if not sock in subs:
                self.sub_list.remove(sock)

    def update_helper(self, sock, topic):
        try:
            fr_info = sock.getpeername()
            return f"{fr_info[0]}, {fr_info[1]}, {topic}"
        except OSError:
            pass

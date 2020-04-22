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
        elif hd == "disc":
            frame = DisconnectFrame(Frame)
        else:
            return 0

        return 0 if frame.header == "error" else frame

    def process_connect(self, sock):
        """Respond to a connection"""

        self.send_q.put((sock, AckFrame().compose("connack").encode()))

    def process_data(self, sock, frame):
        """Process a publish frame"""

        # check if the topic exists yet
        if not frame.topic in self.topics:
            # if not, create it and add the sender to the publisher list
            self.add_topic(frame.topic)
        if not sock in self.publishers[frame.topic]:
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

        self.send_q.put((sock, AckFrame().compose("unsuback").encode()))

    def process_disc(self, sock, frame):
        """Process a Disconnect frame"""
        for topic in self.topics:
            if sock in self.publishers[topic]:
                self.publishers[topic].remove(sock)
            if sock in self.subscribers[topic]:
                self.subscribers[topic].remove(sock)
            self.rem_topic(topic)


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
        if (topic in self.topics and not \
            self.publishers[topic] and not \
            self.subscribers[topic]
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
        self.sub_list.append(sock.getpeername())
        return 1
        # logging.info("Subscribing")


    def rem_sub(self, sock, topic):
        """Remove subscriber from given topic"""
        if sock in self.subscribers[topic]:
            self.subscribers[topic].remove(sock)


    def add_pub(self, sock, topic):
        """Add publisher to given topic"""
        if sock in self.publishers[topic]:
            # logging.info("Publisher already known")
            return

        self.publishers[topic].append(sock)
        self.pub_list.append(sock.getpeername())


    def rem_pub(self, sock, topic):
        """Remove publisher from given topic"""
        if sock in self.publishers[topic]:
            self.publishers[topic].remove(topic)

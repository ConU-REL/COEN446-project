from Message import *
import queue
import logging


class MQTT:
    """Class containing methods for MQTT processes"""

    # data storage
    topics = []
    subscribers = {}
    sub_list = []
    publishers = {}
    pub_list = []

    # send queue
    send_q = None

    def __init__(self, send_q):
        self.send_q = send_q

    def process_msg(self, msg):
        """Process received message"""
        # create frame
        fr = Frame(msg)
        hd = fr.header.lower()
        frame = None

        # check frame type
        if hd == "error" or hd == "base":
            # exit if bad
            return 0
        if hd == "connect":
            # process frame
            frame = ConnectFrame(msg)
        elif hd == "pub":
            # process frame
            frame = PublishFrame(msg)
        elif hd == "sub":
            # process frame
            frame = SubscribeFrame(msg)
        elif hd == "unsub":
            # process frame
            frame = UnsubscribeFrame(msg)
        elif hd == "disconnect":
            # process frame
            frame = DisconnectFrame(msg)
        else:
            return 0

        return 0 if frame.header == "error" else frame

    def process_connect(self, sock):
        """Respond to a connection"""

        # send connack
        self.send_q.put((sock, AckFrame().compose("connack").encode()))

    def process_data(self, sock, frame):
        """Process a publish frame"""
        # add info from pub frame
        self.add_topic(frame.topic)
        self.add_pub(sock, frame.topic)

        # rebroadcast to subscribers
        self.broadcast_data(frame)

    def process_sub(self, sock, frame):
        """Process a Subscribe frame"""
        resp = []
        # try to subscribe the client
        for topic in frame.topics:
            self.add_topic(topic)
            if self.add_sub(sock, topic):
                resp.append(1)
            else:
                resp.append(0)

        # send ACK with list of returns
        self.send_q.put((sock, AckFrame().compose("suback", resp).encode()))

    def process_unsub(self, sock, frame):
        """Process an Unsubscribe frame"""
        # try to unsub the client
        for topic in frame.topics:
            self.rem_sub(sock, topic)
            self.rem_topic(topic)
            self.update_pub_sub()

        # send ACK
        self.send_q.put((sock, AckFrame().compose("unsuback").encode()))

    def process_disc(self, sock):
        """Process a Disconnect frame"""
        # remove client from subs and pubs
        for topic in self.topics:
            self.rem_pub(sock, topic)
            self.rem_sub(sock, topic)

        # make backup of topics since we're working on it
        topics_bk = self.topics.copy()

        # remove topic from list if nobody is susbcribed to it
        for topic in topics_bk:
            self.rem_topic(topic)

        # update human-readable lists
        self.update_pub_sub()

    def broadcast_data(self, frame):
        """Broadcast data to subscribers"""
        # rebroadcast to all subscribers
        for sock in self.subscribers[frame.topic]:
            # send data
            self.send_q.put((sock, frame.encode()))

    def add_topic(self, topic):
        """Handle adding a topic"""
        # if topic doesn't exist, add it
        if not topic in self.topics:
            self.topics.append(topic)
            self.publishers[topic] = []
            self.subscribers[topic] = []

    def rem_topic(self, topic):
        """Handle removing a topic"""
        # if no more pubs or subs for a topic, remove it
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
        # exit if already subbed
        if sock in self.subscribers[topic]:
            return 0

        # add sub
        self.subscribers[topic].append(sock)
        # add human-readable
        fr_info = sock.getpeername()
        self.sub_list.append(f"{fr_info[0]}, {fr_info[1]}, {topic}")

        return 1

    def rem_sub(self, sock, topic=None):
        """Remove subscriber from given topic"""
        # remove sub
        if not topic is None:
            if topic in self.subscribers:
                if sock in self.subscribers[topic]:
                    self.subscribers[topic].remove(sock)

    def add_pub(self, sock, topic):
        """Add publisher to given topic"""
        # if already a pub, exit
        if sock in self.publishers[topic]:
            return

        # add pub
        self.publishers[topic].append(sock)
        # add human-readable
        fr_info = sock.getpeername()
        self.pub_list.append(f"{fr_info[0]}, {fr_info[1]}, {topic}")

    def rem_pub(self, sock, topic=None):
        """Remove publisher from given topic"""
        # remove pub
        if not sock is None:
            if topic in self.publishers:
                if sock in self.publishers[topic]:
                    self.publishers[topic].remove(sock)

    def update_pub_sub(self):
        """Update the Human-Readable lists of pubs and subs"""

        # store good pubs and subs
        pubs = []
        subs = []

        # find good pubs and subs
        for topic in self.topics:
            pubs += [self.update_helper(x, topic) for x in self.publishers[topic]]
            subs += [self.update_helper(x, topic) for x in self.subscribers[topic]]

        # make copy of list since we're working on it
        pub_list = self.pub_list.copy()
        for sock in pub_list:
            # remove bad pubs from list
            if not sock in pubs:
                self.pub_list.remove(sock)

        # make copy of list since we're working on it
        sub_list = self.sub_list.copy()
        for sock in sub_list:
            # remove bad subs from list
            if not sock in subs:
                self.sub_list.remove(sock)

    def update_helper(self, sock, topic):
        """Helper to format human-readable pubs and subs"""
        try:
            fr_info = sock.getpeername()
            return f"{fr_info[0]}, {fr_info[1]}, {topic}"
        except OSError:
            pass

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
        header, content = msg.split(" ... ", 1)
        msg = [header, content]
        frame_type = Frame.frame_types[header.lower()]

        if frame_type == 1:
            frame = ConnectFrame(msg)
            return 0 if not frame else frame
        elif frame_type == 3:
            frame = DiscFrame(msg)
            return 0 if not frame else frame
        elif frame_type == 4:
            frame = DataFrame(msg)
            return 0 if not frame else frame

    def process_data(self, sock, frame):
        """Process a data frame"""

        # check if the topic exists yet
        if not frame.topic in self.topics:
            # if not, create it and add the sender to the publisher list
            self.add_topic(frame.topic)
            self.add_pub(sock, frame.topic)

        self.broadcast_data(frame)

    def process_conn(self, sock, frame):
        """Process a connect frame"""

        # check if topic exists
        if not frame.topic in self.topics:
            self.add_topic(frame.topic)
            
        # if subscriber
        if not frame.conn_type:
            self.add_sub(sock, frame.topic)

    def broadcast_data(self, frame):
        """Broadcast data to subscribers"""
        for sock in self.subscribers[frame.topic]:
            self.send_q.put((sock, frame))

    def add_topic(self, topic):
        self.topics.append(topic)
        self.publishers[topic] = []
        self.subscribers[topic] = []

    def rem_topic(self, topic):
        pass

    def add_sub(self, sock, topic):
        """Add subscriber to given topic"""

        if sock in self.subscribers[topic]:
            logging.info("already subscribed")
            return

        self.subscribers[topic].append(sock)
        self.sub_list.append(sock.getpeername())
        logging.info("subscribing")


    def rem_sub(self, sock, topic):
        """Remove subscriber from given topic"""
        pass

    def add_pub(self, sock, topic):
        """Add publisher to given topic"""

        if sock in self.publishers[topic]:
            logging.info("already published")
            return

        self.publishers[topic].append(sock)
        self.pub_list.append(sock.getpeername())


    def rem_pub(self, sock, topic):
        """Remove publisher from given topic"""
        pass

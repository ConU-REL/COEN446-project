from Message import *
import queue


class MQTT:
    """Class containing methods for MQTT processes"""

    topics = []
    subscribers = {}
    publishers = {}

    send_q = None

    def __init__(self, send_q):
        self.send_q = send_q

    def process_msg(self, msg):
        """Process received message"""
        header, content = msg.split(" ... ", 1)
        msg = [header, content]
        frame_type = Frame.frame_types[header.lower()]

        if frame_type == 1:
            return ConnectFrame(msg)
        elif frame_type == 3:
            return DiscFrame(msg)
        elif frame_type == 4:
            return DataFrame(msg)

    def process_data(self, sock, frame):
        """Process a data frame"""

        # check if the topic exists yet
        if not frame.topic in self.topics:
            # if not, create it and add the sender to the publisher list
            self.add_topic(frame.topic)
            self.add_pub(sock, frame.topic)

        self.broadcast_data(frame)

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
        pass

    def rem_sub(self, sock, topic):
        """Remove subscriber from given topic"""
        pass

    def add_pub(self, sock, topic):
        """Add publisher to given topic"""
        self.publishers[topic].append(sock)

    def rem_pub(self, sock, topic):
        """Remove publisher from given topic"""
        pass

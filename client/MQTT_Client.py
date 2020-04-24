"""
    This module should handle all MQTT Client functionality including:
        - Connecting to a server
            - All related socket tasks
            - Connection acknowledgement
        - Publishing data
        - Subscribing/receiving data
        - Unsubscribing
        - Disconnecting
"""

import Message
import socket
import logging
import threading
import queue
import tcp_client
import json


class MQTT_Client:
    """MQTT Client Class, handles all MQTT client tasks"""

    # socket connected?
    connected = False
    # connection ACKed?
    connack_rec = False

    # flag to kill tcp thread
    stop_thread = False

    # list of subscribed topics
    topics = []

    # requested subscriptions
    sub_req = []
    # requested unsubscriptions
    unsub_req = []

    # queues for TCP thread
    recv_q = queue.Queue()
    send_q = queue.Queue()

    def __init__(self, ip="localhost", port=8888, timeout=3):
        # set connection params
        self.srv_ip = ip
        self.srv_port = port
        self.srv_timeout = timeout

        # the socket
        self.socket = None
        # tcp thread obj
        self.tcp_thread = None

    def is_connected(self):
        """Returns whether connected and ACKed"""
        if self.connected and self.connack_rec:
            return 1
        return 0

    def connect(self, out_q):
        """Connect to MQTT broker"""
        # received message queue
        self.out_q = out_q
        # try to start the socket
        try:
            # create the socket
            self.sock = socket.create_connection(
                (self.srv_ip, self.srv_port), self.srv_timeout
            )
            # set socket to non blocking
            self.sock.setblocking(0)
            # send the connect frame
            self.send_q.put(Message.ConnectFrame().encode())

            # update connected flag
            self.connected = True
        except ConnectionRefusedError:
            # if connection failed, exit with error
            return 1

        # create the TCP thread
        self.tcp_thread = threading.Thread(
            target=tcp_client.client_thread,
            daemon=False,
            args=(lambda: self.stop_thread, self.sock, self.recv_q, self.send_q,),
        )

        # create the message processing thread
        self.process_thread = threading.Thread(target=self.process_inc, daemon=True,)

        # start the threads if they aren't started
        if not self.tcp_thread.isAlive():
            # reset quit flag before starting
            self.stop_thread = False
            self.tcp_thread.start()
        if not self.process_thread.isAlive():
            self.process_thread.start()
        return 0

    def disconnect(self,):
        """Disconnect from MQTT broker"""
        # check if connection ACKed
        if self.connack_rec:
            # if ACKed, disconnect
            self.send_q.put(Message.DisconnectFrame().encode())

        # if connected, disconnect
        if self.connected:
            # kill the TCP thread
            self.stop_thread = True
            self.tcp_thread.join()

            # close the socket
            self.sock.close()

            # reset flags and subscriptions
            self.connack_rec = False
            self.connected = False
            self.topics = []
            self.sub_req = 0
            self.unsub_req = 0
        else:
            return False

    def subscribe(self, topics=None):
        """Subscribe to topic(s)"""
        # check if ACKed
        if not self.connack_rec:
            return 1
        # if no topics, exit
        if topics == None:
            return 1

        # check if topic is list or string
        if isinstance(topics, list):
            # check if we're already subscribed to any of the requested topics
            for topic in topics:
                if topic in self.topics:
                    # remove from req if we are subbed already
                    topics.remove(topic)
        elif isinstance(topics, str):
            # don't sub if already subbed
            if topics in self.topics:
                return
            topics = [topics]
        # store the request
        self.sub_req = topics
        # compose message
        msg = {"header": "SUB", "topics": topics}
        # create frame
        frame = Message.SubscribeFrame(json.dumps(msg))
        # send frame
        self.send_q.put(frame.encode())

    def unsubscribe(self, topics=None):
        """Unsubscribe from topic(s)"""
        # check if ACKed
        if not self.connack_rec:
            return 1
        # if no topics passed, return
        if topics == None:
            return 1
        # only unsub from stuff we're subbed to
        for topic in topics:
            if not topic in self.topics:
                topics.remove(topic)
        # if nothing, return
        if not topics:
            return
        self.unsub_req = topics
        # compose frame
        frame = Message.UnsubscribeFrame(topics=topics)
        # send frame
        self.send_q.put(frame.encode())

    def publish(self, topic, content):
        """Publish data to Broker"""
        # check if ACKed
        if not self.connack_rec:
            return 1

        # compose frame
        frame = Message.PublishFrame().compose(topic, content)

        # send frame
        self.send_q.put(frame.encode())

    def process_inc(self):
        """Process incoming messages (threaded)"""
        while True:
            # if connected
            if self.connected:
                # if socket is closed, reset
                if self.sock._closed:
                    self.connack_rec = 0
                    self.disconnect()
            # try to get a message from queue
            try:
                msg = self.recv_q.get_nowait()
                # convert from bytes to string
                msg = msg.decode("utf-8")
                # analyze frame
                frame = Message.Frame(msg)

                # check frame type
                hd = frame.header.lower()

                # check if frame is good, otherwise disregard it
                if hd == "error" or hd == "base":
                    pass
                # if ack frame
                elif hd == "ack":
                    # process it
                    self.process_ack(Message.AckFrame(msg))
                # if pub frame
                elif hd == "pub":
                    # process it
                    self.process_data(Message.PublishFrame(msg))

            except queue.Empty:
                # if no messages, do nothing
                pass

    def process_ack(self, frame):
        """Process ACK Frame"""
        # try to get the contents
        try:
            tp = frame.content.lower()
        except json.JSONDecodeError:
            return 1

        # if CONNACK frame
        if tp == "":
            self.connack_rec = True
        # if SUBACK frame
        elif tp == "sub":
            # get topic sub return values
            contents = frame.topics_return
            for sub in range(0, len(contents)):
                # update subscriptions
                if contents[sub]:
                    self.topics.append(self.sub_req[sub])
            # reset requested sub
            self.sub_req = []
        # if UNSUBACK frame
        elif tp == "unsub":
            # update subscriptions
            if self.unsub_req:
                for sub in self.unsub_req:
                    self.topics.remove(sub)
                # reset requested unsub
                self.unsub_req = []

    def process_data(self, frame):
        """ Process incoming data"""
        # add topic if not added
        if not frame.topic in self.topics:
            return
        # put data in output queue
        self.out_q.put([frame.topic, frame.content])

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

# from tcp_client import client_thread, stop


class MQTT_Client:
    """MQTT Client Class, handles all MQTT client tasks"""

    sock = None
    connected = False
    connack_rec = False

    stop_thread = False

    topics = []

    sub_req = []
    unsub_req = []

    recv_q = queue.Queue()
    send_q = queue.Queue()

    def __init__(self, ip="localhost", port=8888, timeout=3):
        self.srv_ip = ip
        self.srv_port = port
        self.srv_timeout = timeout

        self.socket = None
        self.tcp_thread = None

    def connect(self, out_q):
        self.out_q = out_q
        try:
            self.sock = socket.create_connection(
                (self.srv_ip, self.srv_port), self.srv_timeout
            )
            self.sock.setblocking(0)
            self.send_q.put(Message.ConnectFrame().encode())
            # self.sock.sendall()

            self.connected = True
        except ConnectionRefusedError:
            logging.info("connection error")
            return 1

        self.tcp_thread = threading.Thread(
            target=tcp_client.client_thread,
            daemon=False,
            args=(lambda: self.stop_thread, self.sock, self.recv_q, self.send_q,),
        )

        self.process_thread = threading.Thread(target=self.process_inc, daemon=True,)
        if not self.tcp_thread.isAlive():
            self.stop_thread = False
            self.tcp_thread.start()
        if not self.process_thread.isAlive():
            self.process_thread.start()
        return 0

    def disconnect(self,):
        if self.connack_rec:
            self.send_q.put(Message.DisconnectFrame().encode())
            # TODO: send disconnect frame here
            pass

        if self.connected:
            self.stop_thread = True
            self.tcp_thread.join()
            self.sock.close()

            self.connack_rec = False
            self.connected = False
            self.topics = []
            self.sub_req = 0
            self.unsub_req = 0
        else:
            return False

    def subscribe(self, topics=None):
        if not self.connack_rec:
            return 1
        if topics == None:
            return 1
        for topic in topics:
            if topic in self.topics:
                topics.remove(topic)
        if not topics:
            return
        self.sub_req = topics
        msg = {"header": "SUB", "topics": topics}
        frame = Message.SubscribeFrame(json.dumps(msg))

        self.send_q.put(frame.encode())

    def unsubscribe(self, topics=None):
        if not self.connack_rec:
            return 1
        if topics == None:
            return 1
        for topic in topics:
            if not topic in self.topics:
                topics.remove(topic)
        if not topics:
            return
        self.unsub_req = topics
        frame = Message.UnsubscribeFrame(topics=topics)
        self.send_q.put(frame.encode())

    def publish(self, topic, content):
        if not self.connack_rec:
            return 1
        
        frame = Message.PublishFrame().compose(topic, content)

        self.send_q.put(frame.encode())

    def process_inc(self):
        while True:
            if self.connected:
                if self.sock._closed:
                    self.connack_rec = 0
                    self.disconnect()
            try:
                msg = self.recv_q.get_nowait()
                msg = msg.decode("utf-8")
                frame = Message.Frame(msg)

                hd = frame.header.lower()

                if hd == "error" or hd == "base":
                    pass
                elif hd == "ack":
                    self.process_ack(Message.AckFrame(msg))
                elif hd == "pub":
                    self.process_data(Message.PublishFrame(msg))

            except queue.Empty:
                pass

    def process_ack(self, frame):
        try:
            tp = frame.content.lower()
        except json.JSONDecodeError:
            return 1

        if tp == "":
            self.connack_rec = True
        elif tp == "sub":
            contents = frame.topics_return
            for sub in range(0, len(contents)):
                if contents[sub]:
                    self.topics.append(self.sub_req[sub])
            self.sub_req = []
        elif tp == "unsub":
            if self.unsub_req:
                for sub in self.unsub_req:
                    self.topics.remove(sub)
                self.unsub_req = []

    def process_data(self, frame):
        if not frame.topic in self.topics:
            return
        
        self.out_q.put([frame.topic, frame.content])

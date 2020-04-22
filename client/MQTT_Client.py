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
    
    def __init__(self, ip="localhost", port=8888, timeout=3):
        self.srv_ip = ip
        self.srv_port = port
        self.srv_timeout = timeout

        self.socket = None
        self.tcp_thread = None

    def connect(self, recv_q, send_q):
        self.recv_q = recv_q
        self.send_q = send_q
        try:
            self.sock = socket.create_connection(
                (self.srv_ip, self.srv_port), self.srv_timeout
            )
            self.sock.setblocking(0)
            self.sock.sendall(Message.ConnectFrame().encode().encode("utf-8"))
            self.connected = True
        except ConnectionRefusedError:
            return 1

        self.tcp_thread = threading.Thread(
            target=tcp_client.client_thread,
            daemon=False,
            args=(lambda: self.stop_thread, self.sock, self.recv_q, self.send_q,),
        )

        self.process_thread = threading.Thread(
            target=self.process_inc,
            daemon=True,
        )
        
        self.tcp_thread.start()
        self.process_thread.start()
        return 0

    def disconnect(self,):
        if self.connack_rec:
            # TODO: send disconnect frame here
            pass

        if self.connected:
            self.stop_thread = True
            self.tcp_thread.join()
            while not self.sock._closed:
                pass
                return False
        else:
            return False

    def subscribe(self, topics=None):
        # if not self.connack_rec:
        #     return 1
        if topics == None:
            return 1
        
        msg = {"header":"SUB", "topics":topics}
        frame = Message.SubscribeFrame(json.dumps(msg))

        self.send_q.put(frame.encode())

    def unsubscribe(self,):
        if not self.connack_rec:
            return 1
        pass

    def publish(self,):
        if not self.connack_rec:
            return 1
        pass

    def process_inc(self):
        while True:
            try:
                msg = self.recv_q.get_nowait()
                msg = msg.decode("utf-8")
                frame = Message.Frame(msg)
                
                hd = frame.header.lower()
                logging.info(f"Message received: {hd}")

                if hd == "error" or hd == "base":
                    pass
                elif hd == "ack":
                    self.process_ack(Message.AckFrame(msg))
                elif hd == "data":
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
            pass
        elif tp == "unsub":
            pass

    def process_data(self, frame):
        pass
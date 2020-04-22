# Imports
import socket, sys
import queue, threading
import npyscreen
import json
import logging
from tcp_client import client_thread
from Message import *
from MQTT_Client import MQTT_Client

recv_q = queue.Queue()
send_q = queue.Queue()

mqtt = MQTT_Client()

class ClientApp(npyscreen.NPSAppManaged):
    def onStart(self):
        self.registerForm("MAIN", MainForm())


class MainForm(npyscreen.Form):
    OK_BUTTON_TEXT = "Exit"
    counter = 0

    def send_msg(self):
        return
        msg = {
            "header": "PUB",
            "topic": "test topic",
            "qos": 0,
            "retain": 0,
            "content": "test content",
        }
        msg = PublishFrame(json.dumps(msg))
        try:
            self.counter += 1
        except ConnectionResetError:
            self.conn.value = "Disconnected"
            self.btn_conn.name = "Connect"
            self.btn_conn.whenPressed = self.connect
            self.display()
        except AttributeError:
            pass

    def subscribe(self):
        mqtt.subscribe(["test"])

    def connect(self):
        self.conn.value = "Connecting"
        self.conn.display()
        conn = mqtt.connect(recv_q, send_q)
        if conn == 0:
            self.conn.value = "Connected"
            self.btn_conn.name = "Disconnect"
            self.btn_conn.whenPressed = self.disconnect
        elif conn == 1:
            self.conn.value = "Timed Out"

        self.conn.display()

    def disconnect(self):
        conn = mqtt.disconnect()
        if not conn:
            self.conn.value = "Disconnected"
            self.btn_conn.name = "Connect"
            self.btn_conn.whenPressed = self.connect
        else:
            # potential error case here?
            pass

        self.display()

    def while_waiting(self):
        pass

    def update_log(self, msg=None):
        # max number of recent messages we want to see
        self.max_size = 10
        # if we're at max capacity, delete the oldest message from the log
        if len(self.recv_log.values) >= self.max_size:
            self.recv_log.values.pop()

        self.recv_log.values = [json.loads(msg)["header"]] + self.recv_log.values
        # refresh the display

        self.display()

    def create(self):
        self.keypress_timeout = 1

        self.conn = self.add(
            npyscreen.TitleText, name="Connection", editable=False, relx=2, rely=1
        )
        self.conn.value = "Disconnected"

        self.topic = self.add(npyscreen.TitleText, name="Topic")
        self.nextrely += 1

        self.recv_log = self.add(
            npyscreen.BoxTitle,
            name="Received Message Log",
            editable=False,
            relx=2,
            rely=3,
            max_height=10,
        )

        self.topics_log = self.add(
            npyscreen.BoxTitle,
            name="Topics",
            editable=False,
            relx=2,
            rely=13,
            max_height=8,
            max_width=int(self.recv_log.width / 3),
        )

        self.sub_log = self.add(
            npyscreen.BoxTitle,
            name="Subscriptions",
            editable=False,
            relx=self.topics_log.max_width + 2,
            rely=13,
            max_height=8,
            max_width=int(self.recv_log.width / 3),
        )

        self.btn_conn = self.add(
            npyscreen.ButtonPress,
            name="Connect",
            relx=self.sub_log.relx + self.sub_log.max_width,
            rely=13,
        )

        self.btn_sub = self.add(
            npyscreen.ButtonPress,
            name="Subscribe",
            relx=self.btn_conn.relx,
            rely=self.btn_conn.rely + 2,
        )

        self.btn_unsub = self.add(
            npyscreen.ButtonPress,
            name="Unsubscribe",
            relx=self.btn_conn.relx,
            rely=self.btn_sub.rely + 1,
        )

        self.btn_send = self.add(
            npyscreen.ButtonPress,
            name="Send Message",
            relx=self.btn_conn.relx,
            rely=self.btn_unsub.rely + 2,
        )

        self.btn_conn.whenPressed = self.connect
        self.btn_send.whenPressed = self.send_msg
        self.btn_sub.whenPressed = self.subscribe

    def afterEditing(self):
        mqtt.disconnect()
        self.parentApp.setNextForm(None)


if __name__ == "__main__":
    TA = ClientApp()
    TA.run()
    # main()

# Imports
import socket, sys
import npyscreen
import json


class ClientApp(npyscreen.NPSAppManaged):
    def onStart(self):
        self.registerForm("MAIN", MainForm())


class MainForm(npyscreen.Form):
    OK_BUTTON_TEXT = "Exit"
    counter = 0
    sock = None

    def send_msg(self):
        msg = {
            "header": "PUB",
            "topic": "test topic",
            "qos": 0,
            "retain": 0,
            "content": "test content",
        }
        msg = json.dumps(msg)
        try:
            self.sock.sendall(msg.encode("utf-8"))
            self.counter += 1
        except ConnectionResetError:
            self.conn.value = "Disconnected"
            self.btn_conn.name = "Connect"
            self.btn_conn.whenPressed = self.connect
            self.display()
        except AttributeError:
            pass

    def subscribe(self):
        msg = {
            "header":"SUB",
            "topics":["test topic"]
        }
        msg = json.dumps(msg)

        try:
            self.sock.sendall(msg.encode("utf-8"))
            self.counter += 1
        except ConnectionResetError:
            self.conn.value = "Disconnected"
            self.btn_conn.name = "Connect"
            self.btn_conn.whenPressed = self.connect
            self.display()
        except AttributeError:
            pass

    def connect(self):
        try:
            self.conn.value = "Connecting"
            self.conn.display()

            self.sock = socket.create_connection(("localhost", 8888), 3)
        except ConnectionRefusedError:
            self.conn.value = "Timed Out"
            self.conn.display()
        else:
            self.conn.value = "Connected"
            self.btn_conn.name = "Disconnect"
            self.btn_conn.whenPressed = self.disconnect
            self.btn_conn.update(True)
            self.display()

    def disconnect(self):
        self.sock.close()
        self.conn.value = "Disconnected"
        self.btn_conn.name = "Connect"
        self.btn_conn.whenPressed = self.connect

        self.display()

    def create(self):
        self.conn = self.add(
            npyscreen.TitleText,
            name="Connection",
            editable=False,
            relx = 2,
            rely = 1
        )
        self.conn.value = "Disconnected"

        self.topic = self.add(npyscreen.TitleText, name="Topic")
        self.nextrely += 1

        self.recv_log = self.add(
            npyscreen.BoxTitle,
            name="Received Message Log",
            editable=False,
            relx = 2,
            rely = 3,
            max_height = 10,
        )

        self.topics_log = self.add(
            npyscreen.BoxTitle,
            name="Topics",
            editable=False,
            relx = 2,
            rely = 13,
            max_height = 8,
            max_width = int(self.recv_log.width/3)
        )

        self.sub_log = self.add(
            npyscreen.BoxTitle,
            name="Subscriptions",
            editable=False,
            relx = self.topics_log.max_width+2,
            rely = 13,
            max_height = 8,
            max_width = int(self.recv_log.width/3)
        )
        
        self.btn_conn = self.add(
            npyscreen.ButtonPress,
            name="Connect",
            relx = self.sub_log.relx + self.sub_log.max_width,
            rely = 13
        )
        
        btn_send = self.add(
            npyscreen.ButtonPress,
            name="Send Message",
            relx = self.sub_log.relx + self.sub_log.max_width,
            rely = 14
        )

        btn_sub = self.add(
            npyscreen.ButtonPress,
            name="Subscribe",
            relx = self.sub_log.relx + self.sub_log.max_width,
            rely = 15
        )


        self.btn_conn.whenPressed = self.connect
        btn_send.whenPressed = self.send_msg
        btn_sub.whenPressed = self.subscribe


    def afterEditing(self):
        self.parentApp.setNextForm(None)


if __name__ == "__main__":
    TA = ClientApp()
    TA.run()
    # main()

# Imports
import socket, sys
import npyscreen


class ClientApp(npyscreen.NPSAppManaged):
    def onStart(self):
        self.registerForm("MAIN", MainForm())


class MainForm(npyscreen.Form):
    OK_BUTTON_TEXT = "Exit"
    counter = 0
    sock = None

    def send_msg(self):
        msg = f"DATA ... {self.topic.value} ... test data {self.counter}"
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
        msg = f"CONNECT ... SUBSCRIBE ... {self.topic.value}"
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
            npyscreen.TitleText, name="Connection", editable=False
        )
        self.conn.value = "Disconnected"

        self.topic = self.add(npyscreen.TitleText, name="Topic")
        self.nextrely += 1

        self.btn_conn = self.add(npyscreen.ButtonPress, name="Connect")
        self.btn_conn.whenPressed = self.connect
        self.nextrely -= 1
        self.nextrelx += 15

        btn_send = self.add(npyscreen.ButtonPress, name="Send Message")
        btn_send.whenPressed = self.send_msg

        btn_sub = self.add(npyscreen.ButtonPress, name="Subscribe")
        btn_sub.whenPressed = self.subscribe

        

    def afterEditing(self):
        self.parentApp.setNextForm(None)


if __name__ == "__main__":
    TA = ClientApp()
    TA.run()
    # main()

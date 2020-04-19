# Imports
import socket, sys
import npyscreen

# create socket
sock = socket.create_connection(("localhost", 8888))

msg = b"test message"


class ClientApp(npyscreen.NPSAppManaged):
    def onStart(self):
        self.registerForm("MAIN", MainForm())


class MainForm(npyscreen.Form):
    def send_msg(self):
        sock.sendall(msg)

    def create(self):
        btn_send = npyscreen.ButtonPress
        btn_send.whenPressed = self.send_msg
        self.add(btn_send, name="Send Message")

    def afterEditing(self):
        self.parentApp.setNextForm(None)


if __name__ == "__main__":
    TA = ClientApp()
    TA.run()
    # main()


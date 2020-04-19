# Imports
import npyscreen
import logging
import threading
import queue

from tcp_server import server_thread

conn_q = {}
send_q = {}


class ServerApp(npyscreen.NPSAppManaged):
    tcp_thread = threading.Thread(target=server_thread, \
        daemon=True, args=(conn_q, send_q,))

    def onStart(self):
        self.value = None
        self.tcp_thread.start()
        logging.info("Thread Started")
        self.addForm("MAIN", MainForm)


class MainForm(npyscreen.Form):
    OK_BUTTON_TEXT = "Exit"


    def create(self):
        self.keypress_timeout = 1
        self.add(npyscreen.TitleText, name="Received Message Log")
        self.recv_log = self.add(npyscreen.Pager, name="Received Message Log")
        self.recv_log.display()

        # btn_ = npyscreen.ButtonPress
        # btn_send.whenPressed = self.send_msg
        # self.add(btn_send, name="Send Message")


    def update_log(self, msg=None):
        self.max_size = 10
        if(len(self.recv_log.values) >= self.max_size):
            self.recv_log.values.pop()
        self.recv_log.values = [msg] + self.recv_log.values
        self.recv_log.display()
        logging.info("List updated")


    def while_waiting(self):
        for sock in conn_q:
            try:
                msg = conn_q[sock].get_nowait()
            except queue.Empty:
                continue
            
            self.update_log(msg.decode('utf-8'))


    # called when exit button is pressed
    def afterEditing(self):
        logging.info("After Editing")
        global quit
        quit = True
        self.parentApp.setNextForm(None)



if __name__ == "__main__":
    TA = ServerApp()
    TA.run()
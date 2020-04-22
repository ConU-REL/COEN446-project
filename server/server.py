# Imports
import npyscreen
import logging
import threading
import queue
from Message import Frame

from tcp_server import server_thread
from MQTT import MQTT


conn_q = queue.Queue()
send_q = queue.Queue()


mqtt_inst = MQTT(send_q)


class ServerApp(npyscreen.NPSAppManaged):
    tcp_thread = threading.Thread(
        target=server_thread, daemon=True, args=(conn_q, send_q,)
    )

    def onStart(self):
        self.tcp_thread.start()
        self.addForm("MAIN", MainForm)


class MainForm(npyscreen.Form):
    OK_BUTTON_TEXT = "Exit"

    def create(self):
        self.keypress_timeout = 1
        self.add(
            npyscreen.TitleText,
            name="MQTT Broker Console",
            editable=False,
            rely = 0
        )
        
        self.recv_log = self.add(
            npyscreen.BoxTitle,
            name="Received Message Log",
            editable=False,
            relx = 2,
            rely = 1,
            max_height = 10
        )
        
        self.topics_log = self.add(
            npyscreen.BoxTitle,
            name="Topics",
            editable=False,
            relx = 2,
            rely = 11,
            max_height = 10,
            max_width = int(self.recv_log.width/3)
        )

        self.pub_log = self.add(
            npyscreen.BoxTitle,
            name="Publishers",
            editable=False,
            relx = self.topics_log.max_width+2,
            rely = 11,
            max_height = 10,
            max_width = int(self.recv_log.width/3)
        )

        self.sub_log = self.add(
            npyscreen.BoxTitle,
            name="Subscribers",
            editable=False,
            relx = 2*self.topics_log.max_width+2,
            rely = 11,
            max_height = 10,
            max_width = int(self.recv_log.width/3)
        )

        self.display()

        # btn_ = npyscreen.ButtonPress
        # btn_send.whenPressed = self.send_msg
        # self.add(btn_send, name="Send Message")

    def update_log(self, msg=None):
        # max number of recent messages we want to see
        self.max_size = 10
        # if we're at max capacity, delete the oldest message from the log
        if len(self.recv_log.values) >= self.max_size:
            self.recv_log.values.pop()
        self.recv_log.values = [msg.__str__()] + self.recv_log.values
        # refresh the display

        self.topics_log.values = mqtt_inst.topics
        self.sub_log.values = mqtt_inst.sub_list
        self.pub_log.values = mqtt_inst.pub_list

        logging.info(mqtt_inst.sub_list)

        self.display()

    def while_waiting(self):
        try:
            (sock, msg) = conn_q.get_nowait()
            frame = mqtt_inst.process_msg(msg.decode("utf-8"))

            if not frame:
                self.update_log(Frame("bad"))
                return

            tp = frame.header.lower()
            logging.info(tp)
            if tp == "connect":
                mqtt_inst.process_connect(sock)
            elif tp == "pub":
                mqtt_inst.process_data(sock, frame)
            elif tp == "sub":
                mqtt_inst.process_sub(sock, frame)
            elif tp == "unsub":
                mqtt_inst.process_unsub(sock, frame)
            elif tp == "disconnect":
                mqtt_inst.process_disc(sock)

            self.update_log(frame)
        except queue.Empty:
            pass

    # called when exit button is pressed
    def afterEditing(self):
        global quit
        quit = True
        self.parentApp.setNextForm(None)


if __name__ == "__main__":
    TA = ServerApp()
    TA.run()

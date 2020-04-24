# Imports
import queue
import npyscreen
import logging
from MQTT_Client import MQTT_Client

out_q = queue.Queue()

mqtt = MQTT_Client()


class ClientApp(npyscreen.NPSAppManaged):
    def onStart(self):
        self.registerForm("MAIN", MainForm())


class MainForm(npyscreen.Form):
    OK_BUTTON_TEXT = "Exit"
    counter = 0

    def __init__(self, *args, **kwargs):
        super(MainForm, self).__init__(*args, **kwargs)
        self.add_handlers({"^C": self.disable_editing})

    def send_msg(self):
        if not self.topic.value in ["", " "]:
            mqtt.publish(self.topic.value, self.data.value)

    def subscribe(self):
        if not self.topic.value in ["", " "]:
            mqtt.subscribe([self.topic.value])

    def unsubscribe(self):
        if not self.topic.value in ["", " "]:
            mqtt.unsubscribe([self.topic.value])

    def connect(self):
        self.conn.value = "Connecting"
        self.conn.display()
        conn = mqtt.connect(out_q)
        if conn == 0:
            self.conn.value = "Connected"
            self.btn_conn.name = "Disconnect"
            self.btn_conn.whenPressed = self.disconnect
        elif conn == 1:
            self.conn.value = "Timed Out"

        self.conn.display()
        self.update_log()

    def disconnect(self):
        conn = mqtt.disconnect()
        if not conn:
            self.conn.value = "Disconnected"
            self.btn_conn.name = "Connect"
            self.btn_conn.whenPressed = self.connect
        else:
            # potential error case here?
            pass

        self.update_log()
        self.display()

    def while_waiting(self):
        self.update_log()
        if not mqtt.connected:
            self.disconnect()
            self.display()

    def update_log(self):
        # max number of recent messages we want to see
        self.max_size = 10
        # if we're at max capacity, delete the oldest message from the log
        if len(self.recv_log.values) >= self.max_size:
            self.recv_log.values.pop()

        self.sub_log.values = mqtt.topics
        try:
            self.recv_log.values.append(" ".join(out_q.get_nowait()))
            logging.info(self.recv_log.values)
        except queue.Empty:
            pass
        # refresh the display
        self.display()

    def create(self):
        self.keypress_timeout = 1

        self.conn = self.add(
            npyscreen.TitleText, name="Connection", editable=False, relx=2, rely=1
        )
        self.conn.value = "Disconnected"

        self.topic = self.add(npyscreen.TitleText, name="Topic")

        self.data = self.add(npyscreen.TitleText, name="Data")
        self.nextrely += 1

        self.recv_log = self.add(
            npyscreen.BoxTitle,
            name="Received Message Log",
            editable=False,
            relx=2,
            rely=4,
            max_height=10,
        )

        self.sub_log = self.add(
            npyscreen.BoxTitle,
            name="Subscriptions",
            editable=False,
            relx=2,
            rely=14,
            max_height=8,
            max_width=int(self.recv_log.width / 3),
        )

        self.btn_conn = self.add(
            npyscreen.ButtonPress,
            name="Connect",
            relx=self.sub_log.relx + self.sub_log.max_width,
            rely=14,
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
        self.btn_unsub.whenPressed = self.unsubscribe

    def disable_editing(self, *args, **keywords):
        self.editing = False

    def afterEditing(self):
        mqtt.disconnect()
        self.parentApp.setNextForm(None)


if __name__ == "__main__":
    TA = ClientApp()
    TA.run()
    # main()

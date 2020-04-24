import npyscreen, queue

from MQTT_Client import MQTT_Client

# for debugging
import logging


# create the queue for received messages:
msgs = queue.Queue()

# create the MQTT client instance with the default
# parameters since we're connecting to a server on the localhost
# and default port

mqtt = MQTT_Client()

# create the UI instance
class ClientApp(npyscreen.NPSAppManaged):
    def onStart(self):
        self.registerForm("MAIN", ManagementForm())


class ManagementForm(npyscreen.Form):
    OK_BUTTON_TEXT = "Exit"

    def __init__(self, *args, **kwargs):
        super(ManagementForm, self).__init__(*args, **kwargs)
        # add a keyboard shortcut to exit
        self.add_handlers({"^C": self.disable_editing})


    def while_waiting(self):
        """While the user isn't actively moving around the form, update stuff"""
        self.update_log()
        if not mqtt.connected:
            self.disconnect()

    def update_log(self):
        """Update UI elements with new info"""
        # max number of recent messages we want to see
        self.max_size = 10

    def send_msg(self):
        """Send the message to the broker"""
        if not self.topic.value in ["", " "]:
            mqtt.publish(self.topic.value, self.data.value)

    def disable_editing(self, *args, **keywords):
        """Helper to disable editing (quit)"""
        self.editing = False

    def connect(self):
        """Connect to the MQTT broker"""
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
        """Disconnect from the MQTT broker"""
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


    def afterEditing(self):
        """Called when exiting"""
        mqtt.disconnect()
        self.parentApp.setNextForm(None)

    def create(self):
        """Create the UI elements"""
        self.keypress_timeout = 1

if __name__ == "__main__":
    TA = ClientApp()
    TA.run()
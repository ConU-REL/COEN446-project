import npyscreen, queue
import json
from MQTT_Client import MQTT_Client

# for debugging
import logging


# create the queue for received messages:
msgs = queue.Queue()

# create the MQTT client instance with the default
# parameters since we're connecting to a server on the localhost
# and default port

mqtt = MQTT_Client()
topic = "user_db"

# set the logging level
logging.basicConfig(level=logging.DEBUG)


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
        if not mqtt.connected:
            self.disconnect()


    def submit(self):
        """Send the message to the broker"""
        if mqtt.connected:
            if not (self.user.value in ["", " "]):
                try:
                    temp = int(self.temp.value)
                    msg = {"name": self.user.value, "temp": temp}
                    mqtt.publish(topic, json.dumps(msg))
                except ValueError:
                    npyscreen.notify_confirm(
                        "Temperature must be a number", title="Bad Input"
                    )
            else:
                npyscreen.notify_confirm("Input is not acceptable", title="Bad Input")
        else:
            npyscreen.notify_confirm(
                "Please connect to broker before submitting",
                title="Can't Submit, Not Connected",
            )

    def disable_editing(self, *args, **keywords):
        """Helper to disable editing (quit)"""
        self.editing = False

    def connect(self):
        """Connect to the MQTT broker"""
        self.status.value = "Connecting"
        self.status.display()
        conn = mqtt.connect(msgs)
        if conn == 0:
            self.status.value = "Connection Successful"
            self.btn_conn.name = "Disconnect"
            self.btn_conn.whenPressed = self.disconnect
            self.status.display()
            return 0
        elif conn == 1:
            self.status.value = "Connection Failed. Check Broker Status"
            self.status.display()
            return 1

    def disconnect(self):
        """Disconnect from the MQTT broker"""
        conn = mqtt.disconnect()
        if not conn:
            self.btn_conn.name = "Connect"
            self.btn_conn.whenPressed = self.connect
            self.status.value = "Disconnected"
            self.status.display()

    def afterEditing(self):
        """Called when exiting"""
        mqtt.disconnect()
        self.parentApp.setNextForm(None)

    def create(self):
        """Create the UI elements"""
        self.keypress_timeout = 1

        self.add(
            npyscreen.TitleText,
            name="Temperature Management Console",
            editable=False,
            rely=0,
        )

        self.label_btn_conn = self.add(
            npyscreen.TitleText,
            name="Connect to broker:",
            editable=False,
            relx=3,
            rely=2,
        )

        # add connect button
        self.btn_conn = self.add(
            npyscreen.ButtonPress,
            name="Connect",
            relx=22,
            rely=self.label_btn_conn.rely,
        )

        # add text asking for name
        self.title_user = self.add(
            npyscreen.TitleText, name="Name:", relx=3, rely=4, editable=False
        )

        # add name entry field
        self.user = self.add(
            npyscreen.Textfield, name="Name", relx=23, rely=self.title_user.rely,
        )

        # add text asking for preferred temp
        self.title_temp = self.add(
            npyscreen.TitleText,
            name="Preferred Temp:",
            relx=3,
            rely=self.title_user.rely + 1,
            editable=False,
        )

        # add temp entry field
        self.temp = self.add(
            npyscreen.Textfield, relx=self.user.relx, rely=self.title_user.rely + 1,
        )

        self.btn_send = self.add(
            npyscreen.ButtonPress, name="Submit", relx=30, rely=self.temp.rely + 2,
        )

        self.nextrely += 1
        self.add(
            npyscreen.TitleText,
            name="If you prefer, you can also load a test file and send it "\
                "using the button below.",
            editable=False,
        )

        self.btn_load = self.add(npyscreen.ButtonPress, name="Load Test")

        self.nextrely += 5
        self.status = self.add(npyscreen.TitleText, name="Status: ", editable=False)

        self.btn_conn.whenPressed = self.connect
        self.btn_send.whenPressed = self.submit

        self.display()


if __name__ == "__main__":
    TA = ClientApp()
    TA.run()

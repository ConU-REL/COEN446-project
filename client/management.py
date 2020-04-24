import npyscreen, queue
import json, time
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
logging.basicConfig(level=logging.INFO)


# create the UI instance
class ClientApp(npyscreen.NPSAppManaged):
    def onStart(self):
        self.registerForm("MAIN", ManagementForm())


class ManagementForm(npyscreen.Form):
    OK_BUTTON_TEXT = "Exit (Ctrl + C)"

    def __init__(self, *args, **kwargs):
        super(ManagementForm, self).__init__(*args, **kwargs)
        # add a keyboard shortcut to exit
        self.add_handlers({"^C": self.disable_editing})

    def while_waiting(self):
        """While the user isn't actively moving around the form, update stuff"""
        if not mqtt.connected:
            self.disconnect()

    def submit(self, p_name=None, p_temp=None):
        """Send the message to the broker"""
        if mqtt.connected:
            # use params or use UI entries?
            name = None
            temp = None
            if not p_name is None and not p_temp is None:
                name = p_name
                temp = p_temp
            elif p_name is None and p_temp is None:
                name = self.user.value
                temp = self.temp.value

            # check input isn't blank
            if not (name in ["", " "]):
                try:
                    # check temp is int
                    temp = int(temp)
                    msg = {"name": name, "temp": temp}
                    # publish
                    mqtt.publish(topic, json.dumps(msg))
                except ValueError:
                    # if temp isn't int
                    npyscreen.notify_confirm(
                        "Temperature must be a number", title="Bad Input"
                    )
            else:
                # bad input
                npyscreen.notify_confirm("Input is not acceptable", title="Bad Input")
        else:
            # not connected to MQTT
            npyscreen.notify_confirm(
                "Please connect to broker before submitting",
                title="Can't Submit, Not Connected",
            )

    def load(self):
        """Load a JSON file for testing"""
        # choose the file
        file = npyscreen.selectFile(must_exist=True, confirm_if_exists=False)

        # open the file
        with open(file, "r") as file:
            try:
                # try to pull data from file
                self.test = json.load(file)["test"]
                # make the "start test" button visible
                self.btn_start.hidden = False
                # update UI
                self.display()

            except (json.JSONDecodeError, KeyError):
                # if bad file
                npyscreen.notify_confirm(
                    "Error in JSON file, please fix and retry.", title="JSON Error"
                )
                return

    def start_test(self):
        """Start a test"""
        # check connected
        if mqtt.connected:
            # send all commands with short delay
            for cmd in self.test:
                self.submit(cmd[0].lower(), cmd[1])
                time.sleep(0.15)
        else:
            # if not connected
            npyscreen.notify_confirm(
                "Please connect to broker before starting test",
                title="Can't Start Test, Not Connected",
            )
            return

    def disable_editing(self, *args, **keywords):
        """Helper to disable editing (quit)"""
        self.editing = False

    def connect(self):
        """Connect to the MQTT broker"""
        self.status.value = "Connecting"
        self.display()
        # try to connect
        conn = mqtt.connect(msgs)
        if conn == 0:
            # if succesful
            # update UI
            self.status.value = "Connection Successful"
            self.btn_conn.name = "Disconnect"
            self.btn_conn.whenPressed = self.disconnect
            self.display()
            return 0
        elif conn == 1:
            # if failed
            # update UI
            self.status.value = "Connection Failed. Check Broker Status"
            self.display()
            return 1

    def disconnect(self):
        """Disconnect from the MQTT broker"""
        # disconnect
        conn = mqtt.disconnect()
        if not conn:
            # update UI
            self.btn_conn.name = "Connect"
            self.btn_conn.whenPressed = self.connect
            self.status.value = "Disconnected"
            self.display()

    def afterEditing(self):
        """Called when exiting"""
        # disconnect before exiting
        mqtt.disconnect()
        self.parentApp.setNextForm(None)

    def create(self):
        """Create the UI elements"""
        self.keypress_timeout = 1

        # add title
        self.add(
            npyscreen.TitleText,
            name="Temperature Management Console",
            editable=False,
            rely=0,
        )

        # add button label
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

        # add send button
        self.btn_send = self.add(
            npyscreen.ButtonPress, name="Submit", relx=30, rely=self.temp.rely + 2,
        )

        self.nextrely += 1
        # add info text
        self.add(
            npyscreen.TitleText,
            name="If you prefer, you can also load a test file and send it "
            "using the button below.",
            editable=False,
        )

        # add load btn
        self.btn_load = self.add(npyscreen.ButtonPress, name="Load Test")
        self.nextrely -= 1
        self.nextrelx += 15
        # add start btn
        self.btn_start = self.add(npyscreen.ButtonPress, name="Start Test", hidden=True)

        # add status field
        self.status = self.add(
            npyscreen.TitleText, name="Status:", value="Idle", editable=False, rely=-3
        )

        # assign button actions
        self.btn_conn.whenPressed = self.connect
        self.btn_send.whenPressed = self.submit

        self.btn_load.whenPressed = self.load
        self.btn_start.whenPressed = self.start_test

        # update UI
        self.display()


if __name__ == "__main__":
    TA = ClientApp()
    TA.run()

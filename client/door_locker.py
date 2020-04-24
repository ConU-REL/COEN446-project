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
topic = "event_db"

# set the logging level
logging.basicConfig(level=logging.DEBUG)

presence = []

# create the UI instance
class ClientApp(npyscreen.NPSAppManaged):
    def onStart(self):
        self.registerForm("MAIN", DoorLockerForm())


class DoorLockerForm(npyscreen.Form):
    OK_BUTTON_TEXT = "Exit (Ctrl + C)"

    def __init__(self, *args, **kwargs):
        super(DoorLockerForm, self).__init__(*args, **kwargs)
        # add a keyboard shortcut to exit
        self.add_handlers({"^C": self.disable_editing})

    def while_waiting(self):
        """While the user isn't actively moving around the form, update stuff"""
        if not mqtt.connected:
            self.disconnect()

    def arrives(self):
        self.submit(0)

    def leaves(self):
        self.submit(1)

    def submit(self, instr, name=None):
        """Send the message to the broker"""
        if mqtt.connected:
            if not name is None:
                user = name
            else:
                user = self.user.value
            msg = {}
            if not (user in ["", " "]):
                msg["name"] = user
                if not instr:
                    msg["instr"] = "arrives"
                else:
                    msg["instr"] = "leaves"
                mqtt.publish(topic, json.dumps(msg))
            else:
                npyscreen.notify_confirm("Input is not acceptable", title="Bad Input")
        else:
            npyscreen.notify_confirm(
                "Please connect to broker before submitting",
                title="Can't Submit, Not Connected",
            )

    def load(self):
        file = npyscreen.selectFile(must_exist=True, confirm_if_exists=False)

        with open(file, "r") as file:
            try:
                self.test = json.load(file)["test"]
                self.btn_start.hidden = False
                self.display()

            except (json.JSONDecodeError, KeyError):
                npyscreen.notify_confirm(
                    "Error in JSON file, please fix and retry.", title="JSON Error"
                )
                return

    def start_test(self):
        if mqtt.connected:
            for cmd in self.test:
                if cmd[0] == "delay":
                    try:
                        delay = int(cmd[1])
                    except ValueError:
                        npyscreen.notify_confirm(
                            "Error in JSON file, please fix and retry.",
                            title="JSON Error",
                        )
                        return
                    if delay <= 10 and delay >= 1:
                        time.sleep(delay)
                else:
                    instr = None
                    if cmd[0].lower() == "arrives":
                        instr = False
                    elif cmd[0].lower() == "leaves":
                        instr = True

                    self.submit(instr, cmd[1])
        else:
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
        conn = mqtt.connect(msgs)
        if conn == 0:
            self.status.value = "Connection Successful"
            self.btn_conn.name = "Disconnect"
            self.btn_conn.whenPressed = self.disconnect
            self.display()
            return 0
        elif conn == 1:
            self.status.value = "Connection Failed. Check Broker Status"
            self.display()
            return 1

    def disconnect(self):
        """Disconnect from the MQTT broker"""
        conn = mqtt.disconnect()
        if not conn:
            self.btn_conn.name = "Connect"
            self.btn_conn.whenPressed = self.connect
            self.status.value = "Disconnected"
            self.display()

    def afterEditing(self):
        """Called when exiting"""
        mqtt.disconnect()
        self.parentApp.setNextForm(None)

    def create(self):
        """Create the UI elements"""
        self.keypress_timeout = 1

        self.add(
            npyscreen.TitleText,
            name="Smart Door Locker Console",
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

        self.btn_arrive = self.add(
            npyscreen.ButtonPress, name="Arrives", relx=15, rely=self.user.rely + 2,
        )

        self.btn_leave = self.add(
            npyscreen.ButtonPress, name="Leaves", relx=25, rely=self.btn_arrive.rely,
        )

        self.nextrely += 1
        self.add(
            npyscreen.TitleText,
            name="If you prefer, you can also load a test file and send it "
            "using the button below.",
            editable=False,
        )

        self.btn_load = self.add(npyscreen.ButtonPress, name="Load Test")
        self.nextrely -= 1
        self.nextrelx += 15
        self.btn_start = self.add(npyscreen.ButtonPress, name="Start Test", hidden=True)

        self.status = self.add(
            npyscreen.TitleText, name="Status:", value="Idle", editable=False, rely=-3
        )
        self.btn_conn.whenPressed = self.connect
        self.btn_arrive.whenPressed = self.arrives
        self.btn_leave.whenPressed = self.leaves

        self.btn_load.whenPressed = self.load
        self.btn_start.whenPressed = self.start_test

        self.display()


if __name__ == "__main__":
    TA = ClientApp()
    TA.run()
